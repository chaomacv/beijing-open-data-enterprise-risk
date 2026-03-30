# Beijing Open Data Enterprise Risk Pipeline

基于北京市公共数据开放平台的企业风控数据筛选、下载、标签化与画像构建流水线。

本项目的目标是从北京市公共数据开放平台（<https://data.beijing.gov.cn/>）的大规模公开数据集中，筛选出银行感兴趣的涉企信息，将原本以“数据集”为单位的开放数据，转化为以“企业”为中心、带有结构化标签的风险画像数据条目。

## 任务介绍

### 目标

围绕北京市公共数据开放平台中的公开数据，构建企业标签化体系，用于：

- 贷前风控
- 精准获客与营销参考
- 金融产品创新与场景化建模
- 企业经营与合规信息补充

### 原始数据规模

- 原始目录规模：约 `4433` 个数据集
- 总数据量：约 `1.77` 亿条记录
- 数据集类型覆盖处罚、公示、资质、补贴、荣誉、备案、经营名录等多类涉企信息

数据集示例包括：

- 文物领域行政处罚信息
- 违反《中华人民共和国著作权法》处罚数据
- 北京市在建水利工程项目台账
- 经开区小微企业贷款贴息政策拟支持企业名单
- 东城园国高新企业名单

### 任务要求

- 剔除与企业无关的信息
- 筛选出银行真正感兴趣的涉企数据
- 将公开数据整理为“以企业为中心”的标签化条目
- 支持从“企业视角”和“标签视角”两种方式组织结果

## 实现思路

整体实现步骤如下：

1. 分析数据内容和结构
2. 提炼数据集名称关键词
3. 使用关键词对数据集进行初步筛选与分类
4. 对筛选出的数据集进行人工精细化复核
5. 对保留数据集自动补充更新时间和具体文件名，并批量下载
6. 对下载后的数据文件自动抽取公司主体并打标签
7. 聚合形成最终的企业标签化数据条目和风控宽表

## 多轮筛选流程

### 第一轮：模型初筛

第一轮使用 `Gemini Pro` 对数据目录文件进行大规模过滤，目标是“只要与企业相关，就尽量保留”。

- 筛选前：`4433`
- 筛选后：`2431`
- 保留比例：约 `50%`

初筛逻辑：

- 保留主体为企业、公司、个体工商户、商业机构的数据
- 保留能反映企业经营活动、合规情况、荣誉、补贴、许可、资质、处罚、检查、备案等信息的数据
- 剔除个人、民生、公共设施、自然环境、纯政府内部事务等明显非企数据

被过滤的数据示例包括：

- 鲜羊肉价格
- 图书馆图书信息
- 北京市主要农作物品种审定名录
- 压力管道使用登记证信息
- 婚姻登记机关
- 电动自行车充电设施信息

### 第二轮：人工基于目录和摘要复筛

第二轮结合文件名和摘要进行人工复核，进一步收缩到更高相关度的数据集。

- 筛选前：`2431`
- 筛选后：`952`
- 保留比例：约 `40%`

这一轮重点判断：

- 数据是否真正以企业为核心主体
- 是否具备银行业务参考价值
- 是否虽然“看起来涉企”，但对金融决策帮助有限

### 第三轮：基于具体数据条目的内容分析

第三轮深入具体数据条目本身，继续分析字段结构和内容，再做一次过滤。

- 筛选前：`952`
- 筛选后：`536`
- 保留比例：约 `50%`

这一轮完成后，沉淀出了后续自动分类所需的关键词体系和数据集类别理解。

## 关键词提炼与分类

在多轮筛选的基础上，项目总结出一组稳定的数据集名称关键词，用于自动分类和打标。

目前脚本中主要覆盖的一级分类包括：

- 严重信用违约风险
- 经营合规预警
- 经济优质企业
- 科技与创新实力
- 政府表彰与荣誉
- 政策扶持与奖补

这部分规则已经体现在 [enterprise_kyc_classifier.py](./scripts/enterprise_kyc_classifier.py) 中。

## 工程化处理链路

从北京市开放数据平台下载的目录总表开始，整个工程链路如下：

