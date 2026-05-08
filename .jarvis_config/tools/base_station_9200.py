# -*- coding: utf-8 -*-
import os
import subprocess
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from jarvis.jarvis_utils.output import PrettyOutput


class BaseStation9200Tool:
    """9200 基站综合操作工具

    支持对 9200 基站进行远程操作：
    1. 远程命令执行（主控板/基带板）
    2. 文件下载（从基站下载文件到本地）
    3. 日志采集（按故障类型采集对应日志）
    4. 系统信息查询（CPU、内存、磁盘、进程）
    """

    name = "base_station_9200"
    description = """9200基站综合操作工具，提供对9200基站的自动化操作能力。

    功能包括：
    1. SSH连接管理 - 支持连接主控单板和基带板
    2. 远程命令执行 - 在基站上执行命令并返回结果
    3. 文件下载 - 从基站下载文件到本地
    4. 日志采集 - 按故障类型采集对应的日志文件
    5. 系统信息查询 - 获取基站的CPU、内存、磁盘、进程等信息

    登录凭据：
    - 主控单板：用户名itran，密码Itran_2430!@#
    - 基带板：用户名root，密码Itran_2430!@#$
    """
    parameters = {
        "type": "object",
        "properties": {
            "base_ip": {
                "type": "string",
                "description": "基站主控单板IP地址，例如：192.168.1.100",
            },
            "operation": {
                "type": "string",
                "enum": ["exec_command", "download", "collect_logs", "system_info"],
                "description": "操作类型：exec_command（执行命令）、download（下载文件）、collect_logs（采集日志）、system_info（系统信息）",
            },
            "command": {
                "type": "string",
                "description": "要执行的远程命令（exec_command时必需）",
            },
            "remote_path": {
                "type": "string",
                "description": "远程文件路径（download时必需）",
            },
            "local_path": {
                "type": "string",
                "description": "本地保存路径（download时使用，默认当前目录）",
            },
            "log_type": {
                "type": "string",
                "enum": ["reset_board", "reset_container", "cpu", "memory", "init", "comm", "blackbox", "all"],
                "description": "日志类型（collect_logs时使用）：reset_board（单板复位）、reset_container（容器复位）、cpu（CPU冲高）、memory（内存问题）、init（初始化）、comm（通信问题）、blackbox（黑匣子）、all（全部）",
            },
            "board_type": {
                "type": "string",
                "enum": ["main", "baseband"],
                "description": "单板类型：main（主控板，默认）或 baseband（基带板）",
            },
            "slot": {
                "type": "integer",
                "description": "槽位号（操作基带板时必需，默认3）",
            },
            "timeout": {
                "type": "integer",
                "description": "命令超时时间（秒），默认300",
            },
        },
        "required": ["base_ip", "operation"],
    }

    # 9200 基站登录信息
    MAIN_USER = "itran"
    MAIN_PASSWORD = "Itran_2430!@#"
    BASEBAND_USER = "root"
    BASEBAND_PASSWORD = "Itran_2430!@#$"

    # 日志路径配置
    MAIN_LOG_PATHS = {
        "system": "/logs/OssLog/",
        "container": "/logs/oss/oss/",
        "kernel": "/var/log/",
        "blackbox": "/mnt/flash/BBX/",
        "dockerd": "/var/log/",
    }

    BASEBAND_LOG_PATHS = {
        "bbx": "/mnt/flash/BBX/",
        "osslog": "/mnt/flash/OssLog/",
    }

    # 故障类型 → 日志采集配置
    FAULT_LOG_MAP = {
        "reset_board": {
            "main": [
                ("/logs/OssLog/BBX_Simplelog.cur", "BBX_Simplelog.cur"),
                ("/mnt/flash/BBX/", "blackbox_main"),
            ],
            "cmds": ["ls -lt /var/log/Kernel-*.log.gz 2>/dev/null | head -3"],
        },
        "reset_container": {
            "main": [
                ("/logs/oss/oss/", "container_logs"),
            ],
            "cmds": [
                "find /logs/oss/oss/ -name 'exit.txt*' -type f 2>/dev/null | head -5",
                "ls -lt /logs/oss/Coredump/ 2>/dev/null | head -5",
                "ls -lt /logs/oss/CoredumpBak/ 2>/dev/null | head -5",
            ],
        },
        "cpu": {
            "main": [
                ("/logs/OssLog/OssCoreCpu.log", "OssCoreCpu.log"),
                ("/logs/OssLog/OssCpu.log", "OssCpu.log"),
                ("/logs/OssLog/OssCpuLoop.log", "OssCpuLoop.log"),
            ],
            "cmds": ["cat /proc/cpuinfo | head -20"],
        },
        "memory": {
            "main": [
                ("/logs/OssLog/mem.log", "mem.log"),
            ],
            "cmds": [
                "cat /proc/meminfo | head -20",
                "find /logs/OssLog/ -name 'MemLeak_*.log' -type f 2>/dev/null | head -5",
                "find /logs/OssLog/ -name 'oomMoni_*.log' -type f 2>/dev/null | head -5",
                "find /logs/OssLog/ -name 'ProcMemInfo.log' -type f 2>/dev/null | head -3",
            ],
        },
        "init": {
            "main": [],
            "cmds": [
                "ls -lt /logs/OssLog/*.log 2>/dev/null | head -10",
                "find /logs/oss/oss/ -name '*.log' -type f -newer /tmp/.oss_init 2>/dev/null | head -10",
            ],
        },
        "comm": {
            "main": [],
            "cmds": [
                "grep -r 'rudp' /logs/OssLog/ 2>/dev/null | tail -20",
                "grep -r 'RUDP' /logs/OssLog/ 2>/dev/null | tail -20",
                "grep -r 'comm_broken\\|comm_setup' /logs/OssLog/ 2>/dev/null | tail -20",
            ],
        },
        "blackbox": {
            "main": [
                ("/mnt/flash/BBX/", "blackbox_main"),
            ],
            "cmds": ["ls -lt /mnt/flash/BBX/ 2>/dev/null | head -10"],
        },
        "all": {
            "main": [
                ("/logs/OssLog/", "OssLog"),
                ("/mnt/flash/BBX/", "blackbox"),
            ],
            "cmds": [],
        },
    }

    def _check_sshpass(self) -> bool:
        try:
            subprocess.run(["which", "sshpass"], check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError:
            PrettyOutput.auto_print("❌ sshpass 未安装，请先安装: sudo yum install -y sshpass")
            return False

    def _ssh_exec(self, host: str, user: str, password: str, command: str, timeout: int = 300) -> Dict[str, Any]:
        """通过 SSH 执行远程命令"""
        ssh_cmd = f"sshpass -p '{password}' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 {user}@{host} '{command}'"
        try:
            result = subprocess.run(
                ssh_cmd, shell=True, capture_output=True, text=True,
                timeout=timeout, encoding='utf-8', errors='ignore'
            )
            return {
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
        except subprocess.TimeoutExpired:
            return {"exit_code": -1, "stdout": "", "stderr": f"命令执行超时({timeout}s)"}
        except Exception as e:
            return {"exit_code": -1, "stdout": "", "stderr": str(e)}

    def _ssh_download(self, host: str, user: str, password: str, remote_path: str, local_path: str) -> bool:
        """通过 SCP 下载文件"""
        os.makedirs(os.path.dirname(local_path) if os.path.dirname(local_path) else '.', exist_ok=True)
        scp_cmd = f"sshpass -p '{password}' scp -o StrictHostKeyChecking=no -o ConnectTimeout=10 {user}@{host}:{remote_path} {local_path}"
        try:
            result = subprocess.run(scp_cmd, shell=True, capture_output=True, text=True, timeout=300)
            return result.returncode == 0
        except Exception as e:
            PrettyOutput.auto_print(f"❌ 下载失败: {e}")
            return False

    def _get_baseband_ip(self, slot: int) -> str:
        return f"192.254.{slot}.16"

    def _get_ssh_creds(self, board_type: str, slot: int = 3) -> tuple:
        """获取 SSH 连接信息，返回 (host, user, password)"""
        if board_type == "baseband":
            return self._get_baseband_ip(slot), self.BASEBAND_USER, self.BASEBAND_PASSWORD
        return None, self.MAIN_USER, self.MAIN_PASSWORD  # host 使用 base_ip

    def _exec_command(self, base_ip: str, command: str, board_type: str = "main", slot: int = 3, timeout: int = 300) -> str:
        """执行远程命令"""
        host, user, password = self._get_ssh_creds(board_type, slot)
        if host is None:
            host = base_ip

        if board_type == "baseband":
            # 基带板通过主控板中转
            PrettyOutput.auto_print(f"📡 通过主控板 {base_ip} 中转连接基带板 {host}")
            tunnel_cmd = f"sshpass -p '{self.MAIN_PASSWORD}' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 {self.MAIN_USER}@{base_ip} \"sshpass -p '{password}' ssh -o StrictHostKeyChecking=no {user}@{host} '{command}'\""
            try:
                result = subprocess.run(tunnel_cmd, shell=True, capture_output=True, text=True, timeout=timeout)
                output = result.stdout
                if result.stderr:
                    output += f"\nSTDERR: {result.stderr}"
                return output if output else "(无输出)"
            except subprocess.TimeoutExpired:
                return f"❌ 命令执行超时({timeout}s)"
            except Exception as e:
                return f"❌ 命令执行失败: {e}"
        else:
            r = self._ssh_exec(host, user, password, command, timeout)
            output = r["stdout"]
            if r["stderr"]:
                output += f"\nSTDERR: {r['stderr']}"
            return output if output else "(无输出)"

    def _download_file(self, base_ip: str, remote_path: str, local_path: str, board_type: str = "main", slot: int = 3) -> str:
        """下载文件"""
        if not local_path:
            local_path = os.path.basename(remote_path)

        if board_type == "baseband":
            # 基带板：先从基带板传到主控板，再从主控板下载到本地
            bb_ip = self._get_baseband_ip(slot)
            PrettyOutput.auto_print(f"📡 基带板文件中转: {bb_ip}:{remote_path} → {base_ip} → 本地")

            # 1. 在主控板上从基带板下载
            tmp_file = f"/home/{self.MAIN_USER}/bb_transfer_{int(time.time())}"
            transfer_cmd = f"sshpass -p '{self.MAIN_PASSWORD}' ssh -o StrictHostKeyChecking=no {self.MAIN_USER}@{base_ip} \"sshpass -p '{self.BASEBAND_PASSWORD}' scp -o StrictHostKeyChecking=no {self.BASEBAND_USER}@{bb_ip}:{remote_path} {tmp_file}\""
            r = subprocess.run(transfer_cmd, shell=True, capture_output=True, text=True, timeout=300)
            if r.returncode != 0:
                return f"❌ 基带板文件传到主控板失败: {r.stderr}"

            # 2. 从主控板下载到本地
            if self._ssh_download(base_ip, self.MAIN_USER, self.MAIN_PASSWORD, tmp_file, local_path):
                # 3. 清理主控板临时文件
                self._ssh_exec(base_ip, self.MAIN_USER, self.MAIN_PASSWORD, f"rm -f {tmp_file}")
                return f"✅ 文件下载成功: {local_path}"
            return f"❌ 从主控板下载到本地失败"
        else:
            # 主控板直接下载
            if self._ssh_download(base_ip, self.MAIN_USER, self.MAIN_PASSWORD, remote_path, local_path):
                return f"✅ 文件下载成功: {local_path}"
            return f"❌ 文件下载失败: {remote_path}"

    def _collect_logs(self, base_ip: str, log_type: str, local_path: str = None) -> str:
        """按故障类型采集日志"""
        if not local_path:
            local_path = f"bug_{log_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        os.makedirs(local_path, exist_ok=True)

        config = self.FAULT_LOG_MAP.get(log_type)
        if not config:
            return f"❌ 不支持的日志类型: {log_type}"

        results = []

        # 1. 执行诊断命令
        cmds = config.get("cmds", [])
        if cmds:
            PrettyOutput.auto_print(f"\n🔍 执行诊断命令...")
            diag_file = os.path.join(local_path, "diagnostic.txt")
            with open(diag_file, 'w') as f:
                for cmd in cmds:
                    f.write(f"\n{'='*60}\n")
                    f.write(f"命令: {cmd}\n")
                    f.write(f"{'='*60}\n")
                    output = self._exec_command(base_ip, cmd)
                    f.write(output + "\n")
            results.append(f"✅ 诊断信息: {diag_file}")

        # 2. 下载日志文件
        main_files = config.get("main", [])
        for item in main_files:
            remote_src, label = item
            PrettyOutput.auto_print(f"📦 采集日志: {label} ({remote_src})")

            # 检查是否是目录
            check = self._ssh_exec(base_ip, self.MAIN_USER, self.MAIN_PASSWORD, f"test -d {remote_src} && echo DIR || echo FILE")
            is_dir = "DIR" in check.get("stdout", "")

            if is_dir:
                # 打包目录
                archive = f"/tmp/{label}_{int(time.time())}.tar.gz"
                self._ssh_exec(base_ip, self.MAIN_USER, self.MAIN_PASSWORD, f"cd {remote_src} && tar -czf {archive} . 2>/dev/null")
                local_file = os.path.join(local_path, f"{label}.tar.gz")
                if self._ssh_download(base_ip, self.MAIN_USER, self.MAIN_PASSWORD, archive, local_file):
                    results.append(f"✅ {label}: {local_file}")
                else:
                    results.append(f"❌ {label}: 下载失败")
                self._ssh_exec(base_ip, self.MAIN_USER, self.MAIN_PASSWORD, f"rm -f {archive}")
            else:
                # 下载单个文件
                local_file = os.path.join(local_path, os.path.basename(remote_src))
                if self._ssh_download(base_ip, self.MAIN_USER, self.MAIN_PASSWORD, remote_src, local_file):
                    results.append(f"✅ {label}: {local_file}")
                else:
                    results.append(f"❌ {label}: 文件不存在或下载失败")

        if not results:
            return f"⚠️ 未找到 {log_type} 对应的日志文件"

        return f"日志采集完成，保存到: {local_path}\n" + "\n".join(results)

    def _system_info(self, base_ip: str, board_type: str = "main", slot: int = 3) -> str:
        """查询系统信息"""
        host, user, password = self._get_ssh_creds(board_type, slot)
        if host is None:
            host = base_ip

        info_cmds = [
            ("系统信息", "uname -a"),
            ("CPU信息", "cat /proc/cpuinfo | head -30"),
            ("内存信息", "cat /proc/meminfo | head -20"),
            ("磁盘使用", "df -h"),
            ("运行时间/负载", "uptime"),
            ("进程概览", "ps aux --sort=-%mem | head -20"),
        ]

        if board_type == "main":
            info_cmds.extend([
                ("容器状态", "docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' 2>/dev/null || echo 'docker命令不可用'"),
                ("OSS进程", "ps aux | grep -i oss | grep -v grep | head -10"),
            ])

        output_parts = []
        for label, cmd in info_cmds:
            PrettyOutput.auto_print(f"📊 获取 {label}...")
            result = self._exec_command(base_ip, cmd, board_type, slot)
            output_parts.append(f"\n{'='*60}\n{label}\n{'='*60}\n{result}")

        return "\n".join(output_parts)

    def execute(self, **kwargs) -> str:
        """执行基站操作"""
        base_ip = kwargs.get("base_ip")
        operation = kwargs.get("operation")

        if not base_ip:
            return "❌ 必须提供 base_ip 参数"

        if not self._check_sshpass():
            return "❌ 请先安装 sshpass 工具"

        if operation == "exec_command":
            command = kwargs.get("command")
            if not command:
                return "❌ exec_command 操作必须提供 command 参数"
            board_type = kwargs.get("board_type", "main")
            slot = kwargs.get("slot", 3)
            timeout = kwargs.get("timeout", 300)
            PrettyOutput.auto_print(f"📡 在 {board_type} 上执行命令: {command}")
            return self._exec_command(base_ip, command, board_type, slot, timeout)

        elif operation == "download":
            remote_path = kwargs.get("remote_path")
            if not remote_path:
                return "❌ download 操作必须提供 remote_path 参数"
            local_path = kwargs.get("local_path", os.path.basename(remote_path))
            board_type = kwargs.get("board_type", "main")
            slot = kwargs.get("slot", 3)
            PrettyOutput.auto_print(f"📥 下载文件: {remote_path} → {local_path}")
            return self._download_file(base_ip, remote_path, local_path, board_type, slot)

        elif operation == "collect_logs":
            log_type = kwargs.get("log_type", "all")
            local_path = kwargs.get("local_path")
            PrettyOutput.auto_print(f"📦 采集日志类型: {log_type}")
            return self._collect_logs(base_ip, log_type, local_path)

        elif operation == "system_info":
            board_type = kwargs.get("board_type", "main")
            slot = kwargs.get("slot", 3)
            PrettyOutput.auto_print(f"📊 查询 {board_type} 系统信息")
            return self._system_info(base_ip, board_type, slot)

        else:
            return f"❌ 不支持的操作类型: {operation}"
