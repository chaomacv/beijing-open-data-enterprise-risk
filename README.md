# Beijing Open Data Enterprise Risk Pipeline

基于北京市公共数据开放平台的企业风控数据筛选、下载、标签化与画像构建流水线。

这个项目已经完成了主体处理逻辑。当前仓库会同时保留核心脚本、数据样本、处理中间表和输出结果，方便直接整体同步到 GitHub。

## 项目目标

围绕北京市开放数据平台中的公开数据，构建面向银行业务的企业标签体系，用于：

- 贷前风控
- 企业经营与合规补充
- 精准获客与营销参考
- 科技金融与场景化产品建模

处理结果会把原本“以数据集为单位”的开放数据，转成“以企业为中心”的标签化记录与风控宽表。

## 核心流程

```text
目录清单.xlsx
  -> enterprise_kyc_classifier.py
目录清单_分类结果.xlsx
  -> 人工过筛
目录清单_分类结果_人工过筛.xlsx
  -> dataset_freshness_and_filename_updater.py
目录清单_分类结果_人工过筛_更新时间_补充文件名.xlsx
  -> prune_columns.py
目录清单_分类结果_人工过筛_更新时间_补充文件名_精简列信息.xlsx
  + bank/*.csv|*.xlsx
  -> build_entity_profile_one_pass.py
特征矩阵风控模型宽表.xlsx / json
```

详细说明见 [docs/pipeline.md](./docs/pipeline.md)。

## 仓库结构

```text
bank/
├── README.md
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
│   └── README.md
└── output/
    └── README.md
```

目录说明：

- `scripts/`：核心处理脚本，适合放在 GitHub 中长期维护。
- `docs/`：项目流程说明文档。
- `dataset/`：原始/样例数据目录。
- `output/`：处理输出目录，存放人工过筛表、中间产物和结果宽表。

## 快速开始

```bash
cd agent/bank
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

```bash
python scripts/enterprise_kyc_classifier.py

# 人工复核后生成：
# output/目录清单_分类结果_人工过筛.xlsx

python scripts/dataset_freshness_and_filename_updater.py
python scripts/prune_columns.py
python scripts/batch_downloader.py
python scripts/build_entity_profile_one_pass.py
```

默认情况下，脚本会把输入输出指向 `output/`。如果你想改路径，可以通过各脚本的命令行参数覆盖。

## 当前输出形态

项目最终可形成以下结果：

- 企业级标签化命中记录
- 企业风控特征宽表
- 未匹配文件清单、补救处理记录、辅助 JSON 导出

当前仓库包含：

- 分类后的目录索引表
- 数据样本和下载文件
- 结果宽表与辅助 JSON
- 核心处理脚本和流程文档
