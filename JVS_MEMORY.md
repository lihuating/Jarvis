# JVS_MEMORY.md

该文件由 Jarvis 自动生成，用于加速大工程下的启动与“开始回答”时间。

- 生成时间: 2026-03-31 17:28:14
- 项目根目录: /media/vdc/code/Jarvis
- 规则索引指纹: 1d83d652c8f930d42e313be219072273

---

项目概况:
Git托管目录结构（共1598个文件）:
├── .github/
│   └── workflows/
├── .jarvis/
│   ├── evolution/
│   │   └── decisions/
│   ├── jsec/
│   ├── memory/
│   ├── methodologies/
│   ├── rules/
│   │   ├── deployment/
│   │   ├── development_tools/
│   │   ├── evolution/
│   │   └── tool_config/
│   └── spec/
├── .specstory/
│   └── history/
├── builtin/
│   ├── agent/
│   ├── multi_agent/
│   ├── prompts/
│   │   └── code_agent_system/
│   └── rules/
│       ├── agent_personality/
│       ├── architecture_design/
│       ├── code_quality/
│       ├── deployment/
│       ├── development_tools/
│       ├── development_workflow/
│       ├── performance/
│       ├── security/
│       ├── testing/
│       ├── tool_config/
│       └── ui_design/
├── docs/
│   ├── best_practices/
│   ├── compare/
│   ├── images/
│   ├── jarvis_book/
│   ├── superpowers/
│   │   └── plans/
│   └── technical/
│       └── implementation/
├── memory_data/
├── scripts/
├── src/
│   ├── jarvis/
│   │   ├── jarvis_agent/
│   │   │   └── language_extractors/
│   │   ├── jarvis_browser/
│   │   ├── jarvis_c2rust/
│   │   ├── jarvis_code_agent/
│   │   │   └── code_analyzer/
│   │   │       ├── build_validator/
│   │   │       └── languages/
│   │   ├── jarvis_config/
│   │   ├── jarvis_data/
│   │   │   └── tiktoken/
│   │   ├── jarvis_git_squash/
│   │   ├── jarvis_git_utils/
│   │   ├── jarvis_jck/
│   │   ├── jarvis_lsp/
│   │   ├── jarvis_mcp/
│   │   ├── jarvis_memory_organizer/
│   │   ├── jarvis_methodology/
│   │   ├── jarvis_platform/
│   │   ├── jarvis_platform_manager/
│   │   ├── jarvis_sec/
│   │   │   └── checkers/
│   │   ├── jarvis_smart_shell/
│   │   ├── jarvis_tools/
│   │   │   └── cli/
│   │   ├── jarvis_utils/
│   │   ├── jarvis_windows/
│   │   └── scripts/
│   └── jarvis_rust_tools/
│       └── src/
└── tests/
    ├── jarvis_agent/
    ├── jarvis_c2rust/
    ├── jarvis_code_agent/
    ├── jarvis_config/
    ├── jarvis_git_utils/
    ├── jarvis_lsp/
    ├── jarvis_mcp/
    ├── jarvis_memory_organizer/
    ├── jarvis_platform/
    ├── jarvis_platform_manager/
    ├── jarvis_sec/
    ├── jarvis_smart_shell/
    ├── jarvis_tools/
    ├── jarvis_utils/
    ├── performance/
    ├── regression/
    ├── security/
    └── test_utils/

最近提交:
提交 1: 07b0186 - chore(project): 添加项目文档、配置规范及NBSA03根文件系统结构 (20个文件)
    - nbsa03/ramdisk_make/nfsroot-arm/sbin/iproute
    - nbsa03/ramdisk_make/nfsroot-arm/usr/sbin/rdate
    - nbsa03/ramdisk_make/nfsroot-arm/usr/sbin/ubiattach
    - nbsa03/ramdisk_make/nfsroot-arm/sbin/slattach
    - nbsa03/ramdisk_make/nfsroot-arm/usr/sbin/nanddump
    ...
提交 2: a6babd5 - RDC:ITRAN-1788445 ossmoni 任务top命令采集优化 (2个文件)
    - osscommon/main_control_board/oss_script/common_script/OssMoni.sh
    - vswe/ramdisk_make/oss/OssMoni.sh
提交 3: f9aaee9 - RDC:ITRAN-1681020 mmap预留内存地址管理 AND OSS mmap地址预留设置 (11个文件)
    - vbpd2/ramdisk_make/rcs/reserve_multi_mm_addr.sh
    - vbpd6/rcs
    - vbpd6/ramdisk_make/make_ramdisk_bin.sh
    - gbae_be/ramdisk_make/rcs/reserve_multi_mm_addr.sh
    - osscommon/check_multi_addr_reserv.sh
    ...
提交 4: b03a205 - RDC:ITRAN-1651041 vsae 一键采集信息添加 (1个文件)
    - vsae/ramdisk_make/log_config/collect_config.json
提交 5: 2e28ad3 - RDC:ITRAN-1420465 OssMoni.sh脚本优化 (2个文件)
    - osscommon/main_control_board/oss_script/common_script/OssMoni.sh
    - vswe/ramdisk_make/oss/OssMoni.sh
工具概况: read_code, memory, methodology, search_web, load_rule, meta_agent, task_list_manager, read_webpage, edit_file, execute_script, virtual_tty, vsw_mem_collect（共12个）
