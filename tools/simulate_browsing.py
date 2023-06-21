import time
import random
import argparse
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By

def simulate_operations(url_file):
    # 创建浏览器实例
    driver = webdriver.Chrome()

    # 读取URL地址文件
    with open(url_file, 'r') as file:
        urls = file.readlines()

    # 循环处理每个网址
    for url in urls:
        url = url.strip()  # 去除换行符和空格

        # 打开网页
        driver.get(url)

        # 最大化窗口
        driver.maximize_window()

        # 模拟鼠标点击
        element = driver.find_element(By.XPATH, "//a[@id='my-link']")
        ActionChains(driver).move_to_element(element).click().perform()

        # 模拟随机移动
        actions = ActionChains(driver)
        actions.move_to_element_with_offset(element, 10, 10)
        for _ in range(5):
            actions.move_by_offset(random.randint(-50, 50), random.randint(-50, 50))
            actions.perform()
            time.sleep(1)

        # 模拟滚动网页
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(2)

    # 关闭浏览器
    driver.quit()

# 解析命令行参数
parser = argparse.ArgumentParser(description='Simulate browsing operations')
parser.add_argument('file', help='URL addresses file name')
args = parser.parse_args()

# 以命令行参数中的文件名调用函数
filename = args.file
simulate_operations(filename)
