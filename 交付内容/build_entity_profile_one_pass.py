import argparse
import json
import os
import re
import shutil
import tempfile
from collections import defaultdict

import pandas as pd


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

HEADER_ROWS = [0, 1, 2, 3, 4, 5]
CSV_ENCODINGS = ["utf-8-sig", "utf-8", "gbk", "gb18030", "gb2312", "latin-1", "cp1252"]
EXCEL_ENGINES = ["openpyxl", "xlrd"]
ILLEGAL_EXCEL_CHARACTERS = re.compile(r"[\x00-\x08\x0B-\x0C\x0E-\x1F]")

# 按优先级排序。primary 阶段只用 exact，supplemental 阶段会继续尝试 contains / fallback。
COMPANY_COLUMN_NAMES = [
    "申报主体",
    "企业名称",
    "被处罚单位名称",
    "申报单位",
    "单位名称",
    "实施单位",
    "依托单位",
    "申报单位名称",
    "处罚机构名称",
    "行政相对人名称",
    "北京市企业技术中心所在企业名称",
    "国家企业技术中心所在企业名称",
    "机构名称",
    "被抽样销售者",
    "名称",
    "建设单位",
    "合作社/家庭农场名称",
    "获得荣誉单位名称",
    "ORG_NAME",
    "权利人名称",
    "标题",
    "证券简称",
    "法人单位名称",
    "公司全称",
    "相关企业",
    "企业名称*",
    "纳税人名称",
    "公司名称",
    "项目名称",
    "案件名称",
    "主体名称",
]

TAG_MAPPING = {
    "失信": "失信",
    "严重违法": "严重违法",
    "查封": "查封",
    "欠税": "税务问题",
    "重大税收违法": "税务问题",
    "处罚": "处罚",
    "违法": "违法",
    "不正当竞争": "不正当竞争",
    "不合格": "产品抽检不合格",
    "警示": "警示",
    "经营异常": "经营异常",
    "违规": "违规",
    "上市": "上市",
    "新三板": "新三板",
    "独角兽": "独角兽",
    "瞪羚": "瞪羚",
    "高新": "高新",
    "专精特新": "专精特新",
    "小巨人": "小巨人",
    "创新": "创新",
    "技术中心": "技术中心",
    "雏鹰": "雏鹰",
    "科研": "科技研究型",
    "科技型": "科技研究型",
    "科技研究": "科技研究型",
    "优秀创业项目": "优秀创业项目",
    "重点企业": "重点企业",
    "标杆": "标杆",
    "百强": "百强",
    "重点行业减排": "重点行业减排",
    "本市专利数据（企业）": "本市专利数据（企业）",
    "龙头企业": "龙头企业",
    "荣誉": "评优评先及获奖企业",
    "奖": "评优评先及获奖企业",
    "先进": "评优评先及获奖企业",
    "优秀组织": "评优评先及获奖企业",
    "生态农场": "评优评先及获奖企业",
    "文明": "评优评先及获奖企业",
    "12315绿色通道": "评优评先及获奖企业",
    "绿色食品": "评优评先及获奖企业",
    "头雁": "评优评先及获奖企业",
    "巾帼": "评优评先及获奖企业",
    "文化出口": "评优评先及获奖企业",
    "北京优农": "评优评先及获奖企业",
    "示范": "评优评先及获奖企业",
    "知识产权试点": "知识产权优势企业",
    "知识产权优势": "知识产权优势企业",
    "奖励": "奖励",
    "拟支持": "拟支持",
    "新能源": "新能源",
    "新材料": "新材料",
    "可再生": "可再生",
    "资金": "资金",
    "补助": "补助",
    "贴息": "贴息",
    "扶持": "扶持",
    "免税": "免税",
    "优惠": "优惠",
    "对口帮扶": "对口帮扶",
    "千人进千企": "千人进千企",
    "试点企业": "试点企业",
    "大学生创业": "大学生创业",
    "市政府重点工程": "市政府重点工程",
}


