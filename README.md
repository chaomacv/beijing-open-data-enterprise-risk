# Beijing Open Data Enterprise Risk Pipeline

这个目录已经整理为一个可独立发布到 GitHub 的项目骨架，目标是基于北京市开放数据平台的数据集目录，筛选企业风控相关数据源，批量下载数据文件，并构建企业级风险特征宽表。

## 项目目标

项目核心流程包括：

1. 从北京市开放数据平台目录中筛选企业风控相关数据集
2. 对数据集进行规则分类与人工复核
3. 自动补充数据集更新时间和具体文件名
4. 批量下载公开数据文件
5. 从下载文件中抽取企业名称并构建企业画像宽表

这个仓库默认更偏向“代码与流程发布”，而不是“原始数据全集发布”。因此，大体量下载文件、缓存文件和中间结果默认会被 `.gitignore` 排除。

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

详细流程说明见 [交付内容/README.md](./交付内容/README.md)。

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
