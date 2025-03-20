import os
import sys
import tempfile
import shutil
import re
import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException
import traceback

def remove_duplicates_and_empty_lines_from_file(filename):
    lines_seen = set()
    output_lines = []

    with open(filename, 'r') as file:
        for line in file:
            line = line.strip()
            line = re.sub(r'^[^a-zA-Z0-9]+|[^a-zA-Z0-9]+$', '', line)
            if line and line not in lines_seen:
                lines_seen.add(line)
                output_lines.append(line)

    temp_filename = tempfile.mktemp()
    with open(temp_filename, 'w') as file:
        file.write('\n'.join(output_lines))

    shutil.move(temp_filename, filename)
    print("去重、去空行和去除非字母数字字符操作完成并已将结果保存到原始文件中。")

def process_url(url):
    # 配置 Chrome 选项
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # 无头模式，适合 CI 环境
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    # 使用 ChromeDriver（需在 GitHub Actions 中安装）
    driver = webdriver.Chrome(options=chrome_options)

    try:
        driver.get(url)
        print(f"成功打开网页: {url}")
        driver.maximize_window()
        print("窗口已最大化")

        window_size = driver.get_window_size()

        for _ in range(5):
            operation = random.randint(1, 3)

            if operation == 1:  # 模拟点击
                try:
                    x = random.randint(0, window_size['width'] - 1)
                    y = random.randint(0, window_size['height'] - 1)
                    element = driver.find_element("tag name", "body")
                    ActionChains(driver).move_to_element_with_offset(element, x, y).click().perform()
                    print(f"模拟点击成功：坐标({x}, {y})")
                    time.sleep(1)
                except NoSuchElementException:
                    print("无法找到元素")
                    continue

            elif operation == 2:  # 模拟移动鼠标
                actions = ActionChains(driver)
                for _ in range(5):
                    x_offset = random.randint(-100, 100)
                    y_offset = random.randint(-100, 100)
                    actions.move_by_offset(x_offset, y_offset)
                    print(f"模拟鼠标移动成功：偏移量({x_offset}, {y_offset})")
                    time.sleep(1)
                actions.perform()

            else:  # 模拟滚动网页
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                driver.execute_script("window.scrollTo(0, 0);")
                print("模拟滚动到页面底部和顶部")
                time.sleep(2)

        driver.refresh()
        print("刷新网页")
        time.sleep(2)
        time.sleep(15)

    except Exception as e:
        print(f"执行操作时出现异常: {str(e)}")
        traceback.print_exc()

    finally:
        driver.quit()
        print("浏览器已关闭")

        # 在 GitHub Actions 中设置环境变量
        output_name = f"URL_{url.replace('https://', '').replace('/', '_')}"
        with open(os.environ["GITHUB_ENV"], "a") as env_file:
            env_file.write(f"{output_name}={url}\n")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <filename>")
        sys.exit(1)

    filename = sys.argv[1]
    remove_duplicates_and_empty_lines_from_file(filename)

    with open(filename, 'r') as file:
        urls = file.readlines()

    for url in urls:
        url = url.strip()
        if url:
            process_url(url)
