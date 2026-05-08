# PPT 操作规则

## 规则简介

本规则定义了使用 html2pptx 和 OOXML 方式创建、编辑和分析 PowerPoint 文件的规范。在需要处理 .pptx 文件时，必须遵守本规则。

## 触发条件

- 用户要求创建、编辑或分析 PPT/PPTX 文件
- 用户要求制作演示文稿、幻灯片
- 用户提到 .pptx 文件格式
- 用户要求将内容转为演示文稿

## 你必须遵守的原则

### 1. 工作流选择原则

**要求说明：**

| 场景 | 工作流 | 说明 |
|------|--------|------|
| 从零创建 PPT（无模板） | html2pptx 工作流 | HTML → PowerPoint，精确定位 |
| 从零创建 PPT（有模板） | 模板工作流 | 复制/重排模板幻灯片后替换内容 |
| 编辑已有 PPT | OOXML 工作流 | 解包 → 编辑 XML → 打包 |
| 读取 PPT 文本内容 | markitdown | `python -m markitdown file.pptx` |

- **禁止**：选错工作流（如用 OOXML 从零创建、用 html2pptx 编辑已有 PPT）

---

## 工作流 A：从零创建 PPT（html2pptx）

### 2. 设计原则

**要求说明：**

- **必须**：编写代码前先说明设计选择（配色方案、字体、布局）
- **必须**：仅使用 web-safe 字体：Arial、Helvetica、Times New Roman、Georgia、Courier New、Verdana、Tahoma、Trebuchet MS、Impact
- **禁止**：使用 Segoe UI、SF Pro、Roboto 等非通用字体
- **必须**：确保可读性（强对比度、适当字号、清晰对齐）
- **禁止**：使用 CSS 渐变（linear-gradient、radial-gradient）— 它们不会转换到 PowerPoint

### 3. HTML 幻灯片规范

**布局尺寸：**
- 16:9（默认）：`width: 720pt; height: 405pt`
- 4:3：`width: 720pt; height: 540pt`
- 16:10：`width: 720pt; height: 450pt`

**关键文本规则：**
- **必须**：所有文本必须在 `<p>`、`<h1>`-`<h6>`、`<ul>`、`<ol>` 标签内
- **禁止**：将文本直接放在 `<div>` 或 `<span>` 中（不会出现在 PowerPoint 中）
- **禁止**：使用手动项目符号（•、-、*）— 使用 `<ul>` 或 `<ol>`

**样式规则：**
- 背景和边框只对 `<div>` 元素有效，不对文本元素（`<p>`、`<h1>` 等）有效
- 使用 `display: flex` 防止边距塌陷
- 行内格式使用 `<b>`、`<i>`、`<u>` 或 `<span>` 加 CSS 样式

**图标和渐变：**
- **必须**：先使用 Sharp 将渐变/图标光栅化为 PNG，再在 HTML 中引用
- **禁止**：直接在 HTML 中使用 CSS 渐变

### 4. 布局技巧

**包含图表或表格的幻灯片：**
- **推荐**：两列布局 — 一列文字，一列图表/表格（使用 flexbox，如 40%/60%）
- **可选**：全幅布局 — 图表/表格占满整个幻灯片
- **禁止**：将图表/表格放在文字下方垂直堆叠（可读性差）

**HTML 示例：**
```html
<!DOCTYPE html>
<html>
<head>
<style>
html { background: #ffffff; }
body {
  width: 720pt; height: 405pt; margin: 0; padding: 0;
  background: #f5f5f5; font-family: Arial, sans-serif;
  display: flex;
}
.content { margin: 30pt; padding: 40pt; background: #ffffff; }
h1 { color: #2d3748; font-size: 32pt; }
</style>
</head>
<body>
<div class="content">
  <h1>标题</h1>
  <p>正文内容</p>
  <div id="chart" class="placeholder" style="width: 350pt; height: 200pt;"></div>
</div>
</body>
</html>
```

### 5. PptxGenJS 图表规范

**颜色规则（关键）：**
- **禁止**：在 PptxGenJS 中使用 `#` 前缀 — 会导致文件损坏
- ✅ 正确：`color: "FF0000"`，`fill: { color: "0066CC" }`
- ❌ 错误：`color: "#FF0000"`

**图表数据格式：**
```javascript
// 单系列柱状图
slide.addChart(pptx.charts.BAR, [{
    name: "Sales",
    labels: ["Q1", "Q2", "Q3", "Q4"],
    values: [4500, 5500, 6200, 7100]
}], {
    ...placeholders[0],
    barDir: 'col',
    showTitle: true,
    title: 'Quarterly Sales',
    chartColors: ["4472C4"]
});
```

**时间序列数据粒度：**
- < 30 天：按日分组（如 "10-01", "10-02"）
- 30-365 天：按月分组（如 "2024-01"）
- > 365 天：按年分组

**散点图特殊格式：**
- 第一个系列 = X 轴值，后续系列 = Y 值

### 6. 视觉验证（强制要求）

- **必须**：生成 PPT 后创建缩略图验证布局
- **必须**：检查文字截断、文字重叠、定位问题、对比度问题
- 发现问题后调整 HTML 并重新生成

