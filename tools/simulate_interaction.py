from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import random
import sys

# 从命令行参数中获取存储URL地址的文件名
url_file = sys.argv[1]

# 创建 Chrome WebDriver 对象
driver = webdriver.Chrome()

# 从文件中逐行读取URL地址
with open(url_file, "r") as file:
    urls = file.readlines()

# 遍历URL进行操作
for url in urls:
    # 去除行末的换行符
    url = url.strip()

    # 初始化完成标志
    is_complete = False

    # 尝试执行操作，直到完成
    while not is_complete:
        try:
            # 打开网页
            driver.get(url)

            # 随机点击元素
            elements = driver.find_elements_by_tag_name("a")
            if elements:
                random_element = random.choice(elements)
                random_element.click()
                print("执行点击操作")

            # 随机移动鼠标
            actions = ActionChains(driver)
            actions.move_to_element(random_element).perform()
            print("执行移动鼠标操作")

            # 随机滚动页面
            scroll_distance = random.randint(200, 500)
            actions = ActionChains(driver)
            actions.send_keys(Keys.PAGE_DOWN * scroll_distance).perform()
            print("执行滚动页面操作")

            is_complete = True  # 操作成功完成

        except Exception as e:
            # 捕获异常并打印错误信息
            print(f"操作失败: {e}")
            print("重新尝试操作...")
    
    print(f"操作的URL: {url}")
    print("")

# 关闭浏览器窗口
driver.quit()