1. `output/目录清单.xlsx`(from https://data.beijing.gov.cn/)
2. 运行`scripts/enterprise_kyc_classifier.py`
3. 输出`output/目录清单_分类结果.xlsx`
4. 人工筛选与剔除不感兴趣内容
5. 输出`output/目录清单_分类结果_人工过筛.xlsx`
6. 运行`scripts/dataset_freshness_and_filename_updater.py`
7. 输出`output/目录清单_分类结果_人工过筛_更新时间_补充文件名.xlsx`
8. 运行`scripts/prune_columns.py`
9. 输出`output/目录清单_分类结果_人工过筛_更新时间_补充文件名_精简列信息.xlsx`
10. 运行`scripts/build_entity_profile_one_pass.py`
11. 输出`output/特征矩阵风控模型宽表.xlsx`

更详细的脚本级流程见 [docs/pipeline.md](./docs/pipeline.md)。

## 最终产出

最终形成的结果包括：

- 以企业为中心的标签化数据条目
- 以标签为中心的企业命中结果
- 企业风险特征宽表
- 对应的 JSON 导出结果

当前仓库已保留项目代码、文档、数据样本以及大部分处理中间结果和输出结果。

## 当前结构

```text
bank/
├── README.md
├── .gitignore
├── pyproject.toml
├── requirements.txt
├── docs/
│   └── pipeline.md
├── scripts/
│   ├── enterprise_kyc_classifier.py
│   ├── dataset_freshness_and_filename_updater.py
│   ├── batch_downloader.py
│   ├── prune_columns.py
│   └── build_entity_profile_one_pass.py
├── dataset/
│   ├── README.md
│   └── *.csv
└── output/
    ├── README.md
    ├── 目录清单.xlsx
    ├── 目录清单_分类结果.xlsx
    ├── 目录清单_分类结果_人工过筛.xlsx
    ├── 特征矩阵风控模型宽表_*.xlsx
    └── *.json
```

其中：

- `scripts/` 是核心处理脚本
- `docs/` 是流程说明文档
- `dataset/` 存放原始开放数据和样例数据
- `output/` 存放人工过筛表、中间产物和结果宽表

## 核心脚本

- `scripts/enterprise_kyc_classifier.py`
  从原始目录总表出发，对数据集名称做规则分类打标
- `scripts/dataset_freshness_and_filename_updater.py`
  访问数据集详情页，补充更新时间与具体文件名称
- `scripts/batch_downloader.py`
  手动扫码登录后批量触发数据下载
- `scripts/prune_columns.py`
  保留画像构建需要的最小索引字段集
- `scripts/build_entity_profile_one_pass.py`
  从下载数据中抽取企业名称并构建风控宽表

## 快速开始

### 1. 安装依赖

```bash
cd bank
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. 运行处理流程

```bash
python scripts/enterprise_kyc_classifier.py

# 人工复核后生成：
# output/目录清单_分类结果_人工过筛.xlsx

python scripts/dataset_freshness_and_filename_updater.py
python scripts/prune_columns.py

python scripts/batch_downloader.py \
  --input output/目录清单_分类结果_人工过筛_更新时间_补充文件名.xlsx \
  --download-dir output/bank

python scripts/build_entity_profile_one_pass.py \
  --index-file output/目录清单_分类结果_人工过筛_更新时间_补充文件名_精简列信息.xlsx \
  --csv-dir output/bank \
  --output-file output/特征矩阵风控模型宽表.xlsx
```

## 说明

- Selenium 相关脚本依赖本机 Chrome 浏览器和匹配版本的 ChromeDriver
- `output/` 中的文件名保留了项目真实处理过程，便于回溯每一步的输入输出
- 当前仓库为了适配 GitHub 文件大小限制，少数超大原始数据文件未一并推送
## Agent 扩展：非企业数据处理流程

除了企业数据外，本项目还扩展支持对**非企业机构**（如事业单位、社会团体、社会组织、医疗机构、学校等）的数据处理与标签化。

### 处理架构概览

非企业数据处理采用**双路径并行**架构，根据数据文件的特点选择不同的处理方式：

```
dataset/非企业数据文件大json/
    │
    ├─→ 路径一：Gemini智能批处理（适合短上下文文件）
    │   │
    │   ├─→ 读取 CodeGeneratePrompt.txt（提示词模板）
    │   ├─→ gemini_batchThreadPoolExecutor.py（多线程并行处理）
    │   └─→ agent/output_results/xxx_result.json
    │
    └─→ 路径二：定制化脚本转换（适合复杂/大文件）
        │
        ├─→ 浏览文件名 + 查看前几行内容
        ├─→ 根据CodeGeneratePrompt.txt编写convert_xxx.py
        ├─→ 执行定制化转换脚本
        └─→ agent/output_results/xxx_result.json
    │
    └─→ 路径三：批量通用转换（简单文件快速处理）
        │
        ├─→ batch_convert.py（智能字段识别，通用映射）
        └─→ agent/output_results/xxx_result.json
    │
    ↓
agent/output_results/ (所有结果聚合)
    ↓
非企业数据矩阵特征宽表.xlsx (最终宽表)
```

### 三条处理路径详解

#### 路径一：Gemini智能批处理（推荐用于短上下文文件）

**适用场景**：
- 文件结构简单、字段清晰
- 数据条数适中（几千到几万条）
- 不需要复杂的字段映射或条件判断

**处理流程**：

1. **准备提示词模板** (`agent/CodeGeneratePrompt.txt`)
   ```
   该文件包含完整的提示词模板，定义了：
   - 目标群体过滤规则（保留/排除/豁免）
   - 标签生成逻辑（基础标签+细化标签）
   - 输出格式要求（JSON结构）
   - 参考标签库（244个标准标签）
   ```

2. **执行批处理** (`agent/gemini_batchThreadPoolExecutor.py`)
   ```bash
   cd agent
   python gemini_batchThreadPoolExecutor.py \
       --input dataset/非企业数据文件大json/ \
       --prompt CodeGeneratePrompt.txt \
       --output output_results/
   ```

3. **工作原理**：
   - 读取提示词模板作为系统指令
   - 对每个JSON文件：提取文件名 + 前3行样例数据
   - 调用Gemini API生成转换代码逻辑
   - 多线程并行处理多个文件
   - 输出标准化的 `_result.json` 文件

**优点**：
- 无需手动编写转换脚本
- 自动识别字段映射关系
- 批量处理效率高

---

#### 路径二：定制化脚本转换（适合复杂/特殊文件）

**适用场景**：
- 文件结构复杂，需要特殊处理逻辑
- 包含合并单元格（如Excel转JSON）
- 需要多字段组合判断或复杂标签映射
- 数据量超大（几十万条以上）

**处理流程**：

1. **分析文件结构**
   ```bash
   # 查看文件名和前几行
   cat "文件名.json" | python3 -c "
   import json,sys
   d=json.load(sys.stdin)
   print('Columns:', d.get('columns'))
   print('First row:', json.dumps(d.get('data',[])[0], ensure_ascii=False, indent=2))
   "
   ```

2. **参考提示词模板编写脚本**
   
   基于 `agent/CodeGeneratePrompt.txt` 中的规则，编写定制化转换脚本：
   
   ```python
   # agent/convert_xxx.py 模板
   import json
   import os
   
   INPUT_FILE = "dataset/非企业数据文件大json/xxx.json"
   OUTPUT_FILE = "agent/output_results/xxx_result.json"
   
   def convert_file():
       with open(INPUT_FILE, 'r', encoding='utf-8') as f:
           input_data = json.load(f)
       
       data_rows = input_data.get('data', [])
       results = []
       
       for row in data_rows:
           # 1. 提取单位名称（根据实际字段调整）
           entity_name = row.get('社会组织名称', '').strip()
           
           # 2. 提取信用代码（如有）
           credit_code = row.get('统一社会信用代码', '').strip() or None
           
           # 3. 应用目标群体过滤规则（来自CodeGeneratePrompt.txt）
           #    - 排除以'9'开头的私企（除非豁免）
           #    - 保留机关、事业单位、社会组织等
           
           # 4. 生成标签（基础标签+细化标签）
           tag = "根据字段内容生成的标签"
           
           if entity_name:
               results.append({
                   "entity_name": entity_name,
                   "credit_code": credit_code,
                   "tag": tag
               })
       
       # 5. 输出标准格式
       output_data = {
           "file_name": "xxx.json",
           "file_tags": ["标签1", "标签2"],
           "results": results,
           "filtered_out_count": len(data_rows) - len(results)
       }
       
       with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
           json.dump(output_data, f, ensure_ascii=False, indent=2)
   
   if __name__ == '__main__':
       convert_file()
   ```

3. **执行转换**
   ```bash
   cd agent
   python convert_xxx.py
   ```

**已开发的定制化脚本**：

| 脚本 | 功能 | 特殊处理 |
|------|------|----------|
| `convert_social_org_nianjian.py` | 社会组织年检信息 | 年检结论映射（合格/基本合格/不合格/年报） |
| `convert_social_org_eval.py` | 社会组织评估等级 | 5A-1A级标签映射 |
| `convert_social_org_abnormal.py` | 社会组织活动异常 | 异常名录标签 |
| `convert_agriculture_base_v2.py` | 农业科技示范基地 | **处理Excel合并单元格** |
| `convert_yiliao_jigou.py` | 医疗机构信息 | 医院等级映射（三级甲等/二级无等...） |
| `convert_yibao_dingdian_yiliao.py` | 医保定点医疗机构 | 等级代码转文字（2→三级甲等） |
| `convert_nongye_chanpin_shengchan.py` | 农产品生产主体 | **多认证标签拆分**（有机/绿色/GAP） |
| `convert_fengtai_yingji_jiancha.py` | 应急管理局执法检查 | 检查结论分类（合格/不合格/复查合格） |
| `convert_zhengfu_caigou_hetong.py` | 政府采购合同 | **供应商名称提取** |

---

#### 路径三：批量通用转换（简单文件快速处理）

**适用场景**：
- 文件数量多但结构简单
- 字段命名规范统一
- 无需复杂逻辑，只需简单映射

**处理脚本**：`agent/batch_convert.py`

```bash
cd agent
python batch_convert.py
```

**工作原理**：
- 自动遍历 `dataset/非企业数据文件大json/` 目录
- 智能识别字段名（名称/代码/标签字段）
- 基于规则生成通用标签
- 自动过滤无效记录

**优点**：
- 无需为每个文件写脚本
- 适合快速处理大批量简单文件

---

### 三条路径的选择策略

| 文件特点 | 推荐路径 | 说明 |
|----------|----------|------|
| 结构简单、字段清晰 | 路径一：Gemini批处理 | 自动化程度高，无需编码 |
| 包含合并单元格/复杂Excel | 路径二：定制化脚本 | 需要特殊处理逻辑 |
| 需要多字段组合判断 | 路径二：定制化脚本 | 复杂标签生成规则 |
| 数据量超大（50万+） | 路径二：定制化脚本 | 避免API调用限制 |
| 字段规范、批量处理 | 路径三：批量通用 | 快速处理多个文件 |

### 核心提示词文件说明

**`agent/CodeGeneratePrompt.txt`**

该文件是整个非企业数据处理的核心指导文档，包含：

1. **目标群体过滤规则**
   - 保留：机关、事业单位、社会组织、医院、学校、合作社、国企
   - 排除：普通个人、私营企业（代码以9开头，除豁免外）
   - 豁免：合作社、公立医院、国有企业

2. **标签生成逻辑**
   - 基础标签：从文件名提取（如"示范基地"）
   - 细化标签：结合字段内容（如"三级甲等"+"定点医疗机构"）
   - 限制：单文件标签种类不超过6个

3. **输出格式要求**
   ```json
   {
     "file_name": "原始文件名.json",
     "file_tags": ["标签1", "标签2"],
     "results": [
       {
         "entity_name": "机构名称",
         "credit_code": "统一社会信用代码",
         "tag": "具体业务标签"
       }
     ],
     "filtered_out_count": 12
   }
   ```

4. **参考标签库**：244个标准标签定义

### 非企业数据标签体系（244个标签）

| 维度 | 标签数量 | 示例标签 |
|------|----------|----------|
| 社会组织管理 | 15+ | 5A级社会组织、年检合格、活动异常名录 |
| 医疗机构 | 40+ | 三级甲等定点医疗机构、定点零售药店 |
| 教育机构 | 10+ | A级幼儿园、市级示范幼儿园 |
| 农业与基地 | 30+ | 农业科技示范基地、有机农产品认证 |
| 政府监管 | 50+ | 行政处罚、行政检查合格、重点排污单位 |
| 荣誉与资质 | 40+ | 全国青年文明号、首都文明单位 |

完整标签列表见：`agent/非企业数据标签列表.txt`

### 最终产出

```
agent/output_results/
├── 北京市民政局-社会组织年检信息_result.json      (71,266条)
├── 北京市民政局-社会组织评估等级结果_result.json   (107,786条)
├── 市医保局-定点医疗机构信息_result.json           (4,418条)
├── ... (134+个文件)
└── 总计：361,844条机构记录

agent/非企业数据矩阵特征宽表.xlsx     (机构-标签特征矩阵)
agent/非企业数据标签列表.txt          (244个标签定义)
```

### 与企业数据的关联

非企业数据与企业数据可通过以下维度关联分析：
- **统一社会信用代码**：直接关联（部分机构有代码）
- **地址/区域**：地理空间关联
- **业务合作**：政府采购供应商、对口帮扶单位等
- **人员关联**：机构人员与企业任职关系

### 快速使用指南

```bash
cd agent

# 路径一：Gemini智能批处理（适合短上下文文件）
python gemini_batchThreadPoolExecutor.py \
    --input dataset/非企业数据文件大json/ \
    --prompt CodeGeneratePrompt.txt

# 路径二：定制化转换（针对复杂文件）
# 1. 查看文件结构
# 2. 参考CodeGeneratePrompt.txt编写convert_xxx.py
# 3. 执行
python convert_social_org_nianjian.py

# 路径三：批量通用转换（简单文件快速处理）
python batch_convert.py

# 查看结果
ls -lh output_results/
cat output_results/xxx_result.json | head -50
```
