@echo off
REM Windows 登录时启动 WSL 内 Jarvis child 节点
wsl.exe bash -lc "/home/lihuating/.jarvis/start-child-node.sh"
