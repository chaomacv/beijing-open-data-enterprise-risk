# 北京市开放数据平台企业风控数据加工说明

本文档用于说明 `/opt/data/private/xjx/RailMind/agent/bank/交付内容` 目录下这批脚本的处理链路、输入输出关系和推荐执行顺序。

这套流程的起点是从北京市开放数据平台下载的 [目录清单.xlsx](/opt/data/private/xjx/RailMind/agent/bank/交付内容/目录清单.xlsx)，目标是从公开数据集中筛出与企业风控相关的数据源，批量下载明细文件，并进一步构建企业级风控特征宽表。

## 目录概览

- [目录清单.xlsx](/opt/data/private/xjx/RailMind/agent/bank/交付内容/目录清单.xlsx)：原始目录总表，来自北京市开放数据平台。
- [enterprise_kyc_classifier.py](/opt/data/private/xjx/RailMind/agent/bank/交付内容/enterprise_kyc_classifier.py)：按数据集名称做规则分类打标。
- [目录清单_分类结果.xlsx](/opt/data/private/xjx/RailMind/agent/bank/交付内容/目录清单_分类结果.xlsx)：自动分类结果。
- [目录清单_分类结果_人工过筛.xlsx](/opt/data/private/xjx/RailMind/agent/bank/交付内容/目录清单_分类结果_人工过筛.xlsx)：在自动分类结果基础上人工筛选后的版本。
- [dataset_freshness_and_filename_updater.py](/opt/data/private/xjx/RailMind/agent/bank/交付内容/dataset_freshness_and_filename_updater.py)：补充每条数据集的最新更新时间和具体文件名称。
- [batch_downloader.py](/opt/data/private/xjx/RailMind/agent/bank/交付内容/batch_downloader.py)：微信扫码登录后批量下载数据文件。
- [prune_columns.py](/opt/data/private/xjx/RailMind/agent/bank/交付内容/prune_columns.py)：保留后续建模需要的核心字段。
- [build_entity_profile_one_pass.py](/opt/data/private/xjx/RailMind/agent/bank/交付内容/build_entity_profile_one_pass.py)：从下载后的 CSV/XLS/XLSX 中提取企业名称，构建企业画像宽表。
- [bank](/opt/data/private/xjx/RailMind/agent/bank/交付内容/bank)：已下载的数据文件目录，供后续实体抽取使用。

## 整体流程

推荐按照下面顺序执行：

1. 原始目录下载
2. 自动分类打标
3. 人工过筛
4. 补充更新时间与具体文件名
5. 批量下载数据文件
6. 精简索引字段
7. 构建企业风控特征宽表

流程示意如下：

```text
目录清单.xlsx
  -> enterprise_kyc_classifier.py
目录清单_分类结果.xlsx
  -> 人工过筛
目录清单_分类结果_人工过筛.xlsx
  -> dataset_freshness_and_filename_updater.py
目录清单_分类结果_人工过筛_更新时间_补充文件名.xlsx
  -> batch_downloader.py
bank/*.csv|*.xlsx

目录清单_分类结果_人工过筛_更新时间_补充文件名.xlsx
  -> prune_columns.py
目录清单_分类结果_人工过筛_更新时间_补充文件名_精简列信息.xlsx
  -> build_entity_profile_one_pass.py

bank/*.csv|*.xlsx
  + 精简索引表
  -> 特征矩阵风控模型宽表.xlsx / .json
```

## 分步说明

### 1. `enterprise_kyc_classifier.py`

作用：

- 读取 [目录清单.xlsx](/opt/data/private/xjx/RailMind/agent/bank/交付内容/目录清单.xlsx)
- 根据 `数据集名称` 的关键词规则进行一级分类和业务标签打标
- 删除未命中规则、仍为“待人工复核”的记录
- 输出分类结果文件

默认输入输出：

- 输入：`目录清单.xlsx`
- 输出：`目录清单_分类结果.xlsx`

执行方式：

