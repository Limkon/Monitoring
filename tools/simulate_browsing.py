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
from typing import Optional, Tuple

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoSuchElementException,
    WebDriverException,
    TimeoutException,
    ElementNotInteractableException
)

# --- 配置日志 ---
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(threadName)s - [%(levelname)s] - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

class BrowsingConfig:
    """浏览模拟配置"""
    # 如果在 GitHub Actions 中遇到资源耗尽，建议将此值降低 (例如 2)
    MAX_WORKERS = 4
    NUM_RANDOM_OPERATIONS = 3
    NUM_MOUSE_MOVES_PER_OP = 3
    SCROLL_PAUSE_DURATION = 1.0
    ACTION_PAUSE_DURATION = 0.5
    SHORT_PAUSE_DURATION = 0.2
    WEBDRIVER_WAIT_TIMEOUT = 15
    DEFAULT_WINDOW_WIDTH = 1920
    DEFAULT_WINDOW_HEIGHT = 1200
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"

class BrowserSimulator:
    """浏览器模拟器核心类"""

    def __init__(self, chrome_driver_path: Optional[str] = None):
        self.chrome_driver_path = chrome_driver_path

    def remove_duplicates_and_empty_lines_from_file(self, filename: str) -> bool:
        """从文件中移除重复行和空行，并确保行是有效的 URL。"""
        lines_seen = set()
        output_lines = []
        logger.info(f"开始预处理檔案: {filename}...")
        
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                for line in file:
                    stripped_line = line.strip()
                    if stripped_line and re.match(r'^https?://', stripped_line) and stripped_line not in lines_seen:
                        lines_seen.add(stripped_line)
                        output_lines.append(stripped_line)
        except FileNotFoundError:
            logger.error(f"檔案 {filename} 未找到。")
            return False

        try:
            # 使用 tempfile 进行原子写入
            with tempfile.NamedTemporaryFile('w', delete=False, encoding='utf-8') as temp_file:
                temp_file.write('\n'.join(output_lines))
                # 确保最后有换行符，视情况而定，这里保持原逻辑
                temp_filename = temp_file.name
            shutil.move(temp_filename, filename)
            logger.info(f"檔案预处理完成，保留 {len(output_lines)} 个有效 URL。")
            return True
        except Exception as e:
            logger.error(f"写入或移动檔案时发生错误: {e}")
            if 'temp_filename' in locals() and os.path.exists(temp_filename):
                 os.remove(temp_filename)
            return False

    def create_driver(self) -> Optional[webdriver.Chrome]:
        """为单一执行绪建立并返回一个配置好的 WebDriver 实例。"""
        chrome_options = Options()
        arguments = [
            "--headless", "--no-sandbox", "--disable-dev-shm-usage",
            f"--window-size={BrowsingConfig.DEFAULT_WINDOW_WIDTH},{BrowsingConfig.DEFAULT_WINDOW_HEIGHT}",
            "--ignore-certificate-errors", "--ignore-ssl-errors=yes", "--disable-gpu",
            "--log-level=3", f"user-agent={BrowsingConfig.USER_AGENT}",
            "--disable-blink-features=AutomationControlled"
        ]
        for arg in arguments:
            chrome_options.add_argument(arg)
        
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        try:
            if self.chrome_driver_path:
                service = ChromeService(executable_path=self.chrome_driver_path)
                driver = webdriver.Chrome(service=service, options=chrome_options)
            else:
                driver = webdriver.Chrome(options=chrome_options)
            return driver
        except WebDriverException as e:
            logger.error(f"WebDriver 初始化失败: {e}")
            if "executable needs to be in PATH" in str(e):
                logger.error("错误提示：ChromeDriver 可执行档需要被新增到系统 PATH 环境变数中。")
            return None

    def simulate_random_click(self, driver: webdriver.Chrome):
        """模拟一次随机点击。"""
        try:
            wait = WebDriverWait(driver, 5)
            clickable_elements = wait.until(EC.presence_of_all_elements_located(
                (By.XPATH, "//a[@href] | //button | //input[@type='submit'] | //input[@type='button']")
            ))
            
            visible_elements = [elem for elem in clickable_elements if elem.is_displayed()]
            
            if visible_elements:
                target = random.choice(visible_elements)
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", target)
                time.sleep(BrowsingConfig.SHORT_PAUSE_DURATION)
                ActionChains(driver).move_to_element(target).click().perform()
                logger.info(f"    操作: 点击元素 <{target.tag_name}> 成功。")
                return

        except (TimeoutException, NoSuchElementException):
            logger.warning("    未找到可见的可点击元素，将尝试点击 body。")
        except ElementNotInteractableException:
            logger.warning("    找到的元素不可互动，将尝试点击 body。")
        except Exception as e:
            logger.error(f"    寻找点击元素时发生未知错误: {e}，将尝试点击 body。")

        try:
            body = driver.find_element(By.TAG_NAME, "body")
            ActionChains(driver).move_to_element(body).click().perform()
            logger.info("    操作: 点击 <body> 元素成功。")
        except Exception as e:
            logger.error(f"    点击 <body> 时失败: {e}")

    def simulate_mouse_movement(self, driver: webdriver.Chrome):
        """模拟滑鼠在页面上的随机移动。"""
        try:
            actions = ActionChains(driver)
            body = driver.find_element(By.TAG_NAME, "body")
            actions.move_to_element(body)
            
            for _ in range(BrowsingConfig.NUM_MOUSE_MOVES_PER_OP):
                x_offset = random.randint(-200, 200)
                y_offset = random.randint(-200, 200)
                actions.move_by_offset(x_offset, y_offset)
                actions.pause(BrowsingConfig.SHORT_PAUSE_DURATION)
            
            actions.perform()
            logger.info("    操作: 模拟滑鼠移动完成。")
        except Exception as e:
            logger.error(f"    模拟滑鼠移动时失败: {e}")

    def simulate_scrolling(self, driver: webdriver.Chrome):
        """模拟上下滚动页面。"""
        try:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(BrowsingConfig.SCROLL_PAUSE_DURATION / 2)
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(BrowsingConfig.SCROLL_PAUSE_DURATION / 2)
            logger.info("    操作: 模拟页面滚动完成。")
        except Exception as e:
            logger.error(f"    模拟滚动时失败: {e}")

    def process_url_worker(self, url: str, index: int) -> Tuple[str, bool]:
        """处理单一 URL 的完整流程。"""
        logger.info(f"开始处理第 {index + 1} 个 URL: {url}")
        driver = self.create_driver()
        if not driver:
            return url, False

        try:
            driver.set_page_load_timeout(30) # 防止页面加载无限挂起
            driver.get(url)
            
            WebDriverWait(driver, BrowsingConfig.WEBDRIVER_WAIT_TIMEOUT).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            logger.info(f"成功打开网页: {url}")

            operations = [self.simulate_random_click, self.simulate_mouse_movement, self.simulate_scrolling]
            for _ in range(BrowsingConfig.NUM_RANDOM_OPERATIONS):
                op = random.choice(operations)
                op(driver)
                time.sleep(BrowsingConfig.ACTION_PAUSE_DURATION)
            
            driver.refresh()
            logger.info(f"页面刷新成功: {url}")
            return url, True

        except TimeoutException:
            logger.error(f"载入 URL 超时: {url}")
            return url, False
        except WebDriverException as e:
            logger.error(f"处理 URL '{url}' 时发生 WebDriver 错误: {e}")
            return url, False
        except Exception:
            logger.error(f"处理 URL '{url}' 时发生未知异常:\n{traceback.format_exc()}")
            return url, False
        finally:
            if driver:
                try:
                    driver.quit()
                    logger.info(f"URL '{url}' WebDriver 已安全关闭。")
                except Exception as e:
                    logger.warning(f"关闭 URL '{url}' 的 WebDriver 时发生错误: {e}")

