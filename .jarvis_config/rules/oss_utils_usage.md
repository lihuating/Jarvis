---
description: 当需要使用OSS工具进行RDC工作项查询、iCenter页面管理、UAC认证或Gerrit代码查询时使用此规则——OSS工具使用规则，OSS Utils是一个统一的命令行工具，提供RDC工作项查询、iCenter页面管理、UAC认证和Gerrit代码查询功能的命令行接口。包括：使用oss rdc search查询工作项；使用oss icenter create/update/get/subtree管理页面；使用oss uac进行认证；使用oss gerrit查询代码；理解工具的命令语法和参数配置；遵循OSS工具使用最佳实践。每当用户提及"OSS工具"、"oss命令"、"RDC查询"、"iCenter管理"、"Gerrit代码"、"i.zte.com.cn"或需要使用OSS工具进行工作项查询、页面管理、代码查询时触发，无论操作类型和复杂度如何。如果需要使用OSS工具的命令行接口，请使用此规则。
---

# OSS 工具使用规则

## 规则简介

OSS Utils 是一个统一的命令行工具，提供 RDC 工作项查询、iCenter 页面管理、UAC 认证和 Gerrit 代码查询功能的命令行接口。本规则文档描述了 OSS 工具的使用方法和最佳实践。

## 你必须遵守的原则

### 1. 使用场景原则

**要求说明：**

- **必须**：当访问或操作 i.zte.com.cn 域名网页时，优先使用 oss icenter 相关的工具
- **必须**：根据具体需求选择合适的命令模块（RDC、iCenter、UAC、Gerrit）
- **禁止**：在有 OSS 工具支持的场景下使用手动操作

## 你必须执行的操作

### 操作1：RDC 工作项查询

**执行步骤：**

1. 使用 `oss rdc search` 命令
2. 提供必需的 `--workspace` 和 `--query` 参数
3. 确保查询条件为有效的 JSON 格式

**示例：**

    ```bash
    oss rdc search --workspace demo --query '{"status": "open"}'
    ```

### 操作2：iCenter 页面管理

**执行步骤：**

1. 使用 `oss icenter create`、`oss icenter update`、`oss icenter get` 或 `oss icenter subtree` 命令
2. 提供必需的参数（标题、内容、空间ID、页面ID、contentId等）
3. 确保参数格式正确
4. 内容可以通过 `--content` 直接传入，或通过 `--content-file` 从文件读取

**示例：**

    ```bash
    # 创建页面 - 方式1：直接传入内容
    oss icenter create \
      --title "API 接口文档" \
      --content "# API 文档\n\n这里是 API 文档内容" \
      --space-id "123" \
      --parent-id "456"

    # 创建页面 - 方式2：从文件读取内容
    oss icenter create \
      --title "API 接口文档" \
      --content-file content.md \
      --space-id "123" \
      --parent-id "456"

    # 更新页面 - 方式1：直接传入内容
    oss icenter update \
      --content-id "789" \
      --space-id "123" \
      --title "更新后的标题" \
      --content "# 更新内容\n\n这是更新后的内容"

    # 更新页面 - 方式2：从文件读取内容
    oss icenter update \
      --content-id "789" \
      --space-id "123" \
      --title "更新后的标题" \
      --content-file updated_content.md

    # 获取页面的第一层子节点
    oss icenter subtree \
      --content-id "789" \
      --space-id "123"
    ```

**注意：**
- `--content` 和 `--content-file` 不能同时使用，必须二选一
- `--content-file` 支持读取任意文本文件（Markdown、HTML、纯文本等）
- 文件路径支持相对路径和绝对路径
- 更新页面需要提供 `--content-id`（页面内容ID）而不是 `--page-id`
- `subtree` 命令返回指定页面的第一层子节点列表，每个节点包含 id、title 等信息

### 操作3：UAC 认证

**执行步骤：**

1. 使用 `oss uac auth` 命令
2. 确保 UDS 服务正常运行
3. 检查环境变量配置
4. 可选：提供 `--username` 和 `--password` 参数（如未提供，将尝试使用缓存或提示输入）

**示例：**

    ```bash
    # 使用缓存认证信息
    oss uac auth

    # 直接提供用户名和密码
    oss uac auth --username xxx --password xxx
    ```

**注意：**
- 如果不提供用户名和密码，工具会尝试使用缓存的认证信息
- 如果缓存无效，则会提示用户输入

### 操作4：Gerrit 代码查询

#### 4.1 查询变更列表 (query-changes)

**执行步骤：**

1. 使用 `oss gerrit query-changes` 命令
2. 提供必需的 `--query` 参数（可多次使用）
3. 可选：使用 `--limit`、`--start`、`--options` 等参数控制输出

