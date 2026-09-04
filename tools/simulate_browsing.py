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
    TimeoutException
)

# --- 日志配置 ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(threadName)s - [%(levelname)s] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class BrowsingConfig:
    """保活模拟浏览配置"""
    # GitHub Actions 虚拟机建议最大设为 2，防止内存溢出(OOM)闪退
    MAX_WORKERS = 2
    NUM_RANDOM_OPERATIONS = 2
    NUM_MOUSE_MOVES_PER_OP = 2
    SCROLL_PAUSE_DURATION = 1.0
    ACTION_PAUSE_DURATION = 0.5
    SHORT_PAUSE_DURATION = 0.2
    WEBDRIVER_WAIT_TIMEOUT = 20
    DEFAULT_WINDOW_WIDTH = 1920
    DEFAULT_WINDOW_HEIGHT = 1080
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

class BrowserSimulator:
    """保活浏览器模拟器"""

    def __init__(self, chrome_driver_path: Optional[str] = None):
        self.chrome_driver_path = chrome_driver_path

    def remove_duplicates_and_empty_lines_from_file(self, filename: str) -> bool:
        """预处理：清理重复、空白及非法 URL"""
        lines_seen = set()
        output_lines = []
        logger.info(f"开始预处理文件: {filename}...")
        
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                for line in file:
                    stripped_line = line.strip()
                    if stripped_line and re.match(r'^https?://', stripped_line) and stripped_line not in lines_seen:
                        lines_seen.add(stripped_line)
                        output_lines.append(stripped_line)
        except FileNotFoundError:
            logger.error(f"文件 {filename} 未找到。")
            return False

        try:
            with tempfile.NamedTemporaryFile('w', delete=False, encoding='utf-8') as temp_file:
                temp_file.write('\n'.join(output_lines) + '\n')
                temp_filename = temp_file.name
            shutil.move(temp_filename, filename)
            logger.info(f"文件预处理完成，有效保活 URL 数量: {len(output_lines)}")
            return True
        except Exception as e:
            logger.error(f"写入文件发生错误: {e}")
            if 'temp_filename' in locals() and os.path.exists(temp_filename):
                os.remove(temp_filename)
            return False

    def create_driver(self) -> Optional[webdriver.Chrome]:
        """创建低内存开销、高度拟真的 WebDriver"""
        chrome_options = Options()
        arguments = [
            "--headless=new",                    # 使用 Chrome 最新的无头模式（拟真度更高）
            "--no-sandbox",
            "--disable-dev-shm-usage",           # 防止 GitHub Runner 共享内存不足崩溃
            f"--window-size={BrowsingConfig.DEFAULT_WINDOW_WIDTH},{BrowsingConfig.DEFAULT_WINDOW_HEIGHT}",
            "--ignore-certificate-errors",
            "--disable-gpu",
            "--mute-audio",                      # 静音，避免音频解码消耗 CPU
            "--disable-background-networking",
            "--disable-default-apps",
            "--no-first-run",
            "--log-level=3",
            f"user-agent={BrowsingConfig.USER_AGENT}",
            "--disable-blink-features=AutomationControlled" # 去除自动化特征
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
            return None

    def simulate_safe_click(self, driver: webdriver.Chrome):
        """【安全点击】：仅点击空白处或 body，坚决不点击功能性按钮/链接"""
        try:
            body = driver.find_element(By.TAG_NAME, "body")
            # 在页面安全边距处点击一次，触发活跃事件
            ActionChains(driver).move_to_element_with_offset(body, 10, 10).click().perform()
            logger.info("    操作: 触发背景安全点击 (触发活跃事件成功)")
        except Exception as e:
            logger.debug(f"    安全点击被跳过或未执行: {e}")

    def simulate_mouse_movement(self, driver: webdriver.Chrome):
        """模拟鼠标轨迹随机滑动"""
        try:
            actions = ActionChains(driver)
            body = driver.find_element(By.TAG_NAME, "body")
            actions.move_to_element(body)
            
            for _ in range(BrowsingConfig.NUM_MOUSE_MOVES_PER_OP):
                x_offset = random.randint(-150, 150)
                y_offset = random.randint(-150, 150)
                actions.move_by_offset(x_offset, y_offset)
                actions.pause(BrowsingConfig.SHORT_PAUSE_DURATION)
            
            actions.perform()
            logger.info("    操作: 模拟鼠标移动完成")
        except Exception as e:
            logger.debug(f"    模拟鼠标移动未完成: {e}")

    def simulate_scrolling(self, driver: webdriver.Chrome):
        """模拟页面上下自然平滑滚动"""
        try:
            # 缓慢向下滚动 500 像素，再滚回顶部
            driver.execute_script("window.scrollBy({top: 600, behavior: 'smooth'});")
            time.sleep(BrowsingConfig.SCROLL_PAUSE_DURATION)
            driver.execute_script("window.scrollTo({top: 0, behavior: 'smooth'});")
            time.sleep(BrowsingConfig.SCROLL_PAUSE_DURATION)
            logger.info("    操作: 模拟页面平滑滚动完成")
        except Exception as e:
            logger.debug(f"    模拟滚动未完成: {e}")

    def process_url_worker(self, url: str, index: int) -> Tuple[str, bool]:
        """单站点保活主流程"""
        logger.info(f"[{index + 1}] 开始保活访问: {url}")
        driver = self.create_driver()
        if not driver:
            return url, False

        try:
            driver.set_page_load_timeout(35)  # 页面加载超时阈值
            driver.get(url)
            
            # 等待 DOM 树基本加载
            WebDriverWait(driver, BrowsingConfig.WEBDRIVER_WAIT_TIMEOUT).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            logger.info(f"  ✓ 成功触达页面: {url}")

            # 模拟交互行为（安全点击、鼠标移动、滚动）
            operations = [self.simulate_safe_click, self.simulate_mouse_movement, self.simulate_scrolling]
            random.shuffle(operations)
            for op in operations[:BrowsingConfig.NUM_RANDOM_OPERATIONS]:
                op(driver)
                time.sleep(BrowsingConfig.ACTION_PAUSE_DURATION)

            # 保活停留，确保前端埋点、心跳 WebSocket 能够建立并触发
            time.sleep(2)
            logger.info(f"  ✓ 保活动作完成: {url}")
            return url, True

        except TimeoutException:
            logger.warning(f"  ⚠️ 加载超时 (冷启动可能较慢，但请求已发送): {url}")
            return url, True  # 即使超时，请求往往已经唤醒了宿主，通常也算保活成功
        except WebDriverException as e:
            logger.error(f"  ❌ 访问失败 '{url}': {e}")
            return url, False
        except Exception:
            logger.error(f"  ❌ 未知异常 '{url}':\n{traceback.format_exc()}")
            return url, False
        finally:
            if driver:
                try:
                    driver.quit()
                except Exception:
                    pass

def main():
    if len(sys.argv) not in [2, 3]:
        print("用法: python simulate_browsing.py <url_filename> [chrome_driver_path]")
        sys.exit(1)

    url_filename = sys.argv[1]
    chrome_driver_path = sys.argv[2] if len(sys.argv) == 3 else None

    if not os.path.exists(url_filename):
        logger.error(f"URL 文件 '{url_filename}' 不存在。")
        sys.exit(1)

    simulator = BrowserSimulator(chrome_driver_path)

    if not simulator.remove_duplicates_and_empty_lines_from_file(url_filename):
        logger.error("文件预处理失败，任务终止。")
        sys.exit(1)

    try:
        with open(url_filename, 'r', encoding='utf-8') as file:
            urls = [line.strip() for line in file if line.strip()]
        if not urls:
            logger.info(f"文件 '{url_filename}' 内没有需要保活的 URL。")
            sys.exit(0)
        logger.info(f"共发现 {len(urls)} 个站点需要保活，启用 {BrowsingConfig.MAX_WORKERS} 个并发线程。")
    except Exception as e:
        logger.error(f"读取 URL 文件失败: {e}")
        sys.exit(1)

    success_count = 0
    fail_count = 0

    with ThreadPoolExecutor(max_workers=BrowsingConfig.MAX_WORKERS) as executor:
        future_to_url = {
            executor.submit(simulator.process_url_worker, url, i): url 
            for i, url in enumerate(urls)
        }
        
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                _, success = future.result()
                if success:
                    success_count += 1
                else:
                    fail_count += 1
            except Exception as exc:
                logger.error(f"URL '{url}' 产生未捕获异常: {exc}")
                fail_count += 1

    logger.info("=================================")
    logger.info(f"保活任务执行完毕！")
    logger.info(f"目标总数: {len(urls)} | 成功唤醒: {success_count} | 唤醒失败: {fail_count}")
    logger.info("=================================")

if __name__ == "__main__":
    main()
