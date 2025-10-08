import os
import sys
import tempfile
import shutil
import re
import time
import random
import logging
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoSuchElementException,
    MoveTargetOutOfBoundsException,
    InvalidArgumentException,
    WebDriverException,
    TimeoutException,
    ElementNotInteractableException
)

# --- 配置常數 ---
# 併發執行的瀏覽器數量 (執行緒數)
MAX_WORKERS = 4
# 對每個 URL 執行的隨機操作次數
NUM_RANDOM_OPERATIONS = 3
# 每次滑鼠移動操作中的小移動次數
NUM_MOUSE_MOVES_PER_OP = 3
# 滾動操作後的暫停時間
SCROLL_PAUSE_DURATION = 1.0
# 主要動作後的暫停時間
ACTION_PAUSE_DURATION = 0.5
# 短暫暫停時間
SHORT_PAUSE_DURATION = 0.2
# Selenium 等待超時時間
WEBDRIVER_WAIT_TIMEOUT = 15
# 預設瀏覽器視窗寬度
DEFAULT_WINDOW_WIDTH = 1920
# 預設瀏覽器視窗高度
DEFAULT_WINDOW_HEIGHT = 1200
# 使用者代理
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"

# --- 設定日誌 ---
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(threadName)s - [%(levelname)s] - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')


def remove_duplicates_and_empty_lines_from_file(filename):
    """從檔案中移除重複行和空行，並確保行是有效的 URL。結果寫回原檔案。"""
    lines_seen = set()
    output_lines = []
    logging.info(f"開始預處理檔案: {filename}...")
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            for line in file:
                stripped_line = line.strip()
                if stripped_line and re.match(r'^https?://', stripped_line) and stripped_line not in lines_seen:
                    lines_seen.add(stripped_line)
                    output_lines.append(stripped_line)
    except FileNotFoundError:
        logging.error(f"檔案 {filename} 未找到。")
        return False

    try:
        # 使用暫存檔案寫入，然後取代原檔案，確保原子性
        with tempfile.NamedTemporaryFile('w', delete=False, encoding='utf-8') as temp_file:
            temp_file.write('\n'.join(output_lines))
            temp_filename = temp_file.name
        shutil.move(temp_filename, filename)
        logging.info(f"檔案預處理完成，保留 {len(output_lines)} 個有效 URL。")
        return True
    except Exception as e:
        logging.error(f"寫入或移動檔案時發生錯誤: {e}")
        return False


def create_driver(chrome_driver_path=None):
    """為單一執行緒建立並返回一個配置好的 WebDriver 實例。"""
    chrome_options = Options()
    arguments = [
        "--headless", "--no-sandbox", "--disable-dev-shm-usage",
        f"--window-size={DEFAULT_WINDOW_WIDTH},{DEFAULT_WINDOW_HEIGHT}",
        "--ignore-certificate-errors", "--ignore-ssl-errors=yes", "--disable-gpu",
        "--log-level=3", f"user-agent={USER_AGENT}",
        "--disable-blink-features=AutomationControlled"
    ]
    for arg in arguments:
        chrome_options.add_argument(arg)
    
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    try:
        if chrome_driver_path:
            service = ChromeService(executable_path=chrome_driver_path)
            driver = webdriver.Chrome(service=service, options=chrome_options)
        else:
            driver = webdriver.Chrome(options=chrome_options)
        return driver
    except WebDriverException as e:
        logging.error(f"WebDriver 初始化失敗: {e}")
        if "executable needs to be in PATH" in str(e):
            logging.error("錯誤提示：ChromeDriver 可執行檔需要被新增到系統 PATH 環境變數中。")
        return None

# --- 模擬操作輔助函式 ---

def simulate_random_click(driver):
    """模擬一次隨機點擊。優先點擊可互動元素，否則點擊 body。"""
    try:
        # 優先尋找可見的連結或按鈕
        wait = WebDriverWait(driver, 5) # 給予較短的等待時間尋找元素
        clickable_elements = wait.until(EC.presence_of_all_elements_located(
            (By.XPATH, "//a[@href] | //button | //input[@type='submit'] | //input[@type='button']")
        ))
        
        visible_elements = [elem for elem in clickable_elements if elem.is_displayed()]
        
        if visible_elements:
            target = random.choice(visible_elements)
            # 嘗試滾動到元素並點擊
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", target)
            time.sleep(SHORT_PAUSE_DURATION)
            ActionChains(driver).move_to_element(target).click().perform()
            logging.info(f"    操作: 點擊元素 <{target.tag_name}> 成功。")
            return

    except (TimeoutException, NoSuchElementException):
        logging.warning("    未找到可見的可點擊元素，將嘗試點擊 body。")
    except ElementNotInteractableException:
        logging.warning("    找到的元素不可互動，將嘗試點擊 body。")
    except Exception as e:
        logging.error(f"    尋找點擊元素時發生未知錯誤: {e}，將嘗試點擊 body。")

    # 如果以上失敗，則退回至點擊 body
    try:
        body = driver.find_element(By.TAG_NAME, "body")
        ActionChains(driver).move_to_element(body).click().perform()
        logging.info("    操作: 點擊 <body> 元素成功。")
    except Exception as e:
        logging.error(f"    點擊 <body> 時失敗: {e}")