**示例：**

    ```bash
    # 查询自己的打开变更
    oss gerrit query-changes --query "status:open+owner:self"

    # 查询关注项目的变更，限制10条
    oss gerrit query-changes --query "status:open+is:watched" --limit 10

    # 多个查询（返回数组数组）
    oss gerrit query-changes --query "status:open" --query "owner:self"

    # 查询并获取标签信息
    oss gerrit query-changes --query "status:open" --options LABELS

    # 分页查询：跳过前20条，获取10条
    oss gerrit query-changes --query "status:open" --start 20 --limit 10
    ```

**查询条件示例：**
- `status:open/closed/merged` - 按状态筛选
- `owner:self` - 自己的变更
- `reviewer:self` - 自己是评审者的变更
- `is:watched` - 关注项目的变更
- `project:项目名` - 指定项目
- 多条件组合：`'status:open+owner:self'`

**额外字段选项 (options)：**
- `LABELS` - 标签摘要和批准者
- `DETAILED_LABELS` - 详细标签信息
- `CURRENT_REVISION` - 当前补丁集信息
- `ALL_REVISIONS` - 所有补丁集信息
- `DOWNLOAD_COMMANDS` - 下载命令
- `CURRENT_COMMIT` - 当前提交详细信息
- `ALL_COMMITS` - 所有提交详细信息
- `CURRENT_FILES` - 当前提交修改的文件
- `ALL_FILES` - 所有提交修改的文件
- `DETAILED_ACCOUNTS` - 详细账户信息
- `REVIEWER_UPDATES` - 评审者更新
- `MESSAGES` - 变更消息
- `CURRENT_ACTIONS` - 可用操作
- `CHANGE_ACTIONS` - 变更级操作
- `REVIEWED` - 已评审标记
- `WEB_LINKS` - Web 链接
- `CHECK` - 潜在问题检查
- `COMMIT_FOOTERS` - 提交脚注
- `PUSH_CERTIFICATES` - 推送证书

**注意：**
- 首次使用时会提示输入用户名和密码，认证信息会被缓存
- 结果按最后更新时间排序，最近更新的在前
- 指定多个查询时，返回值为数组数组
- 如果结果超过限制，最后一个变更对象会包含 `_more_changes: true` 字段

#### 4.2 获取变更信息 (get-change)

**执行步骤：**

1. 使用 `oss gerrit get-change` 命令
2. 提供变更 ID（必需参数）
3. 可选：使用 `--options` 获取额外字段

**示例：**

    ```bash
    # 获取基本信息
    oss gerrit get-change 12345

    # 获取变更和当前提交信息
    oss gerrit get-change Iabc123def456 --options CURRENT_COMMIT

    # 获取变更、消息和详细账户信息
    oss gerrit get-change 12345 --options MESSAGES --options DETAILED_ACCOUNTS
    ```

**注意：**
- 变更 ID 可以是数字（如 12345）或 Gerrit 格式（如 Iabc123def456）
- 可用的选项包括：CURRENT_COMMIT, MESSAGES, DETAILED_ACCOUNTS, DETAILED_LABELS 等
- 如需更详细的信息，请使用 `get-change-detail` 命令

#### 4.3 获取变更详情 (get-change-detail)

**执行步骤：**

1. 使用 `oss gerrit get-change-detail` 命令
2. 提供变更 ID（必需参数）

**示例：**

    ```bash
    # 获取完整详细信息
    oss gerrit get-change-detail 12345

    oss gerrit get-change-detail Iabc123def456
    ```

**注意：**
- 此命令返回变更的完整详细信息，包括所有修订、文件、评论等
- 首次使用时会提示输入用户名和密码，认证信息会被缓存

#### 4.4 设置评审 (set-review)

**执行步骤：**

1. 使用 `oss gerrit set-review` 命令
2. 提供变更 ID（必需参数）
3. 可选：使用 `--label` 设置评分、`--message` 添加消息、`--reviewer` 添加评审者等

**示例：**

    ```bash
    # 设置评分
    oss gerrit set-review 12345 --label Code-Review=1 --label Verified=1

    # 设置评分和消息
    oss gerrit set-review 12345 --label Code-Review=1 --message "LGTM"

    # 指定修订版本
    oss gerrit set-review 12345 --revision-id 123abc --label Code-Review=2

    # 添加评审者
    oss gerrit set-review 12345 --reviewer user1@example.com --reviewer user2@example.com

    # 使用标签
    oss gerrit set-review 12345 --tag "my-review" --label Code-Review=1

    # 添加行级评论（使用JSON文件）
    oss gerrit set-review 12345 --comments-file comments.json
    ```

**注意：**
- 评分范围：-2 到 +2，0 表示无评分
- 常用标签：Code-Review（代码评审）、Verified（验证）等
- 如果需要添加行级评论，请使用 `--comments-file` 指定 JSON 文件
- `--revision-id` 默认为 `current`

#### 4.5 获取补丁文件 (get-patch)

**执行步骤：**

