import argparse
from pathlib import Path

import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
WORKSPACE_DIR = PROJECT_DIR / "output"


def categorize_dataset(dataset_name):
    """
    核心打标逻辑：根据数据集名称关键词，映射到细化后的风控维度。
    """
    dataset_name = str(dataset_name)

    rules = {
        "严重信用违约风险": {
            "keywords": ["失信", "严重违法", "欠税", "重大税收违法", "查封", "信用", "红黑名单"],
            "business_value": "准入底线：命中直接拒批或需总行特批",
        },
        "经营合规预警": {
            "keywords": [
                "处罚",
                "违法",
                "监督",
                "不正当竞争",
                "抽检",
                "不合格",
                "警示",
                "检查",
                "经营异常",
                "抽查",
                "违规",
                "双公示",
                "双随机",
                "依法",
                "执法",
            ],
            "business_value": "合规评估：反映企业日常管理精细度，影响信用评级及贷款定价",
        },
        "经济优质企业": {
            "keywords": ["上市", "新三板", "独角兽", "瞪羚"],
            "business_value": "极强增信：具备直接融资能力，流动性极高，属于战略白名单客户特征",
        },
        "科技与创新实力": {
            "keywords": ["高新", "专精特新", "小巨人", "科研", "科技型", "创新", "技术中心", "雏鹰", "科技研究"],
            "business_value": "核心增信：技术护城河深，符合“科技贷”等专项信贷政策，享利率优惠",
        },
        "政府表彰与荣誉": {
            "keywords": [
                "荣誉",
                "奖",
                "先进",
                "优秀创业项目",
                "优秀组织",
                "生态农场",
                "重点企业",
                "文明",
                "标杆",
                "百强",
                "12315绿色通道",
                "知识产权试点",
                "重点行业减排",
                "绿色食品",
                "头雁",
                "巾帼",
                "文化出口",
                "本市专利数据（企业）",
                "知识产权优势",
                "北京优农",
                "龙头企业",
                "示范",
            ],
            "business_value": "基础增信：软实力背书，证明企业社会信用良好",
        },
        "政策扶持与奖补": {
            "keywords": [
                "奖励",
                "拟支持",
                "新能源",
                "新材料",
                "新能源",
                "可再生",
                "资金",
                "补助",
                "贴息",
                "扶持",
                "免税",
                "优惠",
                "对口帮扶",
                "千人进千企",
                "试点企业",
                "大学生创业",
                "市政府重点工程",
            ],
            "business_value": "现金流补充：反映政府认可度，奖补资金可视为非营业性收入",
        },
    }

    core_risk_level = "待人工复核"
    tags = ["未分类"]

    for level, info in rules.items():
        matched_tags = [keyword for keyword in info["keywords"] if keyword in dataset_name]
        if matched_tags:
            core_risk_level = level
            tags = matched_tags
            break

    return pd.Series([core_risk_level, ", ".join(tags)])


def resolve_output_path(input_path, output_path):
    if output_path:
        return Path(output_path)
    return input_path.with_name(f"{input_path.stem}_分类结果{input_path.suffix}")


def main(input_file, output_file=None):
    input_path = Path(input_file)
    output_path = resolve_output_path(input_path, output_file)

    try:
        print(f"正在读取原始数据文件: {input_path} ...")
        df = pd.read_excel(input_path)
    except FileNotFoundError:
        print(f"❌ 未找到文件 '{input_path}'，请确认目录总表已经放入工作区。")
        return
    except Exception as exc:
        print(f"❌ 读取文件出错: {exc}")
        return

    if "数据集名称" not in df.columns:
        print("❌ 错误：输入文件中找不到名为 '数据集名称' 的列，请检查表头！")
        return

    print("正在进行分类打标...")
    df[["一级分类 (Core Risk Level)", "业务标签 (Tags)"]] = df["数据集名称"].apply(
        categorize_dataset
    )

    original_count = len(df)
    df = df[df["一级分类 (Core Risk Level)"] != "待人工复核"].copy()
    removed_count = original_count - len(df)

    try:
        df.to_excel(output_path, index=False)
        print("✅ 成功！未分类条目已删除，仅保留已命中分类的记录。")
        print(f"✅ 共删除未分类记录 {removed_count} 条，导出 {len(df)} 条。")
        print(f"✅ 导出文件路径: {output_path}")
    except Exception as exc:
        print(f"❌ 导出 Excel 文件失败: {exc}")


def parse_args():
    parser = argparse.ArgumentParser(description="根据数据集名称对北京开放数据目录做企业风控标签分类")
    parser.add_argument(
        "--input-file",
        default=str(WORKSPACE_DIR / "目录清单.xlsx"),
        help="待分类的目录总表路径",
    )
    parser.add_argument(
        "--output-file",
        default="",
        help="分类结果输出路径；不传时自动在输入文件旁生成 *_分类结果.xlsx",
    )
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    main(arguments.input_file, arguments.output_file or None)
