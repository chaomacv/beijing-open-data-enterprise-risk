#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将 CSV、XLSX 等表格文件转换为 input_json 格式的 JSON 文件

目标格式：
{
  "source_file": "原始文件名.csv",
  "total_rows": 100,
  "columns": ["列名1", "列名2", ...],
  "data": [
    {"列名1": "值1", "列名2": "值2"},
    ...
  ]
}

使用方法：
  python convert_table_to_json.py <输入文件路径> [输出文件路径]
  
示例：
  python convert_table_to_json.py /path/to/data.xlsx
  python convert_table_to_json.py /path/to/data.csv /path/to/output.json
"""

import pandas as pd
import json
import os
import sys
from pathlib import Path


def convert_table_to_json(input_file, output_file=None):
    """
    将表格文件转换为标准JSON格式
    
    Args:
        input_file: 输入文件路径（支持 .csv, .xlsx, .xls）
        output_file: 输出文件路径（可选，默认保存到 input_json 目录）
    """
    input_path = Path(input_file)
    
    if not input_path.exists():
        print(f"错误：文件不存在 {input_file}")
        return False
    
    # 获取文件扩展名
    ext = input_path.suffix.lower()
    
    # 根据扩展名读取文件
    try:
        if ext in ['.xlsx', '.xls']:
            df = pd.read_excel(input_file)
            source_file = input_path.name
        elif ext == '.csv':
            # 尝试不同编码
            encodings = ['utf-8', 'gbk', 'gb2312', 'latin1']
            for encoding in encodings:
                try:
                    df = pd.read_csv(input_file, encoding=encoding)
                    source_file = input_path.name
                    break
                except UnicodeDecodeError:
                    continue
            else:
                # 如果都失败，尝试用Excel方式读取（有些.csv实际是Excel格式）
                try:
                    df = pd.read_excel(input_file)
                    source_file = input_path.name
                except Exception as e:
                    print(f"错误：无法读取CSV文件 {e}")
                    return False
        else:
            print(f"错误：不支持的文件格式 {ext}，支持的格式：.csv, .xlsx, .xls")
            return False
    except Exception as e:
        print(f"错误：读取文件失败 {e}")
        return False
    
    # 清理数据：将 NaN 转为 None，将 numpy 类型转为 Python 原生类型
    df = df.where(pd.notna(df), None)
    
    # 获取列名
    columns = df.columns.tolist()
    
    # 转换数据为字典列表
    data = []
    for _, row in df.iterrows():
        row_dict = {}
        for col in columns:
            val = row[col]
            # 转换值为可JSON序列化的类型
            if val is None or (isinstance(val, float) and pd.isna(val)):
                row_dict[col] = None
            elif isinstance(val, (int, float)):
                row_dict[col] = val
            else:
                row_dict[col] = str(val) if val is not None else None
        data.append(row_dict)
    
    # 构建输出数据结构
    output_data = {
        "source_file": source_file,
        "total_rows": len(data),
        "columns": columns,
        "data": data
    }
    
    # 确定输出路径
    if output_file is None:
        # 默认保存到 input_json 目录，文件名使用.json后缀
        script_dir = Path(__file__).parent
        output_dir = script_dir / "input_json"
        output_dir.mkdir(exist_ok=True)
        output_file = output_dir / (input_path.stem + ".json")
    else:
        output_file = Path(output_file)
        output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # 写入JSON文件
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"转换成功！")
    print(f"  输入文件: {input_file}")
    print(f"  输出文件: {output_file}")
    print(f"  总行数: {len(data)}")
    print(f"  列数: {len(columns)}")
    print(f"  列名: {columns}")
    
    return True


def batch_convert(directory, pattern='*'):
    """
    批量转换目录下的所有表格文件
    
    Args:
        directory: 输入目录
        pattern: 文件匹配模式，如 '*.csv' 或 '*.xlsx'
    """
    dir_path = Path(directory)
    
    # 支持的文件扩展名
    extensions = ['.csv', '.xlsx', '.xls']
    
    files = []
    for ext in extensions:
        files.extend(dir_path.glob(f"*{ext}"))
    
    if not files:
        print(f"在 {directory} 中未找到表格文件")
        return
    
    print(f"找到 {len(files)} 个文件待转换\n")
    
    success = 0
    failed = 0
    
    for i, file_path in enumerate(files, 1):
        print(f"{i}. 处理: {file_path.name}")
        if convert_table_to_json(str(file_path)):
            success += 1
        else:
            failed += 1
        print()
    
    print(f"批量转换完成: 成功 {success}, 失败 {failed}, 总计 {len(files)}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='将 CSV/XLSX 表格文件转换为 JSON 格式',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  python convert_table_to_json.py data.xlsx
  python convert_table_to_json.py data.csv -o output.json
  python convert_table_to_json.py --batch /path/to/directory
        '''
    )
    
    parser.add_argument('input', nargs='?', help='输入文件路径')
    parser.add_argument('-o', '--output', help='输出文件路径（可选）')
    parser.add_argument('--batch', metavar='DIR', help='批量转换目录下的所有表格文件')
    
    args = parser.parse_args()
    
    if args.batch:
        batch_convert(args.batch)
    elif args.input:
        convert_table_to_json(args.input, args.output)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
