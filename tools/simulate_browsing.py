import os
import sys
import tempfile
import shutil
import re
import time
import random
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException

def remove_duplicates_and_empty_lines_from_file(filename):
    lines_seen = set()  # 用于跟踪已经出现过的行
    output_lines = []  # 用于存储去重后的行

    with open(filename, 'r') as file:
        for line in file:
            line = line.strip()  # 去除行首尾的空白字符
            line = re.sub(r'^[^a-zA-Z0-9]+|[^a-zA-Z0-9]+$', '', line)  # 去除行首尾的非字母数字字符

            if line:  # 检查是否是空行，如果不是空行才进行去重操作
                if line not in lines_seen:  # 如果行不在已出现的行集合中
                    lines_seen.add(line)  # 将行添加到已出现的行集合中
                    output_lines.append(line)  # 将行添加到输出列表中

    temp_filename = tempfile.mktemp()  # 创建一个临时文件
    with open(temp_filename, 'w') as file:
        file.write('\n'.join(output_lines))  # 将去重后的结果写入临时文件中

    shutil.move(temp_filename, filename)  # 将临时文件移动到原始文件的位置，覆盖原始文件

    print("去重、去空行和去除非字母数字字符操作完成并已将结果保存到原始文件中。")

def process_url(url):
    driver = webdriver.Chrome()  # 如果需要指定ChromeDriver路径，请使用参数executable_path

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
        import traceback
        traceback.print_exc()

    finally:
        driver.quit()
        print("浏览器已关闭")

        output_name = f"URL_{url}"
        os.environ[output_name] = url

# 获取命令行参数
if len(sys.argv) != 2:
    print("Usage: python script.py <filename>")
else:
    filename = sys.argv[1]  # 获取文件名参数
    remove_duplicates_and_empty_lines_from_file(filename)  # 调用去重函数，传入文件名参数

    with open(filename, 'r') as file:
        urls = file.readlines()

    for url in urls:
        url = url.strip()
        if url:
            process_url(url)  # 调用模拟浏览函数，传入URL参数
