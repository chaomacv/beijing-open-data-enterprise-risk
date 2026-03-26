import argparse
from pathlib import Path

import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
WORKSPACE_DIR = PROJECT_DIR / "output"


def categorize_dataset(dataset_name):
    """
    核心打标逻辑：根据数据集名称关键词，映射到目录总表所需的一级分类与业务标签。
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
        "资质与准入壁垒": {
            "keywords": ["备案", "核准", "许可", "登记凭证", "特种设备检验", "检验检测", "资质"],
            "business_value": "准入门槛：反映机构合法执业资格、检验检测能力与行业进入壁垒",
        },
        "政府采购与公共服务收入": {
            "keywords": ["政府购买服务", "采购合同", "中标", "承储企业"],
            "business_value": "收入稳定性：反映机构具备政府采购或公共服务供给能力",
        },
        "医保结算与财政支持": {
            "keywords": ["医保", "定点", "新农合", "救助款", "经费", "拨款"],
            "business_value": "支付保障：体现医保结算资格或财政性资金支持来源",
        },
        "官方评级与服务评估": {
            "keywords": ["评估等级", "星级", "绩效比较", "办园质量督导", "等级医院"],
            "business_value": "官方背书：体现主管部门对机构服务质量或运营水平的正式评价",
        },
        "民生保障与社会服务": {
            "keywords": ["养老机构", "福利机构", "康复服务机构"],
            "business_value": "特殊客群识别：指向承担养老、福利、康复等民生保障职责的机构",
        },
        "社会组织与非营利团体": {
            "keywords": ["社会团体", "基金会", "民办非企业"],
            "business_value": "主体识别：指向民政登记的社会组织与非营利法人",
        },
        "社会组织合规风险": {
            "keywords": ["年检", "活动异常名录", "撤销", "吊销"],
            "business_value": "风险过滤：用于识别年检异常、活动异常及资格撤销吊销等负面状态",
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

    matched_levels = []
    matched_tags = []
    for level, info in rules.items():
        current_tags = [keyword for keyword in info["keywords"] if keyword in dataset_name]
        if current_tags:
            matched_levels.append(level)
            matched_tags.extend(current_tags)

    if matched_levels:
        core_risk_level = "，".join(dict.fromkeys(matched_levels))
        tags = list(dict.fromkeys(matched_tags))

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
