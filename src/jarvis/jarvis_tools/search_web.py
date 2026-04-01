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
from pathlib import Path

# pylint: disable=import-error,missing-module-docstring

from jarvis.jarvis_agent import Agent
from jarvis.jarvis_mcp.streamable_mcp_client import StreamableMcpClient

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

    def _get_search_backend_preference(self) -> str:
        """返回搜索后端偏好：auto|mcp|ddgr|wikipedia。"""
        v = os.environ.get("JARVIS_SEARCH_WEB_BACKEND", "auto").strip().lower()
        if v in {"auto", "mcp", "ddgr", "wikipedia"}:
            return v
        return "auto"

    def _get_zhipu_web_search_mcp_base_url(self) -> str:
        # 智谱官方 web_search_prime MCP（用户可通过环境变量覆盖）
        env_url = os.environ.get(
            "JARVIS_ZHIPU_WEB_SEARCH_MCP_URL",
            "https://open.bigmodel.cn/api/mcp/web_search_prime/",
        ).strip()
        if env_url:
            return env_url
        # 如果环境变量未设置，尝试从配置文件 MCP 列表中推断
        cfg = self._get_zhipu_mcp_config_from_global_config()
        if cfg and isinstance(cfg.get("base_url"), str):
            return cfg["base_url"].strip()
        return "https://open.bigmodel.cn/api/mcp/web_search_prime/"

    def _get_zhipu_api_key(self) -> str:
        # 兼容不同命名：优先环境变量，其次从 ~/.jarvis/config.yaml 的 mcp 配置读取
        env_key = (
            os.environ.get("JARVIS_ZHIPU_API_KEY", "").strip()
            or os.environ.get("JARVIS_WEB_SEARCH_MCP_TOKEN", "").strip()
        )
        if env_key:
            return env_key
        cfg = self._get_zhipu_mcp_config_from_global_config()
        if cfg and isinstance(cfg.get("auth_token"), str) and cfg.get("auth_token"):
            return str(cfg["auth_token"]).strip()
        return ""

    def _is_mcp_configured(self) -> bool:
        return bool(self._get_zhipu_api_key() and self._get_zhipu_web_search_mcp_base_url())

    def _get_zhipu_mcp_config_from_global_config(self) -> Optional[Dict[str, Any]]:
        """从 Jarvis 全局配置的 mcp 列表中，选取 web_search_prime 对应项。

        允许用户在 ~/.jarvis/config.yaml 中配置 mcp:
          - name: zhipu_web_search_prime
            type: streamable
            base_url: https://open.bigmodel.cn/api/mcp/web_search_prime/
            endpoint_path: mcp
            auth_token: ...
        """
        try:
            # 避免模块导入顺序导致循环依赖，采用函数内导入
            from jarvis.jarvis_utils.config import get_mcp_config  # pylint: disable=import-error

            mcp_list = get_mcp_config()
            if not isinstance(mcp_list, list):
                return None

            candidates: List[Dict[str, Any]] = []
            for item in mcp_list:
                if not isinstance(item, dict):
                    continue
                if not item.get("enable", True):
                    continue
                t = str(item.get("type", "")).strip().lower()
                if t != "streamable":
                    continue
                base_url = str(item.get("base_url", "")).strip()
                if not base_url:
                    continue
                name = str(item.get("name", "")).strip().lower()
                if "web_search_prime" in base_url or "web-search-prime" in base_url:
                    candidates.append(item)
                elif name in {"zhipu_web_search_prime", "web_search_prime", "web-search-prime"}:
                    candidates.append(item)

            return candidates[0] if candidates else None
        except Exception:
            return None

    def _get_zhipu_mcp_tool_name_override(self) -> str:
        return os.environ.get("JARVIS_ZHIPU_WEB_SEARCH_MCP_TOOL_NAME", "").strip()

    def _pick_mcp_search_tool_name(self, tool_names: List[str]) -> Optional[str]:
        """从 MCP 工具列表里挑选“最像 web search”的工具名。"""
        if not tool_names:
            return None

        override = self._get_zhipu_mcp_tool_name_override()
        if override:
            return override

        # 常见候选（按经验排序）
        common = [
            "webSearchPrime",
            "web_search_prime",
            "web_search",
            "webSearch",
            "search",
            "search_web",
        ]
        for name in common:
            if name in tool_names:
                return name

        # 兜底：按关键词匹配
        lowered = [(n, n.lower()) for n in tool_names]
        for n, nl in lowered:
            if "search" in nl and ("web" in nl or "prime" in nl):
                return n
        for n, nl in lowered:
            if "search" in nl:
                return n
        return tool_names[0]

    def _get_ddgr_command(self) -> list[str]:
        """获取 ddgr 命令，支持多种调用方式

        返回:
            list[str]: ddgr 命令列表
        """
        # 方法0: 允许通过环境变量显式指定 ddgr 路径（便于 VSCode 等环境 PATH 不一致场景）
        try:
            env_path = os.environ.get("JARVIS_DDGR_PATH", "").strip()
            if env_path:
                p = Path(env_path).expanduser()
                if p.exists() and p.is_file():
                    return [str(p)]
        except Exception:
            pass

        # 方法1: 尝试直接使用 ddgr 命令（如果它在 PATH 中）
        ddgr_path = shutil.which("ddgr")
        if ddgr_path:
            return [ddgr_path]

        # 方法1.5: 常见用户级安装路径（PATH 不包含 ~/.local/bin 时也能找到）
        try:
            p = Path("~/.local/bin/ddgr").expanduser()
            if p.exists() and p.is_file():
                return [str(p)]
        except Exception:
            pass

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
        pref = self._get_search_backend_preference()
        backends: List[Tuple[str, str]] = []

        # 若强制指定后端，则不做多余探测，按指定返回（但仍会在执行阶段报出详细错误）
        if pref == "mcp":
            if self._is_mcp_configured():
                return [("mcp", "Zhipu MCP(web_search_prime)")]
            return []
        if pref == "ddgr":
            return [("ddgr", "ddgr")] if self._probe_ddgr_quick() else []
        if pref == "wikipedia":
            return [("wikipedia", "Wikipedia")] if self._probe_wikipedia_available() else []

        # auto：优先 MCP（仅基于配置判断，不做网络探针），再 ddgr，再 Wikipedia
        if self._is_mcp_configured():
            backends.append(("mcp", "Zhipu MCP(web_search_prime)"))
        if self._probe_ddgr_quick():
            backends.append(("ddgr", "ddgr"))
        if self._probe_wikipedia_available():
            backends.append(("wikipedia", "Wikipedia"))
        return backends

    def _search_with_mcp(
        self,
        query: str,
        agent: Agent,
        site: Optional[str] = None,
    ) -> Dict[str, Any]:
        # pylint: disable=broad-except
        """使用智谱 web_search_prime MCP 执行搜索。"""
        if not self._is_mcp_configured():
            return {
                "stdout": "",
                "stderr": "MCP 未配置：请设置 JARVIS_ZHIPU_API_KEY 与 JARVIS_ZHIPU_WEB_SEARCH_MCP_URL。",
                "success": False,
            }

        q = query
        if site:
            # MCP 接口未必支持显式 site 参数，统一降级为 query 拼接
            q = f"{query} site:{site}"

        try:
            base_url = self._get_zhipu_web_search_mcp_base_url()
            api_key = self._get_zhipu_api_key()

            client = StreamableMcpClient(
                {
                    "base_url": base_url,
                    "endpoint_path": "mcp",
                    "auth_token": api_key,
                    "timeout": [10, 60],
                }
            )

            tools = client.get_tool_list()
            tool_names = [t.get("name", "") for t in tools if isinstance(t, dict)]
            tool_names = [n for n in tool_names if n]
            tool_name = self._pick_mcp_search_tool_name(tool_names)
            if not tool_name:
                return {
                    "stdout": "",
                    "stderr": "MCP 未返回可用工具列表，无法选择搜索工具。",
                    "success": False,
                }

            # 智谱 MCP 的参数以 query 为主，保留 limit 作为常见可选项
            ret = client.execute(tool_name, {"query": q, "limit": 10})
            if ret.get("success"):
                stdout = (ret.get("stdout") or "").strip()
                if stdout:
                    return {"stdout": stdout, "stderr": "", "success": True}
                return {
                    "stdout": "",
                    "stderr": "MCP 搜索返回为空。",
                    "success": False,
                }

            return {
                "stdout": "",
                "stderr": f"MCP 搜索失败: {ret.get('stderr', 'unknown')}",
                "success": False,
            }
        except Exception as e:
            return {
                "stdout": "",
                "stderr": f"MCP 搜索异常: {e}",
                "success": False,
            }

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
                "❌ 无可用搜索后端：MCP/ddgr/Wikipedia 均不可用（请检查配置、ddgr 安装或网络）。"
            )
            # 诊断提示：ddgr 在 VSCode/Jarvis 运行环境里可能 PATH 不一致
            try:
                ddgr_cmd = self._get_ddgr_command()
                PrettyOutput.auto_print(
                    "ℹ️ 诊断提示：可尝试设置环境变量 JARVIS_DDGR_PATH 指向 ddgr 可执行文件，例如：\n"
                    "   export JARVIS_DDGR_PATH=~/.local/bin/ddgr\n"
                    f"   （当前解析到的 ddgr 命令候选：{ddgr_cmd}）"
                )
            except Exception:
                pass
            # 诊断提示：MCP 配置
            PrettyOutput.auto_print(
                "ℹ️ MCP 诊断提示：如需使用智谱 web_search_prime，请设置：\n"
                "   export JARVIS_SEARCH_WEB_BACKEND=mcp\n"
                "   export JARVIS_ZHIPU_API_KEY=你的APIKey\n"
                "   export JARVIS_ZHIPU_WEB_SEARCH_MCP_URL=https://open.bigmodel.cn/api/mcp/web_search_prime/\n"
            )
            return {
                "stdout": "",
                "stderr": "无可用搜索后端（MCP/ddgr/Wikipedia 均不可用）。",
                "success": False,
            }

        # 优先顺序：按 available 顺序尝试（auto: MCP -> ddgr -> Wikipedia）
        use_mcp = any(b[0] == "mcp" for b in available)
        use_ddgr = any(b[0] == "ddgr" for b in available)

        if use_mcp:
            PrettyOutput.auto_print("🔍 使用智谱 MCP(web_search_prime) 搜索中…")
            result = self._search_with_mcp(query=query, agent=agent, site=site)
            if result.get("success", False):
                return result
            PrettyOutput.auto_print(
                f"⚠️ MCP 搜索失败，正在切换到其他后端…（原因: {result.get('stderr', 'unknown')}）"
            )

        if use_ddgr:
            result = self._search_with_ddgr(query=query, agent=agent, site=site)
            if result.get("success", False):
                return result
            # ddgr 执行失败，快速切换备用并反馈
            PrettyOutput.auto_print(
                "⚠️ ddgr 搜索失败（超时或执行错误），正在切换备用搜索…"
            )
        else:
            # 探针阶段已发现 ddgr 不可用
            other_backends = [n for n in backend_names if not n.startswith("Zhipu MCP")]
            if other_backends:
                PrettyOutput.auto_print(
                    "⚠️ ddgr 不可用或未安装，使用备用搜索（当前可用: "
                    + ", ".join(other_backends)
                    + "）。"
                )
            else:
                PrettyOutput.auto_print("⚠️ ddgr 不可用或未安装，且无其他可用后端。")
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