```bash
cd /opt/data/private/xjx/RailMind/agent/bank/交付内容
python enterprise_kyc_classifier.py
```

输出中新增的关键列：

- `一级分类 (Core Risk Level)`
- `业务标签 (Tags)`

当前脚本的一级分类主要包括：

- 严重信用违约风险
- 经营合规预警
- 经济优质企业
- 科技与创新实力
- 政府表彰与荣誉
- 政策扶持与奖补

### 2. 人工过筛

作用：

- 对 [目录清单_分类结果.xlsx](/opt/data/private/xjx/RailMind/agent/bank/交付内容/目录清单_分类结果.xlsx) 做人工复核
- 去掉虽然命中关键词，但业务上不需要继续保留的数据集
- 形成后续抓取和下载的候选清单

人工产物：

- [目录清单_分类结果_人工过筛.xlsx](/opt/data/private/xjx/RailMind/agent/bank/交付内容/目录清单_分类结果_人工过筛.xlsx)

这一环节不是脚本自动生成的，但它是后续流程的实际输入。

### 3. `dataset_freshness_and_filename_updater.py`

作用：

- 逐条访问 `文章访问路径`
- 尝试从详情页中提取最新 `更新日期`
- 尝试识别实际下载文件名，写入 `具体文件名称`
- 无法识别具体文件名的行会被删除

默认输入输出：

- 输入：`目录清单_分类结果_人工过筛.xlsx`
- 输出：`目录清单_分类结果_人工过筛_更新时间_补充文件名.xlsx`

执行方式：

```bash
cd /opt/data/private/xjx/RailMind/agent/bank/交付内容
python dataset_freshness_and_filename_updater.py
```

说明：

- 该脚本依赖 Selenium 和 Chrome 浏览器。
- 如果页面中抓不到新的更新时间，脚本会保留原值，并在前面加上 `旧` 标记。
- 该脚本会新增或补全 `具体文件名称` 列。

### 4. `batch_downloader.py`

作用：

- 打开北京市开放数据平台
- 手动微信扫码登录
- 逐条进入数据集页面并触发下载
- 将未能成功触发下载的记录写入 `un_downloaded_records.csv`

推荐执行方式：

```bash
cd /opt/data/private/xjx/RailMind/agent/bank/交付内容
python batch_downloader.py \
  --input 目录清单_分类结果_人工过筛_更新时间_补充文件名.xlsx \
  --download-dir bank
```

说明：

- 脚本默认下载目录是 `downloads/`，但当前目录下后续流程使用的是 [bank](/opt/data/private/xjx/RailMind/agent/bank/交付内容/bank)，因此建议显式传 `--download-dir bank`。
- 下载前需要人工在浏览器里完成微信扫码登录。
- 只会处理 `具体文件名称` 不为空的记录。

### 5. `prune_columns.py`

作用：

- 从更新后的目录总表中保留后续建模真正需要的核心列
- 便于人工查看，也便于把索引表喂给画像构建脚本

建议保留的列：

- `序号`
- `数据集名称`
- `更新日期`
- `文章访问路径`
- `一级分类 (Core Risk Level)`
- `业务标签 (Tags)`
- `具体文件名称`

注意：

- 当前脚本文件内的默认 `INPUT_FILE` 写的是 `目录清单_分类结果.xlsx`。
- 如果要接在本流程里使用，建议先把 [prune_columns.py](/opt/data/private/xjx/RailMind/agent/bank/交付内容/prune_columns.py) 中的 `INPUT_FILE` 改成 `目录清单_分类结果_人工过筛_更新时间_补充文件名.xlsx`，再运行脚本。

推荐输出文件名：

- `目录清单_分类结果_人工过筛_更新时间_补充文件名_精简列信息.xlsx`

执行方式：

```bash
cd /opt/data/private/xjx/RailMind/agent/bank/交付内容
python prune_columns.py
```

### 6. `build_entity_profile_one_pass.py`

作用：

