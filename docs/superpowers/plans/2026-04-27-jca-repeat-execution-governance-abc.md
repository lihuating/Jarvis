# jca 防重复执行治理（A+B+C）落地方案（2026-04-27）

## 背景

长对话/大仓库场景下，`jca`（CodeAgent）可能出现：

- 工具后处理链路较重 → token 更快增长
- 触发上下文压缩/摘要重置
- 摘要后再次做关键验证 → 体验上像“反复分析与确认”

同时，`execute_script` 作为高风险入口，历史上容易在只读查询场景下也触发完整后处理链路。

## 目标

在尽量保证质量（验证可复核、交付可定位）的前提下：

- 将“已交付/已完成”从自然语言升级为可机读状态
- 将只读验证与真实写操作路径分离
- 降低同一会话内重复只读验证的成本

## 方案（A+B+C）

### A：`<JCA_DELIVERY>` 交付落盘 + 短路

- 模型在最终交付时输出 `<JCA_DELIVERY>{...}</JCA_DELIVERY>`
- 落盘到 `.jarvis/code_agent/deliveries/<fingerprint>.*`
- 后续同任务（fingerprint 匹配）默认短路，除非用户显式要求重跑

### B：只读验证缓存

- 对“只读 tools + 只读 execute_script”组合：第一次仍执行、后续相同 key 跳过

### C：只读 `execute_script` 降噪

- 对常见只读命令（保守白名单）允许跳过完整后处理链路

## 代码与文档

- 实现：
  - `src/jarvis/jarvis_code_agent/code_agent_delivery.py`
  - `src/jarvis/jarvis_code_agent/code_agent.py`
- 提示词（分析类场景先行）：
  - `builtin/prompts/code_agent_system/code_analysis.md`
- 用户/开发者文档：
  - `docs/technical/implementation/jca_governance_abc.md`
  - `docs/jarvis_book/4.使用指南.md`（4.5 章节补充）
  - `docs/jarvis_book/8.常见问题.md`（新增 Q14）
  - `docs/best_practices/使用jca进行交互式代码开发.md`

## 风险与边界

- `<JCA_DELIVERY>` 误标 `delivered: true` 会导致短路：需要提示词约束 + 用户可用“重跑”关键词绕过
- `execute_script` 只读判定是保守策略：无法识别的一律按非只读处理（避免误放行写操作）
