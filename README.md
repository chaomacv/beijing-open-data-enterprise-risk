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
