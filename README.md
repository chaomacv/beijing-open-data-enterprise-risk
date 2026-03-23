# Beijing Open Data Enterprise Risk Pipeline

基于北京市公共数据开放平台的企业风控数据筛选、下载、标签化与画像构建流水线。

本项目的目标是从北京市公共数据开放平台（<https://data.beijing.gov.cn/>）的大规模公开数据集中，筛选出银行感兴趣的涉企信息，将原本以“数据集”为单位的开放数据，转化为以“企业”为中心、带有结构化标签的风险画像数据条目。

这个仓库默认更偏向“代码与流程发布”，而不是“原始数据全集发布”。因此，大体量下载文件、缓存文件和中间结果默认会被 `.gitignore` 排除。

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

这部分规则已经体现在 [enterprise_kyc_classifier.py](./交付内容/enterprise_kyc_classifier.py) 中。

## 工程化处理链路

从北京市开放数据平台下载的目录总表开始，整个工程链路如下：

1. `目录清单.xlsx`
2. `enterprise_kyc_classifier.py`
3. `目录清单_分类结果.xlsx`
4. 人工筛选与剔除不感兴趣内容
5. `目录清单_分类结果_人工过筛.xlsx`
6. `dataset_freshness_and_filename_updater.py`
7. `目录清单_分类结果_人工过筛_更新时间_补充文件名.xlsx`
8. `prune_columns.py`
9. `目录清单_分类结果_人工过筛_更新时间_补充文件名_精简列信息.xlsx`
10. `build_entity_profile_one_pass.py`
11. `特征矩阵风控模型宽表.xlsx`

更详细的脚本级流程见 [交付内容/README.md](./交付内容/README.md)。

## 最终产出

最终形成的结果包括：

- 以企业为中心的标签化数据条目
- 以标签为中心的企业命中结果
- 企业风险特征宽表
- 对应的 JSON 导出结果

其中公开仓库中默认只保留代码、文档和流程说明，不直接附带全量原始数据与中间产物。

## 当前结构

```text
bank/
├── README.md
├── .gitignore
├── pyproject.toml
├── requirements.txt
├── 交付内容/
│   ├── README.md
│   ├── enterprise_kyc_classifier.py
│   ├── dataset_freshness_and_filename_updater.py
│   ├── batch_downloader.py
│   ├── prune_columns.py
│   └── build_entity_profile_one_pass.py
├── 不规则文件/          # 本地数据文件，默认不提交
└── 缓存文件/            # 本地缓存与结果，默认不提交
```

其中：

- `交付内容/README.md` 是详细的数据处理流程文档
- `交付内容/*.py` 是核心处理脚本
- `不规则文件/`、`缓存文件/`、`交付内容/bank/` 默认作为本地工作目录，不建议直接上传 GitHub

## 核心脚本

- `交付内容/enterprise_kyc_classifier.py`
  从原始目录总表出发，对数据集名称做规则分类打标
- `交付内容/dataset_freshness_and_filename_updater.py`
  访问数据集详情页，补充更新时间与具体文件名称
- `交付内容/batch_downloader.py`
  手动扫码登录后批量触发数据下载
- `交付内容/prune_columns.py`
  保留画像构建需要的最小索引字段集
- `交付内容/build_entity_profile_one_pass.py`
  从下载数据中抽取企业名称并构建风控宽表

## 快速开始

### 1. 安装依赖

```bash
cd agent/bank
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. 运行处理流程

```bash
cd 交付内容

python enterprise_kyc_classifier.py

# 人工复核后生成：
# 目录清单_分类结果_人工过筛.xlsx

python dataset_freshness_and_filename_updater.py

python batch_downloader.py \
  --input 目录清单_分类结果_人工过筛_更新时间_补充文件名.xlsx \
  --download-dir bank

python build_entity_profile_one_pass.py \
  --index-file 目录清单_分类结果_人工过筛_更新时间_补充文件名_精简列信息.xlsx \
  --csv-dir bank \
  --output-file 特征矩阵风控模型宽表.xlsx
```

如果你需要先精简索引表，再运行最后一步，也可以插入：

```bash
python prune_columns.py
```

## GitHub 发布建议

默认推荐只提交以下内容：

- 顶层说明文件
- `交付内容/` 下的 Python 脚本
- `交付内容/README.md`

默认不提交以下内容：

- 下载得到的大体量 CSV/XLS/XLSX 文件
- 缓存目录和运行产物
- 本地浏览器下载目录
- 临时 Excel、JSON、日志和 Python 缓存

如果你确实想附带一个很小的样例文件，建议单独新建 `examples/` 目录，再按需放入示例数据。

## 推送到 GitHub

这个目录当前位于更大的工作区内部。为了避免受到父级 Git 工作区影响，更稳妥的做法是先复制到一个独立目录，再初始化仓库。

推荐方式：

```bash
cp -R /opt/data/private/xjx/RailMind/agent/bank ~/beijing-open-data-enterprise-risk
cd ~/beijing-open-data-enterprise-risk
git init
git add .
git commit -m "Initial commit: Beijing open data enterprise risk pipeline"
```

如果你确认要直接把当前目录当作独立仓库使用，也可以在 `agent/bank` 目录下执行：

```bash
cd /opt/data/private/xjx/RailMind/agent/bank
git init
git add .
git commit -m "Initial commit: Beijing open data enterprise risk pipeline"
```

然后关联 GitHub 远程仓库：

```bash
git branch -M main
git remote add origin https://github.com/chaomacv/beijing-open-data-enterprise-risk.git
git push -u origin main
```

如果你使用 GitHub CLI，也可以：

```bash
gh repo create beijing-open-data-enterprise-risk --private --source . --remote origin --push
```

## 注意事项

- 当前项目中的数据文件体量较大，直接上传 GitHub 很容易超限。
- 如果后续需要公开发布，建议进一步确认北京市开放数据平台相关数据的分发边界和引用方式。
- `batch_downloader.py` 依赖本地 Chrome 浏览器和可用的 ChromeDriver。
- 这个项目目前是“脚本型项目”，不是完整的 Python 包；`pyproject.toml` 主要用于项目元信息和依赖声明。
