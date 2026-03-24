# 项目处理链路

本文档说明 `agent/bank` 项目的脚本链路、输入输出关系和推荐执行顺序。

当前仓库采用“代码、数据和输出结果统一入库”的组织方式：

- 核心脚本在 `scripts/`
- 真实运行产物默认放在 `output/`
- 原始开放数据或样例数据默认放在 `dataset/`

## 目录说明

- `scripts/enterprise_kyc_classifier.py`：按数据集名称做规则分类打标。
- `scripts/dataset_freshness_and_filename_updater.py`：补充数据集最新更新时间和实际文件名。
- `scripts/batch_downloader.py`：扫码登录后批量下载数据文件。
- `scripts/prune_columns.py`：从索引表中保留后续画像构建所需的关键列。
- `scripts/build_entity_profile_one_pass.py`：从下载文件中抽取企业名称并构建风控宽表。
- `output/`：默认运行工作区和输出目录。

## 推荐执行顺序

```text
output/目录清单.xlsx
  -> scripts/enterprise_kyc_classifier.py
output/目录清单_分类结果.xlsx
  -> 人工过筛
output/目录清单_分类结果_人工过筛.xlsx
  -> scripts/dataset_freshness_and_filename_updater.py
output/目录清单_分类结果_人工过筛_更新时间_补充文件名.xlsx
  -> scripts/prune_columns.py
output/目录清单_分类结果_人工过筛_更新时间_补充文件名_精简列信息.xlsx
  + output/bank/*.csv|*.xlsx
  -> scripts/build_entity_profile_one_pass.py
output/特征矩阵风控模型宽表.xlsx
```

## 各脚本说明

### 1. `enterprise_kyc_classifier.py`

作用：

- 读取 `output/目录清单.xlsx`
- 根据 `数据集名称` 关键词进行一级分类和业务标签打标
- 输出 `output/目录清单_分类结果.xlsx`

运行示例：

```bash
python scripts/enterprise_kyc_classifier.py
```

支持参数：

```bash
python scripts/enterprise_kyc_classifier.py \
  --input-file output/目录清单.xlsx \
  --output-file output/目录清单_分类结果.xlsx
```

### 2. 人工过筛

作用：

- 对自动分类结果做业务复核
- 删除虽然命中关键词但价值不高的数据集
- 形成后续抓取和下载的候选清单

人工产物：

- `output/目录清单_分类结果_人工过筛.xlsx`

### 3. `dataset_freshness_and_filename_updater.py`

作用：

- 逐条访问 `文章访问路径`
- 提取最新 `更新日期`
- 提取实际下载文件名，写入 `具体文件名称`
- 删除无法识别实际文件名的记录

运行示例：

```bash
python scripts/dataset_freshness_and_filename_updater.py
```

支持参数：

```bash
python scripts/dataset_freshness_and_filename_updater.py \
  --input-file output/目录清单_分类结果_人工过筛.xlsx \
  --output-file output/目录清单_分类结果_人工过筛_更新时间_补充文件名.xlsx
```

说明：

- 依赖 Selenium、Chrome 和匹配版本的 ChromeDriver。
- 如果页面抓不到新的更新时间，会保留原值并加上 `旧` 前缀。

### 4. `prune_columns.py`

作用：

- 从最新索引表中保留画像构建需要的核心字段
- 生成更干净的下游输入表

默认保留列：

- `序号`
- `数据集名称`
- `更新日期`
- `文章访问路径`
- `一级分类 (Core Risk Level)`
- `业务标签 (Tags)`
- `具体文件名称`

运行示例：

```bash
python scripts/prune_columns.py
```

默认输入已对齐到：

- `output/目录清单_分类结果_人工过筛_更新时间_补充文件名.xlsx`

### 5. `batch_downloader.py`

作用：

- 打开北京市开放数据平台
- 人工微信扫码登录
- 逐条进入数据集页面并触发下载
- 将未能成功下载的记录写入 `un_downloaded_records.csv`

运行示例：

```bash
python scripts/batch_downloader.py
```

默认情况下：

- 输入索引表使用 `output/目录清单_分类结果_人工过筛_更新时间_补充文件名.xlsx`
- 下载目录使用 `output/bank/`

### 6. `build_entity_profile_one_pass.py`

作用：

- 读取精简后的索引表
- 到 `output/bank/` 中寻找对应下载文件
- 自动识别企业名称列
- 将命中的标签映射为 one-hot 特征
- 聚合成企业风控画像宽表

运行示例：

```bash
python scripts/build_entity_profile_one_pass.py
```

默认输入输出：

- 索引表：`output/目录清单_分类结果_人工过筛_更新时间_补充文件名_精简列信息.xlsx`
- 数据目录：`output/bank/`
- 输出文件：`output/特征矩阵风控模型宽表.xlsx`

同时还会生成：

- `output/未匹配文件列表.json`
- `output/补充处理成功文件_v2.json`
- `output/仅记录文件名_信用红黑名单.json`
- `output/手动处理文件.xlsx`

## 依赖环境

```bash
pip install -r requirements.txt
```

另外还需要：

- Chrome 浏览器
- 与浏览器匹配的 ChromeDriver

## 维护建议

- `scripts/` 保持为通用、可复用的处理脚本。
- `output/` 记录阶段性产物和最终结果，便于直接回溯。
- 如果后续还要补充 GitHub 展示材料，优先往 `docs/` 放流程图和说明截图。
