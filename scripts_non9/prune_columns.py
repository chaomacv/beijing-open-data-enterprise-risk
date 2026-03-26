import argparse
from pathlib import Path

import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
WORKSPACE_DIR = PROJECT_DIR / "output"


def filter_columns(input_file, output_file):
    print(f"正在读取数据表: {input_file} ...")
    try:
        if str(input_file).endswith(".csv"):
            df = pd.read_csv(input_file, encoding="utf-8-sig")
        else:
            df = pd.read_excel(input_file)
    except Exception as exc:
        print(f"❌ 读取文件失败: {exc}")
        return

    columns_to_keep = [
        "序号",
        "数据集名称",
        "更新日期",
        "文章访问路径",
        "一级分类 (Core Risk Level)",
        "业务标签 (Tags)",
        "具体文件名称",
    ]

    missing_cols = [column for column in columns_to_keep if column not in df.columns]
    if missing_cols:
        print(f"❌ 错误：在原始表格中找不到以下列：{missing_cols}，请检查表头！")
        return

    print("正在剔除冗余字段...")
    pruned_df = df[columns_to_keep]

    print(f"正在导出精简版数据表: {output_file} ...")
    try:
        if str(output_file).endswith(".csv"):
            pruned_df.to_csv(output_file, index=False, encoding="utf-8-sig")
        else:
            pruned_df.to_excel(output_file, index=False)

        print("=" * 40)
        print("📊 字段精简完成：")
        print(f"  • 原始字段数: {len(df.columns)} 列")
        print(f"  • 精简后字段: {len(pruned_df.columns)} 列")
        print(f"🎉 最终文件已保存至: {output_file}")
        print("=" * 40)
    except Exception as exc:
        print(f"❌ 保存文件失败: {exc}")


def parse_args():
    parser = argparse.ArgumentParser(description="精简目录索引表，只保留画像构建所需的关键列")
    parser.add_argument(
        "--input-file",
        default=str(WORKSPACE_DIR / "目录清单_分类结果_人工过筛_更新时间_补充文件名.xlsx"),
        help="待精简的索引表路径",
    )
    parser.add_argument(
        "--output-file",
        default="",
        help="输出路径；不传时自动生成 *_精简列信息.xlsx",
    )
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    input_path = Path(arguments.input_file)
    output_path = (
        Path(arguments.output_file)
        if arguments.output_file
        else input_path.with_name(f"{input_path.stem}_精简列信息{input_path.suffix}")
    )
    filter_columns(str(input_path), str(output_path))