def detect_file_format(file_path):
    try:
        with open(file_path, "rb") as file_obj:
            header = file_obj.read(8)
        if header.startswith(b"\xd0\xcf\x11\xe0"):
            return "xls"
        if header.startswith(b"PK\x03\x04"):
            return "xlsx"
        return "csv"
    except Exception:
        return "csv"


def detect_csv_separator(file_path, encoding):
    try:
        with open(file_path, "r", encoding=encoding, errors="ignore") as file_obj:
            first_lines = [file_obj.readline() for _ in range(3)]
    except Exception:
        return ","

    separator_counts = {}
    for separator in [",", "\t", ";", "|"]:
        counts = [line.count(separator) for line in first_lines if line.strip()]
        if counts and min(counts) > 0 and max(counts) == min(counts):
            separator_counts[separator] = min(counts)

    if separator_counts:
        return max(separator_counts, key=separator_counts.get)
    return ","


def read_excel_candidate(file_path, engine, header_row):
    kwargs = {"dtype": str, "engine": engine}
    if header_row == 0:
        return pd.read_excel(file_path, **kwargs)
    return pd.read_excel(file_path, header=header_row, **kwargs)


def read_csv_candidate(file_path, encoding, header_row):
    separator = detect_csv_separator(file_path, encoding)
    kwargs = {
        "encoding": encoding,
        "dtype": str,
        "sep": separator,
        "on_bad_lines": "skip",
        "low_memory": False,
        "skipinitialspace": True,
    }
    if header_row == 0:
        return pd.read_csv(file_path, **kwargs)
    return pd.read_csv(file_path, header=header_row, **kwargs)


def build_read_attempts(file_path):
    detected_format = detect_file_format(file_path)
    attempts = []
    seen = set()

    def add_attempt(kind, header_row, engine=None, encoding=None, temp_suffix=None):
        key = (kind, header_row, engine, encoding, temp_suffix)
        if key in seen:
            return
        seen.add(key)
        attempts.append(
            {
                "kind": kind,
                "header_row": header_row,
                "engine": engine,
                "encoding": encoding,
                "temp_suffix": temp_suffix,
            }
        )

    if detected_format in {"xlsx", "xls"}:
        for header_row in HEADER_ROWS:
            for engine in EXCEL_ENGINES:
                add_attempt("excel", header_row, engine=engine)

    for header_row in HEADER_ROWS:
        for encoding in CSV_ENCODINGS:
            add_attempt("csv", header_row, encoding=encoding)

    if detected_format == "csv":
        for header_row in HEADER_ROWS:
            for engine in EXCEL_ENGINES:
                add_attempt("excel", header_row, engine=engine, temp_suffix=".xlsx")
                add_attempt("excel", header_row, engine=engine, temp_suffix=".xls")

    if detected_format not in {"xlsx", "xls"}:
        for header_row in HEADER_ROWS:
            for engine in EXCEL_ENGINES:
                add_attempt("excel", header_row, engine=engine)

    return attempts


def materialize_attempt_path(file_path, temp_suffix):
    if not temp_suffix:
        return file_path, None

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=temp_suffix)
    temp_file.close()
    shutil.copy2(file_path, temp_file.name)
    return temp_file.name, temp_file.name


def iter_readable_frames(file_path):
    for attempt in build_read_attempts(file_path):
        temp_path = None
        actual_path = file_path
        try:
            actual_path, temp_path = materialize_attempt_path(file_path, attempt["temp_suffix"])
            if attempt["kind"] == "excel":
                df = read_excel_candidate(actual_path, attempt["engine"], attempt["header_row"])
                method = f"excel-{attempt['engine']}"
            else:
                df = read_csv_candidate(actual_path, attempt["encoding"], attempt["header_row"])
                method = f"csv-{attempt['encoding']}"

            if len(df.columns) == 0:
                continue
            if len(df.columns) > 100:
                df = df.iloc[:, :10]

            yield df, method, attempt["header_row"], None
        except Exception as exc:
            yield None, None, attempt["header_row"], f"{attempt['kind']}读取失败: {str(exc)[:80]}"
        finally:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)


