"""
批量下载器 - 支持微信扫码登录后批量下载数据集文件
(已优化: 极简触发模式，浏览器关闭后统一进行本地文件精准对账校验)
"""

import argparse
import os
import re
import sys
import time

import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementClickInterceptedException,
    StaleElementReferenceException,
)


# ==================== 默认配置 ====================

DEFAULT_LOGIN_URL = "https://data.beijing.gov.cn"
DEFAULT_DOWNLOAD_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "downloads"
)
PAGE_LOAD_TIMEOUT = 20
MAX_RETRY = 3


# ==================== 工具函数 ====================

def create_driver(download_dir):
    """创建带有自定义下载路径的 Chrome 浏览器实例"""
    os.makedirs(download_dir, exist_ok=True)

    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")

    prefs = {
        "download.default_directory": os.path.abspath(download_dir),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
        "plugins.always_open_pdf_externally": True,
    }
    options.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(60)
    return driver


def wait_for_wechat_login(driver, login_url):
    """打开登录页面，等待用户完成微信扫码登录"""
    print("\n" + "=" * 70)
    print("  请在弹出浏览器中完成微信扫码登录")
    print("=" * 70)

    driver.get(login_url)
    time.sleep(3)

    # 尝试自动点击登录入口（如果页面有）
    try:
        login_btn = driver.find_element(
            By.XPATH,
            "//*[contains(text(), '登录') or contains(text(), '微信登录') "
            "or contains(@class, 'login')]",
        )
        login_btn.click()
        time.sleep(2)
    except Exception:
        pass

    input("  >>> 微信扫码登录完成后，请在此按 Enter 键继续... ")
    print("\n  [OK] 用户已确认登录完成，开始执行下载任务")
    return True


def wait_for_all_background_downloads(download_dir):
    """在脚本结束前，等待所有的后台下载任务完成"""
    print("\n" + "=" * 70)
    print("  [INFO] 所有网页已遍历完毕，正在等待后台下载队列清空...")
    print("  [注意] 请勿关闭浏览器，脚本会在所有文件下载完毕后自动退出")
    print("=" * 70)
    
    while True:
        current_files = os.listdir(download_dir)
        downloading_files = [
            f for f in current_files
            if f.endswith((".crdownload", ".tmp", ".part"))
        ]
        
        if not downloading_files:
            print("  [OK] 所有后台下载任务已全部完成！")
            time.sleep(2) 
            break
            
        print(f"  [WAIT] 仍有 {len(downloading_files)} 个文件正在后台下载中，等待 10 秒后复查...")
        time.sleep(10)


