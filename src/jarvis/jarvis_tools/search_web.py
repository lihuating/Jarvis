"""网络搜索工具。"""

import os
from typing import Any
from typing import Dict
from typing import Optional
from jarvis.jarvis_utils.output import PrettyOutput

# -*- coding: utf-8 -*-

import json
import shutil
import subprocess
import sys

# pylint: disable=import-error,missing-module-docstring

from jarvis.jarvis_agent import Agent

# fmt: on


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
                cmd, capture_output=True, text=True, timeout=30, check=False
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
                url = f\"https://zh.wikipedia.org/wiki/{urllib.parse.quote(title.replace(' ', '_'))}\" if title else ''
                
                print(f'  {{idx}}. {{title}}')
                if snippet:
                    print(f'     摘要: {{snippet[:200]}}...' if len(snippet) > 200 else f'     摘要: {{snippet}}')
                print(f'     URL: {{url}}')
                print()
        else:
            print('未找到相关结果')
    else:
        print('API返回数据格式错误')
except Exception as e:
    print(f'搜索失败: {{str(e)}}')
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
        
        If ddgr is not available, falls back to alternative APIs like Wikipedia.
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

        # 提取可选参数
        site = args.get("site")

        # 先尝试使用 ddgr
        result = self._search_with_ddgr(query=query, agent=agent, site=site)
        
        # 如果 ddgr 失败，尝试使用备用方案
        if not result.get("success", False):
            PrettyOutput.auto_print("⚠️ ddgr 搜索失败，尝试使用备用搜索方案...")
            
            # 如果指定了网站搜索，备用方案可能不支持，返回原错误
            if site:
                PrettyOutput.auto_print(f"⚠️ 备用方案不支持网站内搜索，建议使用其他方式访问 {site}")
                return result
            
            # 尝试备用搜索
            backup_result = self._search_with_alternative_apis(
                query=query, agent=agent, site=site
            )
            
            # 如果备用方案成功，返回备用结果；否则返回原错误
            if backup_result.get("success", False):
                return backup_result
            else:
                PrettyOutput.auto_print(f"❌ 备用搜索也失败了: {backup_result.get('stderr', 'unknown')}")
                # 返回组合的错误信息
                return {
                    "stdout": "",
                    "stderr": f"ddgr搜索失败: {result.get('stderr', '')}\n备用搜索失败: {backup_result.get('stderr', '')}",
                    "success": False,
                }

        return result

    @staticmethod
    def check() -> bool:
        """Check if the tool is available."""
        return True