- 读取目录索引表中的 `具体文件名称`、`业务标签 (Tags)`、`一级分类 (Core Risk Level)`、`更新日期` 等信息
- 到 `bank/` 目录中读取对应下载文件
- 自动尝试识别企业名称列
- 将命中的标签映射为 one-hot 特征
- 聚合到企业粒度，输出企业风控画像宽表

建议执行方式：

```bash
cd /opt/data/private/xjx/RailMind/agent/bank/交付内容
python build_entity_profile_one_pass.py \
  --index-file 目录清单_分类结果_人工过筛_更新时间_补充文件名_精简列信息.xlsx \
  --csv-dir bank \
  --output-file 特征矩阵风控模型宽表.xlsx
```

主要输出：

- `特征矩阵风控模型宽表.xlsx`
- `特征矩阵风控模型宽表.json`
- `未匹配文件列表.json`
- `仍然未匹配文件_v2.json`
- `补充处理成功文件_v2.json`

输出宽表的核心字段包括：

- `更新日期`
- `企业名称`
- `一级分类`
- 多个 one-hot 风控特征列
- `数据源`

脚本会优先尝试精确匹配企业名称列，失败后再进行补救式模糊匹配；也会兼容多种编码、分隔符和表头行位置。

## 依赖环境

建议至少准备以下 Python 依赖：

```bash
pip install pandas beautifulsoup4 selenium openpyxl xlrd
```

另外还需要：

- 本机可用的 Chrome 浏览器
- 与浏览器匹配的 ChromeDriver

## 关键衔接点

这个目录里的真实处理链路有几个衔接点需要特别注意：

- `目录清单_分类结果.xlsx` 和 `目录清单_分类结果_人工过筛.xlsx` 之间存在人工筛选步骤。
- `batch_downloader.py` 建议显式传入 `--input 目录清单_分类结果_人工过筛_更新时间_补充文件名.xlsx`，否则默认文件名对不上人工过筛版本。
- `batch_downloader.py` 建议显式传入 `--download-dir bank`，这样下载结果能直接接到后续企业画像流程。
- `prune_columns.py` 当前默认输入文件名没有跟到最新链路，需要在脚本里改成补充文件名后的版本再运行。
- `build_entity_profile_one_pass.py` 虽然默认读取 `目录清单_分类结果.xlsx`，但更推荐显式传 `--index-file` 指向精简后的索引表。

## 推荐的一次性执行顺序

```bash
cd /opt/data/private/xjx/RailMind/agent/bank/交付内容

python enterprise_kyc_classifier.py

# 人工复核并另存为：
# 目录清单_分类结果_人工过筛.xlsx

python dataset_freshness_and_filename_updater.py

python batch_downloader.py \
  --input 目录清单_分类结果_人工过筛_更新时间_补充文件名.xlsx \
  --download-dir bank

# 将 prune_columns.py 里的 INPUT_FILE 改为：
# 目录清单_分类结果_人工过筛_更新时间_补充文件名.xlsx
python prune_columns.py

python build_entity_profile_one_pass.py \
  --index-file 目录清单_分类结果_人工过筛_更新时间_补充文件名_精简列信息.xlsx \
  --csv-dir bank \
  --output-file 特征矩阵风控模型宽表.xlsx
```

## 产出物总结

按推荐流程执行后，关键产物如下：

- 目录筛选表：`目录清单_分类结果.xlsx`
- 人工复核表：`目录清单_分类结果_人工过筛.xlsx`
- 补充下载信息后的索引表：`目录清单_分类结果_人工过筛_更新时间_补充文件名.xlsx`
- 精简索引表：`目录清单_分类结果_人工过筛_更新时间_补充文件名_精简列信息.xlsx`
- 下载的数据文件目录：[bank](/opt/data/private/xjx/RailMind/agent/bank/交付内容/bank)
- 企业风控宽表：`特征矩阵风控模型宽表.xlsx`
- 宽表 JSON：`特征矩阵风控模型宽表.json`
