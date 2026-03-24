import os
import re
import time

import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


FILENAME_PATTERN = re.compile(
    r"([\w\u4e00-\u9fff\-（）()【】《》、·]+?\.(?:csv|xlsx))",
    re.IGNORECASE,
)


def compact_text(value):
    return re.sub(r"\s+", "", str(value or ""))


def parse_update_date(page_source):
    page_text = BeautifulSoup(page_source, "html.parser").get_text(separator="", strip=True)
    update_pattern = re.compile(r"更新日期[：:\s]*(\d{4}-\d{2}-\d{2})")
    update_match = update_pattern.search(page_text)
    return update_match.group(1) if update_match else "未找到"


def extract_filename_candidates(page_source):
    soup = BeautifulSoup(page_source, "html.parser")
    raw_texts = [page_source, soup.get_text(separator=" ", strip=True)]

    for tag in soup.find_all(True):
        for attr_name in ("href", "title", "download", "data-original-title"):
            attr_value = tag.get(attr_name)
            if attr_value:
                raw_texts.append(str(attr_value))

    candidates = set()
    for raw_text in raw_texts:
        normalized_text = compact_text(raw_text)
        for match in FILENAME_PATTERN.findall(normalized_text):
            candidates.add(match)

    return sorted(candidates)


def choose_preferred_filename(candidates, dataset_name):
    if not candidates:
        return ""

    dataset_key = compact_text(dataset_name).lower()
    matched_candidates = []

    if dataset_key:
        matched_candidates = [
            filename
            for filename in candidates
            if dataset_key in compact_text(filename).lower()
        ]

    target_candidates = matched_candidates or candidates

    csv_files = sorted(
        filename for filename in target_candidates if filename.lower().endswith(".csv")
    )
    if csv_files:
        return csv_files[0]

    xlsx_files = sorted(
        filename for filename in target_candidates if filename.lower().endswith(".xlsx")
    )
    if xlsx_files:
        return xlsx_files[0]

    return ""


def extract_dynamic_data_info(driver, url, dataset_name):
    """
    提取单个网页的更新日期与具体文件名称。
    """
    try:
        driver.get(url)
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        time.sleep(2)

        page_sources = [driver.page_source]

        try:
            data_info_tab = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), '数据信息')]"))
            )
            data_info_tab.click()
            time.sleep(2)
            page_sources.append(driver.page_source)
        except Exception:
            pass

        update_time = "未找到"
        filename_candidates = set()

        for page_source in page_sources:
            if update_time == "未找到":
                update_time = parse_update_date(page_source)
            filename_candidates.update(extract_filename_candidates(page_source))

        preferred_filename = choose_preferred_filename(
            sorted(filename_candidates), dataset_name
        )
        return update_time, preferred_filename

    except Exception as e:
        print(f"  [!] 抓取出错: {e}")
        return "抓取失败", ""


def batch_process(input_file_path, output_file_path):
    print(f"正在读取文件: {input_file_path}")
    try:
        if input_file_path.endswith(".csv"):
            df = pd.read_csv(input_file_path, encoding="utf-8-sig")
        else:
            df = pd.read_excel(input_file_path)
    except Exception as e:
        print(f"❌ 读取文件失败: {e}")
        return

    required_columns = ["文章访问路径", "更新日期", "数据集名称"]
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        print(f"❌ 错误：表格中缺少必要列: {missing_columns}")
        return

    if "具体文件名称" not in df.columns:
        df["具体文件名称"] = ""

    print(f"共发现 {len(df)} 条数据准备处理。\n")

    print("正在启动 Chrome 浏览器...")
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)

    rows_to_drop = []

    try:
        for index, row in df.iterrows():
            url = str(row.get("文章访问路径", "")).strip()
            dataset_name = str(row.get("数据集名称", "未知数据集")).strip()

            print(f"[{index + 1}/{len(df)}] 正在处理: {dataset_name}")

            if not url.startswith("http"):
                print("  [!] 网址无效或为空，当前行将被删除")
                rows_to_drop.append(index)
                continue

            print(f"  -> 网址: {url}")
            upd_time, filename = extract_dynamic_data_info(driver, url, dataset_name)
            print(f"  -> 结果: 更新日期={upd_time}，具体文件名称={filename or '未找到'}")

            if upd_time not in ["未找到", "抓取失败"]:
                df.at[index, "更新日期"] = upd_time
            else:
                orig_date = str(row.get("更新日期", ""))
                if not orig_date.startswith("旧"):
                    df.at[index, "更新日期"] = f"旧{orig_date}"
                print(f"  [!] 更新日期抓取失败，已保留原值并标记为旧")

            if filename:
                df.at[index, "具体文件名称"] = filename
            else:
                print("  [!] 未找到 .csv 或 .xlsx 文件名，当前行将被删除")
                rows_to_drop.append(index)

            time.sleep(1)

    finally:
        print("\n所有任务处理完毕，关闭浏览器。")
        driver.quit()

    if rows_to_drop:
        df = df.drop(index=sorted(set(rows_to_drop))).reset_index(drop=True)
        print(f"已删除 {len(set(rows_to_drop))} 行未匹配到具体文件名称的数据。")

    print(f"正在保存结果到: {output_file_path}")
    try:
        if output_file_path.endswith(".csv"):
            df.to_csv(output_file_path, index=False, encoding="utf-8-sig")
        else:
            df.to_excel(output_file_path, index=False)
        print("🎉 保存成功！")
    except Exception as e:
        print(f"❌ 保存文件失败: {e}")


if __name__ == "__main__":
    input_file = "目录清单_分类结果_人工过筛.xlsx"
    file_name, ext = os.path.splitext(input_file)
    output_file = f"{file_name}_更新时间_补充文件名{ext}"
    batch_process(input_file, output_file)