def find_and_click_download(driver, filename):
    """在页面上寻找对应文件名的下载按钮并点击（去除了复杂的判断，点完就跑）"""
    compact_filename = re.sub(r"\s+", "", filename)

    # 策略 1: XPath 精确匹配文件名
    xpaths = [
        f"//*[contains(normalize-space(.), '{filename}')]//ancestor-or-self::a",
        f"//a[contains(@href, '{filename}')]",
        f"//a[contains(@title, '{filename}')]",
        f"//a[contains(@download, '{filename}')]",
        f"//*[contains(normalize-space(.), '{os.path.splitext(filename)[0]}')]//ancestor-or-self::a",
        f"//*[contains(normalize-space(.), '{filename}')]/ancestor::*[position()<=3]//a[contains(@class, 'download') or contains(@href, 'download')]",
        f"//*[contains(normalize-space(.), '{filename}')]/ancestor::*[position()<=3]//*[contains(@class, 'download')]",
    ]

    for xpath in xpaths:
        try:
            elements = driver.find_elements(By.XPATH, xpath)
            for elem in elements:
                if elem.is_displayed():
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elem)
                    time.sleep(0.5)
                    elem.click()
                    time.sleep(1) # 给浏览器 1 秒钟的反应时间来建立下载任务
                    print("    [OK] 已点击下载按钮 (XPath匹配)")
                    return True
        except Exception:
            continue

    # 策略 2: 遍历所有 <a> 链接匹配
    try:
        links = driver.find_elements(By.TAG_NAME, "a")
        for link in links:
            try:
                href = link.get_attribute("href") or ""
                text = link.text or ""
                title = link.get_attribute("title") or ""
                download_attr = link.get_attribute("download") or ""

                check_strings = [href, text, title, download_attr]
                matched = any(compact_filename.lower() in re.sub(r"\s+", "", s).lower() for s in check_strings if s)
                if not matched:
                    matched = any(s.lower().endswith((".csv", ".xlsx", ".xls")) for s in [href] if s)

                if matched and link.is_displayed():
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", link)
                    time.sleep(0.5)
                    link.click()
                    time.sleep(1)
                    print("    [OK] 已点击下载链接 (遍历匹配)")
                    return True
            except (StaleElementReferenceException, ElementClickInterceptedException):
                continue
    except Exception:
        pass

    # 策略 3: 通用「下载」按钮
    download_xpaths = [
        "//button[contains(text(), '下载')]",
        "//a[contains(text(), '下载')]",
        "//*[contains(@class, 'download')]",
        "//a[contains(@href, 'download')]",
        "//button[contains(@class, 'btn')]",
        "//span[contains(text(), '下载')]/..",
        "//*[@title='下载']",
    ]

    for xpath in download_xpaths:
        try:
            elements = driver.find_elements(By.XPATH, xpath)
            for elem in elements:
                if elem.is_displayed():
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elem)
                    time.sleep(0.5)
                    elem.click()
                    time.sleep(1)
                    print("    [OK] 已点击下载按钮 (通用匹配)")
                    return True
        except Exception:
            continue

    # 策略 4: JS 触发下载
    try:
        js_code = """
        var links = document.querySelectorAll('a');
        var targetFile = arguments[0].toLowerCase();
        for (var i = 0; i < links.length; i++) {
            var href = (links[i].href || '').toLowerCase();
            var text = (links[i].textContent || '').toLowerCase();
            if (href.indexOf(targetFile) !== -1 || text.indexOf(targetFile) !== -1) {
                links[i].click();
                return 'clicked';
            }
        }
        return 'not_found';
        """
        result = driver.execute_script(js_code, compact_filename.lower())
        if result == "clicked":
            time.sleep(1)
            print("    [OK] 已触发下载 (JS强制触发)")
            return True
    except Exception:
        pass

    return False


def handle_download_popups(driver):
    """处理二次确认弹窗"""
    popup_xpaths = [
        "//button[contains(text(), '确定')]",
        "//button[contains(text(), '同意')]",
        "//button[contains(text(), '确认')]",
        "//button[contains(text(), '开始下载')]",
        "//*[contains(@class, 'confirm')]",
        "//*[contains(@class, 'agree')]",
    ]
    for xpath in popup_xpaths:
        try:
            elements = driver.find_elements(By.XPATH, xpath)
            for elem in elements:
                if elem.is_displayed():
                    elem.click()
                    time.sleep(1)
                    return True
        except Exception:
            continue
    return False


# ==================== 主流程 ====================

