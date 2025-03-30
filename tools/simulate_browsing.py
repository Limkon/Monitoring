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
from selenium.common.exceptions import NoSuchElementException, MoveTargetOutOfBoundsException
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
    chrome_options.add_argument("--headless")  # 无头模式
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")  # 明确设置窗口大小

    # 使用 ChromeDriver
    driver = webdriver.Chrome(options=chrome_options)

    try:
        driver.get(url)
        print(f"成功打开网页: {url}")

        # 获取实际窗口尺寸
        window_width = driver.execute_script("return window.innerWidth;")
        window_height = driver.execute_script("return window.innerHeight;")
        print(f"窗口尺寸: {window_width}x{window_height}")

        for _ in range(5):
            operation = random.randint(1, 3)

            if operation == 1:  # 模拟点击
                try:
                    element = driver.find_element("tag name", "body")
                    body_size = element.size  # {'width': ..., 'height': ...}
                    body_location = element.location  # {'x': ..., 'y': ...}

                    # 限制点击坐标在 body 元素范围内
                    x = random.randint(0, min(body_size['width'], window_width) - 1)
                    y = random.randint(0, min(body_size['height'], window_height) - 1)
                    
                    # 滚动到 body 确保可见（无头模式下可能无需此步）
                    driver.execute_script("arguments[0].scrollIntoView(true);", element)
                    ActionChains(driver).move_to_element_with_offset(element, x, y).click().perform()
                    print(f"模拟点击成功：坐标({x}, {y})")
                    time.sleep(1)
                except (NoSuchElementException, MoveTargetOutOfBoundsException) as e:
                    print(f"点击失败: {e}")
                    continue

            elif operation == 2:  # 模拟移动鼠标
                actions = ActionChains(driver)
                try:
                    # 获取当前鼠标位置（初始为窗口中心）
                    current_x = window_width // 2
                    current_y = window_height // 2
                    
                    for _ in range(5):
                        # 限制偏移量，避免超出窗口
                        x_offset = random.randint(-50, 50)
                        y_offset = random.randint(-50, 50)
                        new_x = current_x + x_offset
                        new_y = current_y + y_offset
                        
                        # 确保新位置在窗口内
                        new_x = max(0, min(new_x, window_width - 1))
                        new_y = max(0, min(new_y, window_height - 1))
                        x_offset = new_x - current_x
                        y_offset = new_y - current_y
                        
                        actions.move_by_offset(x_offset, y_offset)
                        print(f"模拟鼠标移动成功：偏移量({x_offset}, {y_offset})")
                        current_x, current_y = new_x, new_y
                        time.sleep(1)
                    actions.perform()
                except MoveTargetOutOfBoundsException as e:
                    print(f"鼠标移动失败: {e}")
                    continue

            else:  # 模拟滚动网页
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)
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