def simulate_mouse_movement(driver):
    """模擬滑鼠在頁面上的隨機移動。"""
    try:
        actions = ActionChains(driver)
        body = driver.find_element(By.TAG_NAME, "body")
        actions.move_to_element(body) # 移動到 body 作為起點
        
        for _ in range(NUM_MOUSE_MOVES_PER_OP):
            x_offset = random.randint(-200, 200)
            y_offset = random.randint(-200, 200)
            actions.move_by_offset(x_offset, y_offset)
            actions.pause(SHORT_PAUSE_DURATION)
        
        actions.perform()
        logging.info("    操作: 模擬滑鼠移動完成。")
    except Exception as e:
        logging.error(f"    模擬滑鼠移動時失敗: {e}")


def simulate_scrolling(driver):
    """模擬上下滾動頁面。"""
    try:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(SCROLL_PAUSE_DURATION / 2)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(SCROLL_PAUSE_DURATION / 2)
        logging.info("    操作: 模擬頁面滾動完成。")
    except Exception as e:
        logging.error(f"    模擬滾動時失敗: {e}")


def process_url_worker(url, index, chrome_driver_path=None):
    """
    工作函式：處理單一 URL 的完整流程。
    為保證執行緒安全，WebDriver 在此函式內建立和銷毀。
    """
    logging.info(f"開始處理第 {index + 1} 個 URL: {url}")
    driver = create_driver(chrome_driver_path)
    if not driver:
        return url, False

    try:
        driver.get(url)
        
        # 使用顯式等待，確保頁面基本載入完成
        WebDriverWait(driver, WEBDRIVER_WAIT_TIMEOUT).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        logging.info(f"成功打開網頁: {url}")

        # 執行一系列隨機操作
        operations = [simulate_random_click, simulate_mouse_movement, simulate_scrolling]
        for i in range(NUM_RANDOM_OPERATIONS):
            op = random.choice(operations)
            op(driver)
            time.sleep(ACTION_PAUSE_DURATION)
        
        # 刷新頁面
        driver.refresh()
        logging.info(f"頁面刷新成功: {url}")
        
        return url, True

    except TimeoutException:
        logging.error(f"載入 URL 超時: {url}")
        return url, False
    except WebDriverException as e:
        logging.error(f"處理 URL '{url}' 時發生 WebDriver 錯誤: {e}")
        return url, False
    except Exception:
        logging.error(f"處理 URL '{url}' 時發生未知異常:\n{traceback.format_exc()}")
        return url, False
    finally:
        if driver:
            driver.quit()
        logging.info(f"URL '{url}' 處理完畢，WebDriver 已關閉。")


if __name__ == "__main__":
    if len(sys.argv) not in [2, 3]:
        print("用法: python simulate_browsing_refactored.py <url_filename> [chrome_driver_path]")
        sys.exit(1)

    url_filename = sys.argv[1]
    chrome_driver_path = sys.argv[2] if len(sys.argv) == 3 else None

    if not os.path.exists(url_filename):
        logging.error(f"URL 檔案 '{url_filename}' 不存在。")
        sys.exit(1)

    if not remove_duplicates_and_empty_lines_from_file(url_filename):
        logging.error("檔案預處理失敗，指令碼終止。")
        sys.exit(1)

    try:
        with open(url_filename, 'r', encoding='utf-8') as file:
            urls = [line.strip() for line in file if line.strip()]
        if not urls:
            logging.info(f"檔案 '{url_filename}' 中沒有有效的 URL。")
            sys.exit(0)
        logging.info(f"讀取到 {len(urls)} 個 URL 準備處理。將使用最多 {MAX_WORKERS} 個併發執行緒。")
    except Exception as e:
        logging.error(f"讀取 URL 檔案 '{url_filename}' 失敗: {e}")
        sys.exit(1)

    success_count = 0
    fail_count = 0

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_url = {executor.submit(process_url_worker, url, i, chrome_driver_path): url 
                         for i, url in enumerate(urls)}
        
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                processed_url, success = future.result()
                if success:
                    success_count += 1
                else:
                    fail_count += 1
            except Exception as exc:
                logging.error(f"URL '{url}' 在執行中產生了無法捕獲的異常: {exc}")
                fail_count += 1

    logging.info("--- 所有任務執行完畢 ---")
    logging.info(f"總 URL 數量: {len(urls)}")
    logging.info(f"成功處理數量: {success_count}")
    logging.info(f"失敗處理數量: {fail_count}")
    logging.info("指令碼執行結束。")