1. 使用 `oss gerrit get-patch` 命令
2. 提供变更 ID（必需参数）
3. 可选：使用 `--revision-id` 指定修订版本
4. 可选：使用 `--output` 保存到文件
5. 可选：使用 `--zip` 获取 ZIP 格式
6. 可选：使用 `--raw` 获取原始 base64

**示例：**

    ```bash
    # 查看补丁内容（自动解码）
    oss gerrit get-patch 12345

    # 保存补丁到文件
    oss gerrit get-patch 12345 --output my_changes.diff

    # 获取 ZIP 格式补丁（避免 base64 解码）
    oss gerrit get-patch 12345 --zip --output patch.zip

    # 获取原始 base64 编码（用于脚本处理）
    oss gerrit get-patch 12345 --raw --output patch.base64

    # 指定修订版本
    oss gerrit get-patch 12345 --revision-id abc123 --output patch.diff

    # 通过管道处理
    oss gerrit get-patch 12345 | less
    oss gerrit get-patch 12345 | grep -i 'todo'
    ```

**注意：**
- 首次使用时会提示输入用户名和密码，认证信息会被缓存
- 默认情况下会自动解码 base64，输出纯文本补丁
- 使用 `--zip` 时必须指定 `--output` 参数
- 使用 `--raw` 时输出原始 base64 编码，不解码
- `--revision-id` 默认为 `current`
- 不指定 `--output` 时，补丁内容会输出到终端

#### 4.6 清除认证信息 (clear)

**执行步骤：**

1. 使用 `oss gerrit clear` 命令
2. 确认删除缓存的认证信息

**示例：**

    ```bash
    # 清除缓存的认证信息
    oss gerrit clear
    ```


**评论 JSON 文件格式说明：**

`--comments-file` 参数支持两种格式：

**格式1：完整请求体格式**（符合 Gerrit REST API 标准）

支持完整的 Gerrit ReviewInput 请求体格式，可同时设置 tag、message、labels 和 comments：

```json
{
  "tag": "jenkins",
  "message": "Some nits need to be fixed.",
  "labels": {"Code-Review": -1},
  "comments": {
    "file/path": [
      {"line": 23, "message": "comment"},
      {"range": {"start_line": 10, "end_line": 15}, "message": "multi-line comment"}
    ]
  }
}
```

**格式2：简化格式**（推荐使用）

直接提供 comments 字典，文件路径映射到评论数组：

```json
{
  "file/path": [
    {"line": 23, "message": "comment"},
    {"range": {"start_line": 10, "end_line": 15}, "message": "multi-line comment"}
  ]
}
```

**重要提示**：
- 必须使用**字典格式**（对象），不能使用数组格式
- 文件路径作为字典的 key，评论数组作为 value
- 每个文件的评论是一个数组，包含多个评论对象
- 工具会自动识别格式类型，建议优先使用简化格式以直接指定行评论


**注意：**
- 此命令会删除已保存的用户名和密码
- 下次使用 Gerrit 相关命令时，需要重新输入认证信息

## 使用场景

- **iCenter 页面管理**：使用 oss 工具可以查询、管理和操作 iCenter 页面内容
- **RDC 工作项查询**：通过 oss 工具查询 RDC 系统中的工作项信息
- **UAC 认证**：通过 oss 工具进行统一认证，简化访问流程
- **Gerrit 代码查询**：通过 oss 工具查询 Gerrit 代码仓库的变更信息、获取补丁文件、设置评审等

## 注意事项

1. **JSON 参数转义**：在 shell 中使用 JSON 参数时，使用单引号包裹 JSON 字符串
2. **环境变量配置**：确保必要的环境变量已正确配置
3. **认证信息缓存**：iCenter、UAC 和 Gerrit 命令都会缓存认证信息，如果需要刷新可以使用 `--username` 和 `--password` 参数重新认证
4. **Gerrit 认证信息**：Gerrit 命令首次使用时会提示输入用户名和密码，后续会自动使用缓存的认证信息
5. **iCenter 内容选项**：`--content` 和 `--content-file` 不能同时使用，必须二选一
6. **Gerrit 分页查询**：使用 `--start` 和 `--limit` 参数实现分页，避免一次性查询大量数据

## 检查清单

在使用 OSS 工具时，必须确认：

- [ ] 命令语法正确
- [ ] 必需参数已提供
- [ ] JSON 参数格式有效
- [ ] 环境变量配置正确
- [ ] 认证信息有效

## 相关资源

- CLI 入口：`{{ git_root_dir }}/src/oss_utils/cli.py`
- RDC 模块：`{{ git_root_dir }}/src/oss_utils/rdc.py`
- iCenter 模块：`{{ git_root_dir }}/src/oss_utils/icenter.py`
- UAC 模块：`{{ git_root_dir }}/src/oss_utils/uac.py`
- Gerrit 模块：`{{ git_root_dir }}/src/oss_utils/gerrit.py`