```bash
python scripts/thumbnail.py output.pptx workspace/thumbnails --cols 4
```

---

## 工作流 B：编辑已有 PPT（OOXML）

### 7. OOXML 编辑流程

**操作步骤：**

1. **解包**：`python ooxml/scripts/unpack.py <file.pptx> <output_dir>`
2. **编辑 XML**：主要修改 `ppt/slides/slide{N}.xml`
3. **验证**：`python ooxml/scripts/validate.py <dir> --original <file>` （每次编辑后必须验证）
4. **打包**：`python ooxml/scripts/pack.py <input_dir> <output.pptx>`

- **必须**：每次 XML 编辑后立即验证并修复错误
- **禁止**：跳过验证直接打包

### 8. XML 格式规范

**元素顺序（`<p:txBody>` 内）：** `<a:bodyPr>` → `<a:lstStyle>` → `<a:p>`

**关键规则：**
- 带首尾空格的 `<a:t>` 元素必须加 `xml:space='preserve'`
- `<a:rPr>` 和 `<a:endParaRPr>` 必须加 `dirty="0"`
- 图片添加到 `ppt/media/`，在 slide XML 中引用
- 更新 `ppt/slides/_rels/slideN.xml.rels` 中的关系

**文本格式：**
```xml
<!-- 粗体 -->
<a:r><a:rPr b="1"/><a:t>Bold Text</a:t></a:r>
<!-- 斜体 -->
<a:r><a:rPr i="1"/><a:t>Italic Text</a:t></a:r>
<!-- 字体和颜色 -->
<a:r>
  <a:rPr lang="en-US" sz="2400" b="1" dirty="0">
    <a:solidFill><a:srgbClr val="FF0000"/></a:solidFill>
  </a:rPr>
  <a:t>Colored 24pt Bold</a:t>
</a:r>
```

### 9. 幻灯片操作

**添加新幻灯片：**
1. 创建 `ppt/slides/slideN.xml`
2. 更新 `[Content_Types].xml`：添加 Override
3. 更新 `ppt/_rels/presentation.xml.rels`：添加关系
4. 更新 `ppt/presentation.xml`：在 `<p:sldIdLst>` 添加 slide ID
5. 创建 `ppt/slides/_rels/slideN.xml.rels`（如需要）

**重排幻灯片：**
- 修改 `ppt/presentation.xml` 中 `<p:sldId>` 元素顺序
- 保持 slide ID 和 relationship ID 不变

**删除幻灯片：**
1. 从 `ppt/presentation.xml` 删除 `<p:sldId>` 条目
2. 从 `ppt/_rels/presentation.xml.rels` 删除关系
3. 从 `[Content_Types].xml` 删除 Override
4. 删除 slide XML 和 rels 文件
5. 清理未使用的 media
- **禁止**：对剩余幻灯片重新编号

---

## 工作流 C：使用模板创建 PPT

### 10. 模板工作流

**操作步骤：**

1. **提取模板文本和缩略图：**
   ```bash
   python -m markitdown template.pptx > template-content.md
   python scripts/thumbnail.py template.pptx
   ```

2. **分析模板并保存清单** 到 `template-inventory.md`，记录每张幻灯片的索引、布局和用途

3. **创建演示文稿大纲** `outline.md`，映射内容到模板幻灯片
   - **必须**：布局结构匹配实际内容（2个项用两列，3个项用三列）
   - **禁止**：使用比内容更多的占位符

4. **重排模板幻灯片：**
   ```bash
   python scripts/rearrange.py template.pptx working.pptx 0,34,34,50,52
   ```

5. **提取文本清单：**
   ```bash
   python scripts/inventory.py working.pptx text-inventory.json
   ```

6. **生成替换内容** 保存到 `replacement-text.json`
   - **必须**：包含原始清单中的段落属性（bold、font_size 等）
   - **禁止**：在 bullet: true 的文本中包含项目符号字符（•、-、*）— 自动添加
   - 未列出的 shape 会自动清空

7. **应用替换：**
   ```bash
   python scripts/replace.py working.pptx replacement-text.json output.pptx
   ```

---

## 通用注意事项

### 11. 打包前检查清单

- **必须**：清理未引用的资源（media、fonts、notes 目录）
- **必须**：`[Content_Types].xml` 声明所有存在的 slides、layouts、themes
- **必须**：检查 `_rels` 文件中是否有对已删除资源的引用
- **必须**：验证所有 XML 编码（Unicode 字符需转义）

### 12. 代码风格

- 写简洁代码，避免冗余变量名和操作
- 避免不必要的 print 语句
- 使用 Sharp 预处理渐变和图标为 PNG

### 13. 依赖项

- **markitdown**：`pip install "markitdown[pptx]"` — 文本提取
- **pptxgenjs**：`npm install -g pptxgenjs` — html2pptx 创建
- **playwright**：`npm install -g playwright` — HTML 渲染
- **sharp**：`npm install -g sharp` — 图像处理
- **defusedxml**：`pip install defusedxml` — 安全 XML 解析
- **LibreOffice**：PDF 转换
- **Poppler**：`pdftoppm` PDF 转图片