def find_company_column(columns, allow_fuzzy=False):
    columns_list = list(columns)
    normalized_columns = [str(col).strip() for col in columns_list]

    for keyword in COMPANY_COLUMN_NAMES:
        for index, column_name in enumerate(normalized_columns):
            if column_name == keyword:
                return columns_list[index], "exact", 3

    if not allow_fuzzy:
        return None, None, 0

    for keyword in COMPANY_COLUMN_NAMES:
        for index, column_name in enumerate(normalized_columns):
            if keyword in column_name and "Unnamed" not in column_name:
                return columns_list[index], "contains", 2

    for index, column_name in enumerate(normalized_columns):
        if "Unnamed" not in column_name:
            return columns_list[index], "fallback", 1

    return None, None, 0


def extract_companies(series):
    companies = []
    for value in series.dropna().astype(str).str.strip().tolist():
        lowered = value.lower()
        if not value or lowered == "nan" or len(value) < 4:
            continue
        companies.append(value)
    return list(dict.fromkeys(companies))


def choose_better_candidate(current_best, candidate):
    if current_best is None:
        return candidate
    return candidate if candidate["score"] > current_best["score"] else current_best


def resolve_company_data(file_path):
    errors = []
    best_primary = None
    best_supplemental = None
    readable = False

    for df, method, header_row, error in iter_readable_frames(file_path):
        if error:
            errors.append(error)
            continue

        readable = True
        for allow_fuzzy, stage_name in [(False, "primary"), (True, "supplemental")]:
            company_col, match_level, match_score = find_company_column(df.columns, allow_fuzzy=allow_fuzzy)
            if company_col is None:
                continue

            companies = extract_companies(df[company_col])
            if not companies:
                continue

            candidate = {
                "stage": stage_name,
                "company_col": company_col,
                "match_level": match_level,
                "match_score": match_score,
                "header_row": header_row,
                "read_method": method,
                "companies": companies,
                "score": (match_score, len(companies), -header_row),
                "columns_preview": [str(col) for col in list(df.columns)[:10]],
            }

            if stage_name == "primary":
                best_primary = choose_better_candidate(best_primary, candidate)
            else:
                best_supplemental = choose_better_candidate(best_supplemental, candidate)

    if best_primary is not None:
        return best_primary, errors
    if best_supplemental is not None:
        return best_supplemental, errors

    if readable:
        return None, errors + ["未找到公司名称列或未提取到企业名称"]
    return None, errors or ["无法读取文件"]