def batch_download(input_file, download_dir, login_url):
    print(f"\n[INFO] 正在读取文件: {input_file}")
    try:
        if input_file.endswith(".csv"):
            df = pd.read_csv(input_file, encoding="utf-8-sig")
        else:
            df = pd.read_excel(input_file)
    except Exception as e:
        print(f"[ERROR] 读取文件失败: {e}")
        return

    required_cols = ["文章访问路径", "具体文件名称"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        print(f"[ERROR] 缺少必要列: {missing}")
        return

    df_valid = df[df["具体文件名称"].notna() & (df["具体文件名称"].str.strip() != "")].copy()
    total = len(df_valid)
    print(f"[INFO] 共 {len(df)} 条记录，其中 {total} 条将执行下载流程\n")

    if total == 0:
        return

    print(f"[INFO] 下载目录: {os.path.abspath(download_dir)}")
    driver = create_driver(download_dir)

    try:
        # 强制要求每次手动扫码登录
        wait_for_wechat_login(driver, login_url)

        print("\n" + "=" * 70)
        print(f"  开始批量点击下载，共 {total} 个文件")
        print("=" * 70 + "\n")

        for idx, (_, row) in enumerate(df_valid.iterrows()):
            url = str(row.get("文章访问路径", "")).strip()
            filename = str(row.get("具体文件名称", "")).strip()
            dataset_name = str(row.get("数据集名称", "未知")).strip()

            print(f"\n[{idx + 1}/{total}] {dataset_name}")
            print(f"  待下文件: {filename}")

            if not url.startswith("http"):
                print("  [ERROR] 无效 URL，跳过")
                continue

            # 开始尝试访问并点击
            for retry in range(MAX_RETRY):
                try:
                    driver.get(url)
                    WebDriverWait(driver, PAGE_LOAD_TIMEOUT).until(
                        EC.presence_of_element_located((By.TAG_NAME, "body"))
                    )
                    time.sleep(3)

                    # 检查页面是否提示登录失效
                    page_text = driver.page_source
                    if "请登录" in page_text or "微信扫码" in page_text:
                        print("  [WARN] 检测到登录状态失效，需要重新扫码...")
                        wait_for_wechat_login(driver, login_url)
                        driver.get(url)
                        time.sleep(3)

                    # 尝试点击「数据信息」标签
                    try:
                        tab = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), '数据信息')]"))
                        )
                        tab.click()
                        time.sleep(2)
                    except TimeoutException:
                        pass

                    # 查找并点击下载
                    success = find_and_click_download(driver, filename)

                    # 处理弹窗
                    if not success:
                        handle_download_popups(driver)
                        time.sleep(2)
                        success = find_and_click_download(driver, filename)

                    if success:
                        break  # 成功点击，立刻去往下一个链接
                    else:
                        if retry < MAX_RETRY - 1:
                            print(f"  [WARN] 第 {retry + 1} 次未找到下载按钮，重试...")
                            time.sleep(2)
                        else:
                            print(f"  [ERROR] 网页中未定位到该文件的下载按钮")

                except Exception as e:
                    if retry < MAX_RETRY - 1:
                        print(f"  [WARN] 页面加载或执行出错，重试...")
                        time.sleep(2)

        # 网页全部跑完，死等后台下载任务完成
        wait_for_all_background_downloads(download_dir)

    finally:
        print("\n  正在关闭浏览器...")
        driver.quit()
        
        # ==========================================
        # 核心改动：浏览器关闭后，进行本地文件对账校验
        # ==========================================
        print("\n" + "=" * 70)
        print("  开始进行本地文件对账校验...")
        print("=" * 70)
        
        # 获取下载目录下的所有最终文件（此时已不存在.crdownload）
        if os.path.exists(download_dir):
            downloaded_files = os.listdir(download_dir)
        else:
            downloaded_files = []
            
        success_count = 0
        fail_count = 0
        un_downloaded_records = []

        for idx, (_, row) in enumerate(df_valid.iterrows()):
            expected_filename = str(row.get("具体文件名称", "")).strip()
            
            # 判断逻辑：只要下载文件夹里有某个文件的名字包含期待的文件名，就算成功
            # 这样可以兼容浏览器下载时自动添加的 (1), (2) 后缀
            is_downloaded = any(expected_filename in f for f in downloaded_files)
            
            if is_downloaded:
                success_count += 1
            else:
                fail_count += 1
                un_downloaded_records.append({
                    "数据集名称": str(row.get("数据集名称", "未知")).strip(),
                    "具体文件名": expected_filename,
                    "下载链接": str(row.get("文章访问路径", "")).strip(),
                    "原因": "本地对账未找到对应文件"
                })

        print("\n  校验统计:")
        print(f"  计划下载: {total} 个")
        print(f"  实际成功: {success_count} 个")
        print(f"  缺失失败: {fail_count} 个")

        if un_downloaded_records:
            fail_file = os.path.join(
                os.path.dirname(os.path.abspath(input_file)),
                "un_downloaded_records.csv",
            )
            pd.DataFrame(un_downloaded_records).to_csv(fail_file, index=False, encoding="utf-8-sig")
            print(f"  [注意] 缺失文件的记录已保存至:\n  -> {fail_file}")

        print("\n  批量下载任务彻底结束！")


# ==================== 入口 ====================

def main():
    parser = argparse.ArgumentParser(
        description="批量下载数据集文件（采用本地目录对账模式）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("--input", "-i", default="output/目录清单_分类结果_更新时间_补充文件名.xlsx", help="输入的 Excel/CSV 文件路径")
    parser.add_argument("--download-dir", "-d", default="output/分类结果下载文件", help="文件下载保存目录")
    parser.add_argument("--login-url", "-l", default=DEFAULT_LOGIN_URL, help="登录页面 URL")

    args = parser.parse_args()

    if not os.path.exists(args.input):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        alt_path = os.path.join(script_dir, args.input)
        if os.path.exists(alt_path):
            args.input = alt_path
        else:
            print(f"[ERROR] 输入文件不存在: {args.input}")
            sys.exit(1)

    batch_download(args.input, args.download_dir, args.login_url)

if __name__ == "__main__":
    main()