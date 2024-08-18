import time
import random
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException
import os

def process_url(url):
    driver = webdriver.Chrome()

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

    finally:
        driver.quit()
        print("浏览器已关闭")

        output_name = f"URL_{url}"
        os.environ[output_name] = url
