# Excel 操作规则

## 规则简介

本规则定义了使用 openpyxl 和 pandas 创建、编辑和分析 Excel 文件的规范。在需要处理 .xlsx、.xlsm、.csv、.tsv 等电子表格文件时，必须遵守本规则。

## 触发条件

- 用户要求创建、编辑或分析 Excel/CSV 文件
- 用户要求处理包含表格数据的文件
- 用户要求生成数据报表或财务模型
- 用户提到 .xlsx、.xls、.csv 等文件格式

## 你必须遵守的原则

### 1. 工具选择原则

**要求说明：**

- **必须**：根据任务类型选择正确的库
  - **pandas**：数据分析、批量操作、简单数据导出
  - **openpyxl**：复杂格式、公式、Excel 特有功能
- **禁止**：对需要公式和格式的场景使用 pandas 写入（会丢失格式）
- **禁止**：对纯数据分析场景使用 openpyxl 逐行操作（效率低）

### 2. 公式优先原则（关键重点）

**要求说明：**

- **必须**：所有计算使用 Excel 公式，而非 Python 计算后硬编码
- **必须**：让电子表格保持动态可更新
- **禁止**：在 Python 中计算结果后写入单元格

**正确做法：**
```python
# ✅ 使用 Excel 公式
sheet['B10'] = '=SUM(B2:B9)'
sheet['C5'] = '=(C4-C2)/C2'
sheet['D20'] = '=AVERAGE(D2:D19)'
```

**错误做法：**
```python
# ❌ Python 计算后硬编码
total = df['Sales'].sum()
sheet['B10'] = total  # 硬编码了值
```

### 3. 公式重算（强制要求）

**要求说明：**

- **必须**：使用 openpyxl 创建/修改文件后，必须调用 recalc.py 重算公式
- **必须**：重算后检查返回的 JSON 结果，确认 status 为 success
- **禁止**：跳过公式重算步骤直接交付文件

```bash
python recalc.py output.xlsx 30
```

**结果判断：**
- `status: success` → 文件可用
- `status: errors_found` → 检查 error_summary 中的错误类型和位置，修复后重新计算

**常见错误：**
- `#REF!`：无效的单元格引用
- `#DIV/0!`：除零错误
- `#VALUE!`：公式中数据类型错误
- `#NAME?`：未识别的公式名

### 4. 公式验证清单

**要求说明：**

- **必须**：在构建完整模型前先测试 2-3 个样本引用
- **必须**：确认列映射正确（如第 64 列 = BL，不是 BK）
- **必须**：记住 Excel 行是 1 索引（DataFrame 第 5 行 = Excel 第 6 行）

**常见陷阱：**
- NaN 处理：使用 `pd.notna()` 检查空值
- 远端列：财务数据常在 50 列以后
- 除零：使用 `/` 前检查分母
- 跨表引用：使用正确格式 `Sheet1!A1`
- 多重匹配：搜索所有出现，不只是第一个

### 5. 财务模型规范

#### 色彩编码标准

| 颜色 | RGB | 含义 |
|------|-----|------|
| 蓝色文字 | 0,0,255 | 硬编码输入、用户会修改的数值 |
| 黑色文字 | 0,0,0 | 所有公式和计算 |
| 绿色文字 | 0,128,0 | 同一工作簿中跨工作表链接 |
| 红色文字 | 255,0,0 | 外部文件链接 |
| 黄色背景 | 255,255,0 | 需要关注的关键假设或需更新的单元格 |

#### 数字格式标准

- **年份**：格式化为文本字符串（如 "2024"，不是 "2,024"）
- **货币**：使用 `$#,##0` 格式；表头必须标注单位（如 "Revenue ($mm)"）
- **零值**：使用格式使零显示为 "-"，包括百分比
- **百分比**：默认 `0.0%` 格式
- **倍数**：格式化为 `0.0x`（如 EV/EBITDA、P/E）
- **负数**：使用括号 `(123)` 而非减号 `-123`

#### 假设放置规则

- **必须**：所有假设（增长率、利润率、倍数等）放在独立的假设单元格中
- **必须**：在公式中使用单元格引用而非硬编码值
- 示例：使用 `=B5*(1+$B$6)` 而非 `=B5*1.05`

#### 硬编码文档要求

- 在硬编码值旁边添加注释，格式："来源: [系统/文档], [日期], [具体引用], [URL]"

### 6. 文件操作规范

#### 创建新文件
```python
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment

wb = Workbook()
sheet = wb.active

# 添加数据
sheet['A1'] = 'Header'
sheet.append(['Row', 'of', 'data'])

# 添加公式
sheet['B2'] = '=SUM(A1:A10)'

# 格式化
sheet['A1'].font = Font(bold=True, color='FF0000')
sheet['A1'].fill = PatternFill('solid', start_color='FFFF00')
sheet['A1'].alignment = Alignment(horizontal='center')
sheet.column_dimensions['A'].width = 20

wb.save('output.xlsx')
```

#### 编辑已有文件
```python
from openpyxl import load_workbook

wb = load_workbook('existing.xlsx')
sheet = wb.active  # 或 wb['SheetName']

# 修改单元格
sheet['A1'] = 'New Value'
sheet.insert_rows(2)
sheet.delete_cols(3)

wb.save('modified.xlsx')
```

#### 读取和分析数据
```python
import pandas as pd

df = pd.read_excel('file.xlsx')                    # 默认第一个 sheet
all_sheets = pd.read_excel('file.xlsx', sheet_name=None)  # 所有 sheet
df.head()       # 预览
df.info()       # 列信息
df.describe()   # 统计
```

### 7. openpyxl 注意事项

- **必须**：单元格索引是 1-based（row=1, column=1 = A1）
- **必须**：读取计算值时使用 `data_only=True`：`load_workbook('file.xlsx', data_only=True)`
- **警告**：用 `data_only=True` 打开并保存会永久丢失公式，替换为值
- 大文件使用 `read_only=True` 读取或 `write_only=True` 写入
- 公式保留但不计算 — 使用 recalc.py 更新值

### 8. pandas 注意事项

- 指定数据类型避免推断问题：`pd.read_excel('file.xlsx', dtype={'id': str})`
- 大文件只读特定列：`pd.read_excel('file.xlsx', usecols=['A', 'C', 'E'])`
- 正确处理日期：`pd.read_excel('file.xlsx', parse_dates=['date_column'])`

### 9. 零公式错误要求

- **必须**：交付的 Excel 文件中零公式错误
- **禁止**：交付包含 #REF!、#DIV/0!、#VALUE!、#N/A、#NAME? 错误的文件

### 10. 保留已有模板

- **必须**：修改模板文件时严格匹配现有格式、样式和约定
- **禁止**：对已有固定格式的文件强加标准化格式
- **必须**：已有模板约定优先于本规则中的通用建议

## 代码风格

- 写简洁的 Python 代码，避免冗余注释
- 避免冗长的变量名和不必要的操作
- 避免不必要的 print 语句