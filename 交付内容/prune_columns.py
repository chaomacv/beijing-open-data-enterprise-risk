import pandas as pd
import os
def filter_columns(input_file, output_file):
    print(f"正在读取数据表: {input_file} ...")
    try:
        if input_file.endswith('.csv'):
            df = pd.read_csv(input_file, encoding='utf-8-sig')
        else:
            df = pd.read_excel(input_file)
    except Exception as e:
        print(f"❌ 读取文件失败: {e}")
        return

    # 明确定义我们要保留的核心目标列
    columns_to_keep = [
        "序号", 
        "数据集名称", 
        "更新日期", 
        "文章访问路径", 
        "一级分类 (Core Risk Level)", 
        "业务标签 (Tags)", 
        "具体文件名称"
    ]

    # 防错机制：检查我们想要的列是不是都在表里
    missing_cols = [col for col in columns_to_keep if col not in df.columns]
    if missing_cols:
        print(f"❌ 错误：在原始表格中找不到以下列：{missing_cols}，请检查表头！")
        return

    print("正在剔除冗余字段...")
    # 核心过滤逻辑：直接通过列表切片保留所需列
    pruned_df = df[columns_to_keep]

    print(f"正在导出精简版数据表: {output_file} ...")
    try:
        if output_file.endswith('.csv'):
            pruned_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        else:
            pruned_df.to_excel(output_file, index=False)
            
        print("=" * 40)
        print("📊 字段精简完成：")
        print(f"  • 原始字段数: {len(df.columns)} 列")
        print(f"  • 精简后字段: {len(pruned_df.columns)} 列")
        print(f"🎉 最终文件已保存至: {output_file}")
        print("=" * 40)
        
    except Exception as e:
        print(f"❌ 保存文件失败: {e}")

if __name__ == "__main__":
    # 配置你的文件路径
    # 这里建议填入你刚跑完爬虫的那份最终数据表
    INPUT_FILE = "目录清单_分类结果.xlsx"   
    file_name, ext = os.path.splitext(INPUT_FILE)
    
    # 拼接成规范的输出文件名：catalog_latest_分类结果.xlsx
    OUTPUT_FILE = f"{file_name}_精简列信息{ext}"
    filter_columns(INPUT_FILE, OUTPUT_FILE)