def main():
    if len(sys.argv) not in [2, 3]:
        print("用法: python simulate_browsing.py <url_filename> [chrome_driver_path]")
        sys.exit(1)

    url_filename = sys.argv[1]
    chrome_driver_path = sys.argv[2] if len(sys.argv) == 3 else None

    if not os.path.exists(url_filename):
        logger.error(f"URL 檔案 '{url_filename}' 不存在。")
        sys.exit(1)

    simulator = BrowserSimulator(chrome_driver_path)

    if not simulator.remove_duplicates_and_empty_lines_from_file(url_filename):
        logger.error("檔案预处理失败，指令码终止。")
        sys.exit(1)

    try:
        with open(url_filename, 'r', encoding='utf-8') as file:
            urls = [line.strip() for line in file if line.strip()]
        if not urls:
            logger.info(f"檔案 '{url_filename}' 中没有有效的 URL。")
            sys.exit(0)
        logger.info(f"读取到 {len(urls)} 个 URL 准备处理。将使用最多 {BrowsingConfig.MAX_WORKERS} 个并发执行绪。")
    except Exception as e:
        logger.error(f"读取 URL 檔案 '{url_filename}' 失败: {e}")
        sys.exit(1)

    success_count = 0
    fail_count = 0

    with ThreadPoolExecutor(max_workers=BrowsingConfig.MAX_WORKERS) as executor:
        future_to_url = {executor.submit(simulator.process_url_worker, url, i): url 
                         for i, url in enumerate(urls)}
        
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                _, success = future.result()
                if success:
                    success_count += 1
                else:
                    fail_count += 1
            except Exception as exc:
                logger.error(f"URL '{url}' 在执行中产生了无法捕获的异常: {exc}")
                fail_count += 1

    logger.info("--- 所有任务执行完毕 ---")
    logger.info(f"总 URL 数量: {len(urls)}")
    logger.info(f"成功处理数量: {success_count}")
    logger.info(f"失败处理数量: {fail_count}")
    logger.info("指令码执行结束。")

if __name__ == "__main__":
    main()