def build_feature_matrix(index_file, output_file, csv_folder):
    print(f"1. 正在读取目录总表: {index_file}")
    try:
        if index_file.endswith(".csv"):
            df_index = pd.read_csv(index_file, encoding="utf-8-sig")
        else:
            df_index = pd.read_excel(index_file)
    except Exception as exc:
        print(f"❌ 读取目录总表失败: {exc}")
        return

    target_columns = list(dict.fromkeys(TAG_MAPPING.values()))
    company_profiles = defaultdict(
        lambda: {
            "hit_features": set(),
            "core_levels": set(),
            "sources": set(),
            "latest_date": "",
        }
    )

    processed_files = 0
    primary_success_files = 0
    supplemental_success_files = []
    unmatched_files = []

    print("2. 正在进行实体对齐与特征抽取...")
    for _, row in df_index.iterrows():
        csv_filename = str(row.get("具体文件名称", "")).strip()
        dataset_name = str(row.get("数据集名称", "")).strip()
        tags_raw = str(row.get("业务标签 (Tags)", "")).strip()
        core_level = str(row.get("一级分类 (Core Risk Level)", "")).strip()
        url = str(row.get("文章访问路径", "")).strip()
        update_date = str(row.get("更新日期", "")).strip()

        file_tags = [tag.strip() for tag in tags_raw.split(",") if tag.strip()]
        matched_raw_tags = [tag for tag in file_tags if tag in TAG_MAPPING]
        if not matched_raw_tags or not csv_filename:
            continue

        csv_path = os.path.join(csv_folder, csv_filename)
        if not os.path.exists(csv_path):
            unmatched_files.append(
                {
                    "文件名": csv_filename,
                    "数据集名称": dataset_name,
                    "标签": matched_raw_tags,
                    "一级分类": core_level,
                    "错误信息": "文件不存在",
                }
            )
            continue

        resolved, errors = resolve_company_data(csv_path)
        if resolved is None:
            unmatched_files.append(
                {
                    "文件名": csv_filename,
                    "数据集名称": dataset_name,
                    "标签": matched_raw_tags,
                    "一级分类": core_level,
                    "错误信息": "；".join(errors[:3]),
                }
            )
            print(f"   [!] 跳过未匹配文件: {csv_filename}")
            continue

        processed_files += 1
        if resolved["stage"] == "primary":
            primary_success_files += 1
        else:
            supplemental_success_files.append(
                {
                    "原数据": {
                        "文件名": csv_filename,
                        "数据集名称": dataset_name,
                        "标签": matched_raw_tags,
                        "一级分类": core_level,
                    },
                    "匹配列名": resolved["company_col"],
                    "匹配阶段": resolved["stage"],
                    "匹配方式": resolved["match_level"],
                    "header行": resolved["header_row"],
                    "读取方法": resolved["read_method"],
                    "提取企业数": len(resolved["companies"]),
                    "企业样例": resolved["companies"][:5],
                }
            )

        if processed_files <= 5:
            print(
                f"   ✅ {csv_filename}: {resolved['read_method']}, "
                f"header={resolved['header_row']}, 列='{resolved['company_col']}', "
                f"企业数={len(resolved['companies'])}"
            )

        source_string = f"《{dataset_name}》({csv_filename})，{url}"
        for company_name in resolved["companies"]:
            if not company_name or company_name.lower() == "nan" or len(company_name) < 4:
                continue

            company_profiles[company_name]["core_levels"].add(core_level)
            company_profiles[company_name]["sources"].add(source_string)
            for raw_tag in matched_raw_tags:
                company_profiles[company_name]["hit_features"].add(TAG_MAPPING[raw_tag])

            clean_current_date = update_date.replace("旧", "")
            clean_saved_date = company_profiles[company_name]["latest_date"].replace("旧", "")
            if clean_current_date > clean_saved_date:
                company_profiles[company_name]["latest_date"] = update_date

    print(f"   ✅ 数据抽取完成！共处理 {processed_files} 个强关联文件。")
    print(f"   其中主流程直接成功 {primary_success_files} 个，补救流程补充成功 {len(supplemental_success_files)} 个。")

    print("\n3. 正在生成 One-Hot 特征矩阵大表...")
    final_rows = []
    for company_name, data in sorted(company_profiles.items()):
        row_data = {
            "更新日期": data["latest_date"],
            "企业名称": company_name,
            "一级分类": "，".join(sorted(data["core_levels"])),
        }
        for feature in target_columns:
            row_data[feature] = 1 if feature in data["hit_features"] else 0
        row_data["数据源"] = "。".join(sorted(data["sources"]))
        final_rows.append(row_data)

    df_final = pd.DataFrame(final_rows)
    cols_order = ["更新日期", "企业名称", "一级分类"] + target_columns + ["数据源"]
    if not df_final.empty:
        df_final = df_final[cols_order]
    else:
        df_final = pd.DataFrame(columns=cols_order)

    export_feature_matrix(df_final, output_file)

    unmatched_output = os.path.join(os.path.dirname(output_file), "未匹配文件列表.json")
    still_unmatched_output = os.path.join(os.path.dirname(output_file), "仍然未匹配文件_v2.json")
    supplemental_output = os.path.join(os.path.dirname(output_file), "补充处理成功文件_v2.json")

    with open(unmatched_output, "w", encoding="utf-8") as file_obj:
        json.dump(unmatched_files, file_obj, ensure_ascii=False, indent=2)

    with open(still_unmatched_output, "w", encoding="utf-8") as file_obj:
        json.dump(unmatched_files, file_obj, ensure_ascii=False, indent=2)

    with open(supplemental_output, "w", encoding="utf-8") as file_obj:
        json.dump(supplemental_success_files, file_obj, ensure_ascii=False, indent=2)

    if unmatched_files:
        print(f"\n⚠️  仍有 {len(unmatched_files)} 个文件未能匹配公司名称列")
        print(f"📝 未匹配文件已保存至: {unmatched_output}")
        print(f"📝 V2剩余未匹配清单已保存至: {still_unmatched_output}")
    else:
        print("\n✅ 所有文件都成功匹配公司名称列")

    print(f"📝 补救匹配成功明细已保存至: {supplemental_output}")


