"""网络搜索工具。"""

import os
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from jarvis.jarvis_utils.output import PrettyOutput

# -*- coding: utf-8 -*-

import json
import shutil
import subprocess
import sys

# pylint: disable=import-error,missing-module-docstring

from jarvis.jarvis_agent import Agent

# fmt: on

# ddgr 快速探针超时（秒），用于在正式搜索前判断是否可用
DDGR_PROBE_TIMEOUT = 4
# ddgr 正式搜索超时（秒），与原先保持一致
DDGR_SEARCH_TIMEOUT = 30
# 备用 Wikipedia 探针超时（秒）
FALLBACK_PROBE_TIMEOUT = 3


class SearchWebTool:
    """处理网络搜索的类。"""

    name = "search_web"
    description = "搜索互联网上的信息"
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "搜索关键词或问题",
            },
            "site": {
                "type": "string",
                "description": "在特定网站内搜索，如 'wikipedia.org', 'github.com'",
            },
        },
        "required": ["query"],
    }

    def _get_ddgr_command(self) -> list[str]:
        """获取 ddgr 命令，支持多种调用方式

        返回:
            list[str]: ddgr 命令列表
        """
        # 方法1: 尝试直接使用 ddgr 命令（如果它在 PATH 中）
        ddgr_path = shutil.which("ddgr")
        if ddgr_path:
            return [ddgr_path]

        # 方法2: 尝试使用 python -m ddgr（适用于 uv tool install 等安装方式）
        try:
            # 检查 ddgr 模块是否可用
            import importlib.util

            spec = importlib.util.find_spec("ddgr")
            if spec is not None:
                return [sys.executable, "-m", "ddgr"]
        except Exception:
            pass

        # 方法3: 回退到直接使用 ddgr（让 subprocess 处理错误）
        return ["ddgr"]

    def _probe_ddgr_quick(self) -> bool:
        """快速检测 ddgr 是否可用（短超时探针），避免长时间等待后才发现失败。

        返回:
            bool: True 表示 ddgr 可执行且能正常返回，False 表示不可用或超时。
        """
        try:
            ddgr_cmd = self._get_ddgr_command()
            # 使用最小查询触发一次 JSON 输出，超时时间短
            probe_cmd = ddgr_cmd + ["--json", "--np", "-x", "--num", "1", "test"]
            r = subprocess.run(
                probe_cmd,
                capture_output=True,
                text=True,
                timeout=DDGR_PROBE_TIMEOUT,
                check=False,
            )
            if r.returncode != 0:
                return False
            try:
                json.loads(r.stdout)
                return True
            except (json.JSONDecodeError, TypeError):
                return False
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            return False

    def _probe_wikipedia_available(self) -> bool:
        """快速检测备用 Wikipedia 搜索是否可用（curl + 网络可达）。"""
        if not shutil.which("curl"):
            return False
        try:
            r = subprocess.run(
                [
                    "curl",
                    "-s",
                    "--max-time",
                    str(FALLBACK_PROBE_TIMEOUT),
                    "-o",
                    os.devnull,
                    "-w",
                    "%{http_code}",
                    "https://zh.wikipedia.org/w/api.php?action=query&list=search&srsearch=test&format=json&srlimit=1",
                ],
                capture_output=True,
                text=True,
                timeout=FALLBACK_PROBE_TIMEOUT + 2,
                check=False,
            )
            return r.returncode == 0 and r.stdout.strip() == "200"
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            return False

    def _get_available_backends(self) -> List[Tuple[str, str]]:
        """探测当前可用的搜索后端，返回 (后端标识, 显示名称) 列表，顺序为优先使用顺序。"""
        backends: List[Tuple[str, str]] = []
        if self._probe_ddgr_quick():
            backends.append(("ddgr", "ddgr"))
        if self._probe_wikipedia_available():
            backends.append(("wikipedia", "Wikipedia"))
        return backends

    def _search_with_ddgr(
        self,
        query: str,
        agent: Agent,
        site: Optional[str] = None,
    ) -> Dict[str, Any]:
        # pylint: disable=too-many-locals, broad-except
        """使用ddgr命令执行网络搜索、抓取内容并总结结果。"""
        try:
            # 获取 ddgr 命令
            ddgr_cmd = self._get_ddgr_command()

            # 构建ddgr命令
            cmd = ddgr_cmd + [
                "--json",
                "--np",
                "-x",
            ]  # --np 表示不提示，直接执行；-x 显示完整URL

            # 添加网站特定搜索参数
            if site:
                cmd.extend(["-w", site])

            # 添加搜索关键词
            cmd.append(query)

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=DDGR_SEARCH_TIMEOUT,
                check=False,
            )

            if result.returncode != 0:
                return {
                    "stdout": "",
                    "stderr": f"ddgr命令执行失败: {result.stderr}",
                    "success": False,
                }

            try:
                results = json.loads(result.stdout)
            except json.JSONDecodeError as e:
                return {
                    "stdout": "",
                    "stderr": f"解析ddgr JSON输出失败: {e}",
                    "success": False,
                }

            if not results:
                return {
                    "stdout": "未找到搜索结果。",
                    "stderr": "未找到搜索结果。",
                    "success": False,
                }

            # 先打印搜索结果
            PrettyOutput.auto_print("\n🔍 网络搜索结果")
            PrettyOutput.auto_print(f"📝 查询关键词: {query}")
            PrettyOutput.auto_print(f"📊 搜索结果数: {len(results)}")
            PrettyOutput.auto_print("\n📄 搜索摘要:")

            # 收集搜索结果并格式化输出
            results_text = ""
            visited_urls = []

            for idx, r in enumerate(results[:10], 1):
                title = r.get("title", "")
                url = r.get("url", "")
                abstract = r.get("abstract", "")

                if title:
                    PrettyOutput.auto_print(f"  {idx}. {title}")
                    if url:
                        PrettyOutput.auto_print(f"     URL: {url}")
                        visited_urls.append(url)
                    if abstract:
                        PrettyOutput.auto_print(
                            f"     摘要: {abstract[:150]}..."
                            if len(abstract) > 150
                            else f"     摘要: {abstract}"
                        )

                    # 添加到返回文本
                    results_text += f"{idx}. {title}\n"
                    if url:
                        results_text += f"   URL: {url}\n"
                    if abstract:
                        results_text += f"   摘要: {abstract}\n"
                    results_text += "\n"

            # 添加提示信息
            results_text += "💡 提示：如果想要获取详细信息，可以调用read_webpage工具\n"

            return {
                "stdout": results_text,
                "stderr": "",
                "success": True,
            }

        except subprocess.TimeoutExpired:
            return {
                "stdout": "",
                "stderr": "ddgr命令执行超时。",
                "success": False,
            }
        except Exception as e:
            PrettyOutput.auto_print(f"❌ 网页搜索过程中发生错误: {e}")
            return {
                "stdout": "",
                "stderr": f"网页搜索过程中发生错误: {e}",
                "success": False,
            }

    def _search_with_alternative_apis(
        self,
        query: str,
        agent: Agent,
        site: Optional[str] = None,
    ) -> Dict[str, Any]:
        # pylint: disable=too-many-locals, broad-except
        """使用备用API执行网络搜索（当ddgr不可用时）。

        当前支持：
        1. Wikipedia API - 用于查询百科信息
        2. 可以通过execute_script调用其他API
        """
        try:
            # 尝试使用 Wikipedia API
            # URL encode the query
            import urllib.parse
            encoded_query = urllib.parse.quote(query)
            
            wiki_url = f"https://zh.wikipedia.org/w/api.php?action=query&list=search&srsearch={encoded_query}&format=json&utf8=&srlimit=5"
            
            script = f"""curl -s '{wiki_url}' | python3 -c "
import json
import sys
import urllib.parse

try:
    data = json.load(sys.stdin)
    if 'query' in data and 'search' in data['query']:
        results = data['query']['search']
        if results:
            print('📝 查询关键词: {query}')
            print('📊 搜索结果数:', len(results))
            print('📄 搜索摘要:')
            print()
            for idx, item in enumerate(results[:5], 1):
                title = item.get('title', '')
                snippet = item.get('snippet', '')
                url = 'https://zh.wikipedia.org/wiki/' + urllib.parse.quote(title.replace(' ', '_')) if title else ''
                
                print('  ' + str(idx) + '. ' + title)
                if snippet:
                    if len(snippet) > 200:
                        print('     摘要: ' + snippet[:200] + '...')
                    else:
                        print('     摘要: ' + snippet)
                print('     URL: ' + url)
                print()
        else:
            print('未找到相关结果')
    else:
        print('API返回数据格式错误')
except Exception as e:
    print('搜索失败: ' + str(e))
" 2>&1"""

            result = subprocess.run(
                script,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
                cwd=os.getcwd()
            )

            if result.returncode == 0 and result.stdout:
                return {
                    "stdout": result.stdout,
                    "stderr": "",
                    "success": True,
                }
            else:
                return {
                    "stdout": "",
                    "stderr": f"备用搜索失败: {result.stderr}",
                    "success": False,
                }

        except subprocess.TimeoutExpired:
            return {
                "stdout": "",
                "stderr": "备用搜索超时。",
                "success": False,
            }
        except Exception as e:
            PrettyOutput.auto_print(f"❌ 备用搜索过程中发生错误: {e}")
            return {
                "stdout": "",
                "stderr": f"备用搜索过程中发生错误: {e}",
                "success": False,
            }

    def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes the web search.

        Uses ddgr command to search the web and scrape pages for content.
        Supports site-specific search.
        先快速探测 ddgr 与备用后端可用性，失败时快速切换并反馈当前执行方式。
        """
        query = args.get("query")
        agent = args.get("agent")

        if not query:
            return {"stdout": "", "stderr": "缺少查询参数。", "success": False}

        if not isinstance(agent, Agent) or not agent.model:
            return {
                "stdout": "",
                "stderr": "Agent或Agent模型未找到。",
                "success": False,
            }

        site = args.get("site")

        # 快速探测可用后端（ddgr + 备用），便于快速失败与切换反馈
        available = self._get_available_backends()
        backend_names = [b[1] for b in available]

        if not available:
            PrettyOutput.auto_print(
                "❌ 无可用搜索后端：ddgr 不可用且备用 Wikipedia 不可用（请检查 ddgr 安装或网络）。"
            )
            return {
                "stdout": "",
                "stderr": "无可用搜索后端（ddgr 与 Wikipedia 均不可用）。",
                "success": False,
            }

        # 优先使用 ddgr（若探针通过）
        use_ddgr = any(b[0] == "ddgr" for b in available)

        if use_ddgr:
            result = self._search_with_ddgr(query=query, agent=agent, site=site)
            if result.get("success", False):
                return result
            # ddgr 执行失败，快速切换备用并反馈
            PrettyOutput.auto_print(
                "⚠️ ddgr 搜索失败（超时或执行错误），正在切换备用搜索…"
            )
        else:
            # 探针阶段已发现 ddgr 不可用，直接使用备用
            PrettyOutput.auto_print(
                "⚠️ ddgr 不可用或未安装，使用备用搜索（当前可用: "
                + ", ".join(backend_names)
                + "）。"
            )
            result = {"success": False, "stderr": "ddgr 不可用（探针未通过）。"}

        if site:
            PrettyOutput.auto_print(
                f"⚠️ 备用方案不支持网站内搜索，建议使用其他方式访问 {site}"
            )
            return result

        # 尝试备用：仅使用已探测可用的后端
        if any(b[0] == "wikipedia" for b in available):
            PrettyOutput.auto_print("🔀 已切换至 Wikipedia 搜索。")
            backup_result = self._search_with_alternative_apis(
                query=query, agent=agent, site=site
            )
            if backup_result.get("success", False):
                return backup_result
            PrettyOutput.auto_print(
                f"❌ 备用搜索失败: {backup_result.get('stderr', 'unknown')}"
            )
            return {
                "stdout": "",
                "stderr": f"ddgr搜索失败: {result.get('stderr', '')}\n备用搜索失败: {backup_result.get('stderr', '')}",
                "success": False,
            }

        return {
            "stdout": "",
            "stderr": result.get("stderr", "ddgr 搜索失败，且无其他可用后端。"),
            "success": False,
        }

    @staticmethod
    def check() -> bool:
        """Check if the tool is available."""
        return True
