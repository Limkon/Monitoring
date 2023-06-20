from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
import random
import sys

try:
    if len(sys.argv) < 2:
        raise ValueError("请提供要访问的 URL 参数")

    # 从命令行参数获取要访问的 URL
    url = sys.argv[1]

    # 创建浏览器驱动，例如使用 Chrome 浏览器
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # 以无头模式运行，可选
    driver = webdriver.Chrome(options=options)

    # 打开网页
    driver.get(url)
    print("打开网页:", url)
   
except Exception as e:
    print(f"发生错误：{str(e)}")

finally:
    # 不管是否发生异常都会执行的代码
    driver.quit()
    print("浏览器已关闭")
