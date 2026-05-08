# -*- coding: utf-8 -*-
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from typing import Dict

from jarvis.jarvis_utils.output import PrettyOutput


class VswMemCollectTool:
    """9200 基站 VSW 内存信息收集工具

    自动执行以下操作：
    1. 上传 vsw_mem_full.sh 脚本到基站
    2. 执行脚本收集内存信息
    3. 下载结果文件到本地
    4. 清理基站上的临时文件
    """

    name = "vsw_mem_collect"
    description = """收集 9200 基站 VSW 内存信息。自动完成脚本上传、执行、结果下载和清理操作。

    使用场景：
    • 基站性能问题诊断
    • 内存泄漏分析
    • 资源使用监控
    • 系统健康检查

    操作流程：
    1. 上传 vsw_mem_full.sh 脚本到基站 /home/itran/ 目录
    2. 在基站上执行脚本并收集内存信息
    3. 下载结果文件到本地 ~/memory_data/ 目录
    4. 自动清理基站上的临时文件

    注意事项：
    • 需要安装 sshpass 工具
    • 基站 SSH 登录信息：用户名 itran，密码 Itran_2430!@#
    • 结果文件包含基站 IP 和时间戳，便于区分
    """
    parameters = {
        "type": "object",
        "properties": {
            "base_ip": {
                "type": "string",
                "description": "9200 基站 IP 地址，例如：192.168.1.100",
            },
            "script_path": {
                "type": "string",
                "description": "vsw_mem_full.sh 脚本的本地路径。如果不提供，将自动在 ~/Jarvis/vsw_mem_full.sh 查找。",
            },
            "local_download_dir": {
                "type": "string",
                "description": "本地下载目录。默认为 ~/memory_data/",
            },
            "skip_cleanup": {
                "type": "boolean",
                "description": "是否跳过清理基站临时文件。默认为 false（执行清理）。",
            },
        },
        "required": ["base_ip"],
    }

    # 9200 基站登录信息
    SSH_USER = "itran"
    SSH_PASSWORD = "Itran_2430!@#"

    def _check_sshpass(self) -> bool:
        """检查 sshpass 是否已安装"""
        try:
            subprocess.run(
                ["which", "sshpass"], check=True, capture_output=True
            )
            return True
        except subprocess.CalledProcessError:
            PrettyOutput.auto_print("❌ sshpass 未安装")
            PrettyOutput.auto_print(
                "请先安装: sudo yum install -y sshpass"
            )
            return False

    def _run_command(
        self, cmd: str, check: bool = True
    ) -> subprocess.CompletedProcess:
        """执行 shell 命令"""
        PrettyOutput.auto_print(f"📝 执行命令: {cmd}")
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                check=check,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            if result.stdout:
                PrettyOutput.auto_print(result.stdout)
            if result.stderr:
                PrettyOutput.auto_print(result.stderr)
            return result
        except subprocess.CalledProcessError as e:
            PrettyOutput.auto_print(f"❌ 命令执行失败: {e}")
            if e.stderr:
                PrettyOutput.auto_print(f"错误输出: {e.stderr}")
            raise

    def _create_local_directory(self, local_dir: str) -> str:
        """创建本地下载目录"""
        if not os.path.exists(local_dir):
            os.makedirs(local_dir)
            PrettyOutput.auto_print(f"📁 创建本地目录: {local_dir}")
        return local_dir

    def _upload_script(
        self, base_ip: str, script_path: str
    ) -> None:
        """上传脚本到基站"""
        PrettyOutput.auto_print(f"\n{'='*60}")
        PrettyOutput.auto_print(f"📤 上传脚本到基站 {base_ip}")
        PrettyOutput.auto_print(f"{'='*60}")

        remote_path = f"{self.SSH_USER}@{base_ip}:/home/{self.SSH_USER}/"

        cmd = f"sshpass -p '{self.SSH_PASSWORD}' scp {script_path} {remote_path}"
        self._run_command(cmd)
        PrettyOutput.auto_print("✅ 脚本上传成功")

    def _execute_script_on_base(self, base_ip: str) -> None:
        """在基站上执行脚本"""
        PrettyOutput.auto_print(f"\n{'='*60}")
        PrettyOutput.auto_print(
            f"🚀 在基站 {base_ip} 上执行内存收集脚本"
        )
        PrettyOutput.auto_print(f"{'='*60}")

        cmd = f"sshpass -p '{self.SSH_PASSWORD}' ssh -o StrictHostKeyChecking=no {self.SSH_USER}@{base_ip} 'cd /home/{self.SSH_USER} && ./vsw_mem_full.sh > vsw_oss_cpu_mem.log 2>&1'"

        PrettyOutput.auto_print("⏳ 开始执行脚本，这可能需要几分钟时间...")
        try:
            self._run_command(cmd, check=False)
            PrettyOutput.auto_print("✅ 脚本执行完成")
        except Exception as e:
            PrettyOutput.auto_print(
                f"⚠️  脚本执行可能出错，但继续尝试收集文件: {e}"
            )

    def _download_files(
        self, base_ip: str, local_dir: str
    ) -> Dict[str, str]:
        """从基站下载生成的文件"""
        PrettyOutput.auto_print(f"\n{'='*60}")
        PrettyOutput.auto_print(f"📥 从基站 {base_ip} 下载结果文件")
        PrettyOutput.auto_print(f"{'='*60}")

        # 生成带时间戳的文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        remote_base = f"{self.SSH_USER}@{base_ip}:/home/{self.SSH_USER}/"

        downloaded_files = {}

        # 下载 oss_cpu_log.tar.gz
        remote_tar = f"{remote_base}oss_cpu_log.tar.gz"
        local_tar = os.path.join(
            local_dir, f"oss_cpu_log_{base_ip}_{timestamp}.tar.gz"
        )

        cmd = f"sshpass -p '{self.SSH_PASSWORD}' scp {remote_tar} {local_tar}"
        try:
            self._run_command(cmd)
            PrettyOutput.auto_print(f"✅ 成功下载: {local_tar}")
            downloaded_files["tar"] = local_tar
        except Exception as e:
            PrettyOutput.auto_print(f"⚠️  下载 oss_cpu_log.tar.gz 失败: {e}")

        # 下载 vsw_oss_cpu_mem.log
        remote_log = f"{remote_base}vsw_oss_cpu_mem.log"
        local_log = os.path.join(
            local_dir, f"vsw_oss_cpu_mem_{base_ip}_{timestamp}.log"
        )

        cmd = f"sshpass -p '{self.SSH_PASSWORD}' scp {remote_log} {local_log}"
        try:
            self._run_command(cmd)
            PrettyOutput.auto_print(f"✅ 成功下载: {local_log}")
            downloaded_files["log"] = local_log
        except Exception as e:
            PrettyOutput.auto_print(f"⚠️  下载 vsw_oss_cpu_mem.log 失败: {e}")

        return downloaded_files

    def _cleanup_remote_files(self, base_ip: str) -> None:
        """清理基站上的临时文件"""
        PrettyOutput.auto_print(f"\n{'='*60}")
        PrettyOutput.auto_print(f"🧹 清理基站 {base_ip} 上的临时文件")
        PrettyOutput.auto_print(f"{'='*60}")

        cmd = f"sshpass -p '{self.SSH_PASSWORD}' ssh -o StrictHostKeyChecking=no {self.SSH_USER}@{base_ip} 'rm -f /home/{self.SSH_USER}/vsw_oss_cpu_mem.log /home/{self.SSH_USER}/oss_cpu_log.tar.gz /home/{self.SSH_USER}/vsw_mem_full.sh'"
        try:
            self._run_command(cmd, check=False)
            PrettyOutput.auto_print("✅ 清理完成")
        except Exception as e:
            PrettyOutput.auto_print(f"⚠️  清理失败: {e}")

    def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """执行 VSW 内存收集

        Args:
            args: 包含基站 IP 和可选参数的字典

        Returns:
            包含执行结果的字典
        """
        try:
            base_ip = args.get("base_ip", "").strip()
            if not base_ip:
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": "必须提供基站 IP 地址",
                }

            PrettyOutput.auto_print("="*60)
            PrettyOutput.auto_print("🔍 VSW 内存信息收集工具")
            PrettyOutput.auto_print("="*60)

            # 检查依赖
            if not self._check_sshpass():
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": "sshpass 未安装",
                }

            # 获取脚本路径
            script_path = args.get("script_path")
            if not script_path:
                # 默认脚本路径，优先从工具所在目录查找
                tool_dir = os.path.dirname(os.path.abspath(__file__))
                tool_script = os.path.join(tool_dir, "vsw_mem_full.sh")
                default_script = os.path.expanduser(
                    "~/Jarvis/vsw_mem_full.sh"
                )
                alt_script = os.path.expanduser(
                    "~/Jarvis/skills/vsw_mem_full.sh"
                )
                if os.path.exists(tool_script):
                    script_path = tool_script
                elif os.path.exists(default_script):
                    script_path = default_script
                elif os.path.exists(alt_script):
                    script_path = alt_script
                else:
                    return {
                        "success": False,
                        "stdout": "",
                        "stderr": f"找不到脚本文件，请提供 script_path 参数或确保脚本存在于 {tool_script}、{default_script} 或 {alt_script}",
                    }

            if not os.path.exists(script_path):
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": f"脚本文件不存在: {script_path}",
                }

            PrettyOutput.auto_print(f"📄 使用脚本: {script_path}")

            # 获取本地下载目录
            local_dir = args.get(
                "local_download_dir",
                os.path.expanduser("~/memory_data"),
            )

            # 创建本地目录
            local_dir = self._create_local_directory(local_dir)

            # 上传脚本
            self._upload_script(base_ip, script_path)

            # 执行脚本
            self._execute_script_on_base(base_ip)

            # 下载结果文件
            downloaded_files = self._download_files(base_ip, local_dir)

            # 清理远程文件
            skip_cleanup = args.get("skip_cleanup", False)
            if not skip_cleanup:
                self._cleanup_remote_files(base_ip)

            # 返回结果
            PrettyOutput.auto_print(f"\n{'='*60}")
            PrettyOutput.auto_print("✅ 收集完成!")
            PrettyOutput.auto_print(f"📁 结果文件保存在: {local_dir}")
            PrettyOutput.auto_print(f"{'='*60}")

            return {
                "success": True,
                "stdout": f"成功收集基站 {base_ip} 的 VSW 内存信息，结果文件保存在 {local_dir}",
                "stderr": "",
                "downloaded_files": downloaded_files,
                "local_dir": local_dir,
            }

        except Exception as e:
            PrettyOutput.auto_print(f"\n❌ 发生错误: {e}")
            import traceback

            traceback.print_exc()
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
            }
