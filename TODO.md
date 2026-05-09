# Jarvis 项目待办事项

> 创建时间: 2026-05-09

## 功能开发

### jarvis-code-review
- [ ] 实现 jarvis-code-review 命令（`jcr`）
  - 智能代码审查功能
  - 集成 LSP 和静态分析

### jarvis-smart-shell
- [ ] 完善智能 Shell 功能（`jss`）

## 用户体验优化

### 输入处理
- [ ] ESC 停止输入功能
  - 在交互模式下，按 ESC 键可取消当前正在输入的内容
  - 适用于 jvs/jca 等交互式命令

## 扩展功能

### VSCode 插件
- [ ] 开发 VSCode 插件
  - 在 VSCode 编辑器中集成 Jarvis 功能
  - 支持代码编辑、运行命令、查看输出等
  - 参考 JetBrains 插件的设计思路

## 已知问题

- [ ] jarvis-code-review 模块尚未实现（setup.py 已注册但无代码）

## 待优化功能

### 内置命令完善
- [ ] MemoryTags 需要完善
  - 优化标签列表的显示和检索功能
  - 支持标签统计和排序
  - 改进标签过滤和搜索能力
