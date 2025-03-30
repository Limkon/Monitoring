import os
import sys
import tempfile
import shutil
import re
import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException, MoveTargetOutOfBoundsException, InvalidArgumentException, WebDriverException
import traceback

def remove_duplicates_and_empty_lines_from_file(filename):
    lines_seen = set()
    output_lines = []

    with open(filename, 'r') as file:
        for line in file:
            line = line.strip()
            if line and line not in lines_seen and re.match(r'^https?://', line):
                lines_seen.add(line)
                output_lines.append(line)

    temp_filename = tempfile.mktemp()
    with open(temp_filename, 'w') as file:
        file.write('\n'.join(output_lines))

    shutil.move(temp_filename, filename)
    print("去重、去空行操作完成并已将结果保存到原始文件中。")

def process_url(url):
    # 配置 Chrome 选项
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1200")
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--allow-insecure-localhost")
    chrome_options.add_argument("--ignore-ssl-errors")

    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(5)

    try:
        # 验证并修复 URL
        url = url.strip()
        if not re.match(r'^https?://', url):
            url = 'https://' + url
        print(f"尝试加载 URL: {url}")

        # 加载 URL 并忽略 SSL 错误
        ssl_error = False
        try:
            driver.get(url)
            print(f"成功打开网页: {url}")
        except WebDriverException as e:
            if "net::ERR_SSL_PROTOCOL_ERROR" in str(e):
                print(f"SSL 协议错误，但尝试继续操作 {url}: {e}")
                ssl_error = True
            else:
                print(f"其他 WebDriver 错误，无法加载 {url}: {e}")
                return  # 其他错误直接跳过

        # 检查页面是否可用
        try:
            ready_state = driver.execute_script("return document.readyState;")
            if ready_state == "complete" or not ssl_error:
                print(f"页面状态: {ready_state}, 继续操作")
            else:
                print(f"页面状态: {ready_state}, 可能无法操作，但尝试继续")
        except Exception:
            print("无法检查页面状态，尝试继续操作")

        # 获取实际窗口尺寸
        try:
            window_width = driver.execute_script("return window.innerWidth;")
            window_height = driver.execute_script("return window.innerHeight;")
            print(f"窗口尺寸: {window_width}x{window_height}")
        except Exception:
            window_width, window_height = 1920, 1200  # 默认值
            print("无法获取窗口尺寸，使用默认值 1920x1200")

        for _ in range(3):
            operation = random.randint(1, 3)

            if operation == 1:  # 模拟点击
                try:
                    element = driver.find_element("tag name", "body")
                    body_size = element.size
                    body_location = element.location
                    
                    x = random.randint(0, window_width - 1)
                    y = random.randint(0, window_height - 1)
                    
                    offset_x = x - body_location['x']
                    offset_y = y - body_location['y']
                    
                    offset_x = max(0, min(offset_x, body_size['width'] - 1))
                    offset_y = max(0, min(offset_y, body_size['height'] - 1))
                    
                    driver.execute_script("arguments[0].scrollIntoView(true);", element)
                    ActionChains(driver).move_to_element_with_offset(element, offset_x, offset_y).click().perform()
                    print(f"模拟点击成功：坐标({x}, {y}), 偏移量({offset_x}, {offset_y})")
                    time.sleep(0.5)
                except (NoSuchElementException, MoveTargetOutOfBoundsException) as e:
                    print(f"点击失败: {e}")
                    continue

            elif operation == 2:  # 模拟移动鼠标
                actions = ActionChains(driver)
                try:
                    current_x = window_width // 2
                    current_y = window_height // 2
                    
                    for _ in range(3):
                        x_offset = random.randint(-50, 50)
                        y_offset = random.randint(-50, 50)
                        new_x = current_x + x_offset
                        new_y = current_y + y_offset
                        
                        new_x = max(0, min(new_x, window_width - 1))
                        new_y = max(0, min(new_y, window_height - 1))
                        x_offset = new_x - current_x
                        y_offset = new_y - current_y
                        
                        actions.move_by_offset(x_offset, y_offset)
                        print(f"模拟鼠标移动成功：偏移量({x_offset}, {y_offset})")
                        current_x, current_y = new_x, new_y
                        time.sleep(0.5)
                    actions.perform()
                except MoveTargetOutOfBoundsException as e:
                    print(f"鼠标移动失败: {e}")
                    continue

            else:  # 模拟滚动网页
                try:
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    driver.execute_script("window.scrollTo(0, 0);")
                    print("模拟滚动到页面底部和顶部")
                    time.sleep(1)
                except Exception as e:
                    print(f"滚动失败: {e}")

        try:
            driver.refresh()
            print("刷新网页")
            time.sleep(1)
        except Exception as e:
            print(f"刷新失败: {e}")

    except InvalidArgumentException as e:
        print(f"无效的 URL 参数: {url}, 错误: {e}")
    except Exception as e:
        print(f"执行操作时出现异常: {str(e)}")
        traceback.print_exc()

    finally:
        driver.quit()
        print("浏览器已关闭")

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
