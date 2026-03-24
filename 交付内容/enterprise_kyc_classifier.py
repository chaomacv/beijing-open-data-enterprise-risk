import pandas as pd
import os

def categorize_dataset(dataset_name):
    """
    核心打标逻辑：根据数据集名称关键词，映射到细化后的风控维度
    """
    # 确保输入是字符串
    dataset_name = str(dataset_name)
    
    # 定义关键词字典（完全保持原样，未改动规则）
    rules = {
        "严重信用违约风险": {
            "keywords": ["失信", "严重违法", "欠税", "重大税收违法", "查封","信用","红黑名单"],
            "business_value": "准入底线：命中直接拒批或需总行特批"
        },
        "经营合规预警": {
            "keywords": ["处罚", "违法","监督","不正当竞争","抽检","不合格", "警示", "检查", "经营异常","抽查", "违规", "双公示", "双随机","依法","执法"],
            "business_value": "合规评估：反映企业日常管理精细度，影响信用评级及贷款定价"
        },
        # === 以下为拆分后的“增信”维度 ===
        "经济优质企业": {
            "keywords": ["上市", "新三板", "独角兽", "瞪羚"],
            "business_value": "极强增信：具备直接融资能力，流动性极高，属于战略白名单客户特征"
        },
        "科技与创新实力": {
            "keywords": ["高新", "专精特新", "小巨人","科研", "科技型", "创新", "技术中心", "雏鹰","科技研究"],
            "business_value": "核心增信：技术护城河深，符合“科技贷”等专项信贷政策，享利率优惠"
        },
        "政府表彰与荣誉": {
            "keywords": ["荣誉", "奖", "先进", "优秀创业项目","优秀组织","生态农场","重点企业","文明", "标杆", "百强","12315绿色通道","知识产权试点","重点行业减排","绿色食品","头雁","巾帼","文化出口","本市专利数据（企业）","知识产权优势","北京优农","龙头企业", "示范"],
            "business_value": "基础增信：软实力背书，证明企业社会信用良好"
        },
        # === 增信维度结束 ===
        "政策扶持与奖补": {
            "keywords": ["奖励", "拟支持", "新能源","新材料","新能源","可再生","资金", "补助", "贴息", "扶持", "免税", "优惠", "对口帮扶","千人进千企","试点企业","大学生创业","市政府重点工程"],
            "business_value": "现金流补充：反映政府认可度，奖补资金可视为非营业性收入"
        },
        # "实质经营与业务轨迹": {
        #     "keywords": ["合同", "中标", "许可", "备案", "验收", "缴费", "登记", "出让", "成交", "资质", "发证", "目录", "名录","项目审批"],
        #     "business_value": "真实性穿透：交叉验证企业是否正常经营、有真实订单和业务能力"
        # }
    }

    # 默认分类
    core_risk_level = "待人工复核"
    tags = ["未分类"]

    # 遍历规则进行匹配
    for level, info in rules.items():
        matched_tags = [kw for kw in info["keywords"] if kw in dataset_name]
        if matched_tags:
            core_risk_level = level
            tags = matched_tags
            break # 命中高优先级规则后跳出

    # 返回 Pandas Series 以便直接拼接到 DataFrame 的新列中，同时将 tags 列表转为逗号分隔的字符串
    return pd.Series([core_risk_level, ", ".join(tags)])

def main(input_file):
    # 1. 设置输入输出文件名
    # 假设你的原始数据存放在这个 Excel 文件中（如果你的数据是 csv，请改为 pd.read_csv('输入数据.csv')）
    # 使用 os.path.splitext 自动分离文件名和扩展名
    # file_name 会得到 'catalog_latest'，ext 会得到 '.xlsx'
    file_name, ext = os.path.splitext(input_file)
    
    # 拼接成规范的输出文件名：catalog_latest_分类结果.xlsx
    output_file = f"{file_name}_分类结果{ext}"

    # 2. 读取原始结构化数据
    try:
        print(f"正在读取原始数据文件: {input_file} ...")
        df = pd.read_excel(input_file)
    except FileNotFoundError:
        print(f"❌ 未找到文件 '{input_file}'，请确保原始数据表格放在同级目录下。")
        return
    except Exception as e:
         print(f"❌ 读取文件出错: {e}")
         return

    # 检查是否存在“数据集名称”这一列
    if '数据集名称' not in df.columns:
        print("❌ 错误：输入文件中找不到名为 '数据集名称' 的列，请检查表头！")
        return

    # 3. 核心打标操作
    print("正在进行分类打标...")
    # 使用 apply 函数，将 categorize_dataset 返回的两个值直接赋值给 DataFrame 的最后两列
    df[['一级分类 (Core Risk Level)', '业务标签 (Tags)']] = df['数据集名称'].apply(categorize_dataset)

    # 删除未分类条目，不再保留在导出结果中
    original_count = len(df)
    df = df[df['一级分类 (Core Risk Level)'] != '待人工复核'].copy()
    removed_count = original_count - len(df)

    # 4. 导出最终 Excel 文件
    try:
        df.to_excel(output_file, index=False)
        print("✅ 成功！未分类条目已删除，仅保留已命中分类的记录。")
        print(f"✅ 共删除未分类记录 {removed_count} 条，导出 {len(df)} 条。")
        print(f"✅ 导出文件路径: {output_file}")
    except Exception as e:
        print(f"❌ 导出 Excel 文件失败: {e}")

if __name__ == "__main__":
    input_file = '目录清单.xlsx'
    main(input_file)