def export_feature_matrix(df_final, output_file):
    try:
        chunk_size = 100000
        total_rows = len(df_final)
        df_for_excel, sanitized_cells = sanitize_dataframe_for_excel(df_final)

        if sanitized_cells:
            print(f"   已清洗 {sanitized_cells} 个包含 Excel 非法字符的单元格")

        if total_rows <= chunk_size:
            df_for_excel.to_excel(output_file, index=False)
            print("=" * 40)
            print(f"🎉 Excel特征矩阵已生成！保存至: {output_file}")
            print(f"   包含 {total_rows} 家企业 x {len(df_for_excel.columns)} 列特征")
        else:
            file_base, file_ext = os.path.splitext(output_file)
            num_chunks = (total_rows + chunk_size - 1) // chunk_size

            print("=" * 40)
            print(f"📊 数据量较大({total_rows}条)，分页输出 Excel 文件:")
            for index in range(num_chunks):
                start_idx = index * chunk_size
                end_idx = min((index + 1) * chunk_size, total_rows)
                chunk_df = df_for_excel.iloc[start_idx:end_idx]
                chunk_file = output_file if num_chunks == 1 else f"{file_base}_{index + 1}{file_ext}"
                chunk_df.to_excel(chunk_file, index=False)
                print(f"   ✅ {chunk_file}: {len(chunk_df)} 家企业 ({start_idx + 1}-{end_idx})")
            print(f"🎉 共生成 {num_chunks} 个 Excel 文件")
    except Exception as exc:
        print(f"❌ 导出 Excel 文件失败: {exc}")

    json_output_file = output_file.replace(".xlsx", ".json").replace(".xls", ".json")
    try:
        with open(json_output_file, "w", encoding="utf-8") as file_obj:
            json.dump(df_final.to_dict(orient="records"), file_obj, ensure_ascii=False, indent=2)
        print(f"🎉 JSON特征矩阵已生成！保存至: {json_output_file}")
        print("=" * 40)
    except Exception as exc:
        print(f"❌ 导出 JSON 文件失败: {exc}")


def sanitize_excel_value(value):
    if not isinstance(value, str):
        return value, False

    cleaned = ILLEGAL_EXCEL_CHARACTERS.sub("", value)
    if cleaned != value:
        return cleaned, True
    return value, False


def sanitize_dataframe_for_excel(df):
    sanitized_cells = 0

    def sanitize_series(series):
        nonlocal sanitized_cells
        cleaned_values = []
        for value in series.tolist():
            cleaned, changed = sanitize_excel_value(value)
            if changed:
                sanitized_cells += 1
            cleaned_values.append(cleaned)
        return pd.Series(cleaned_values, index=series.index)

    sanitized_df = df.apply(sanitize_series)
    return sanitized_df, sanitized_cells


def parse_args():
    parser = argparse.ArgumentParser(description="一次运行完成企业画像宽表构建和未匹配文件补救处理")
    parser.add_argument(
        "--index-file",
        default=os.path.join(SCRIPT_DIR, "目录清单_分类结果.xlsx"),
        help="目录总表路径",
    )
    parser.add_argument(
        "--output-file",
        default=os.path.join(SCRIPT_DIR, "特征矩阵风控模型宽表.xlsx"),
        help="输出宽表路径",
    )
    parser.add_argument(
        "--csv-dir",
        default=os.path.join(SCRIPT_DIR, "bank"),
        help="原始数据文件目录",
    )
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    build_feature_matrix(arguments.index_file, arguments.output_file, arguments.csv_dir)
