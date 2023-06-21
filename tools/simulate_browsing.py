import time
import random
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
import logging

# 创建日志记录器
logging.basicConfig(filename='browsing.log', level=logging.INFO)

def simulate_operations(filename):
    # 创建浏览器实例
    driver = webdriver.Chrome()

    try:
        # 读取URL文件
        with open(filename, 'r') as file:
            urls = file.readlines()

        # 遍历URL列表
        for url in urls:
            url = url.strip()  # 移除换行符和空格

            try:
                # 打开网页
                driver.get(url)
                logging.info(f"成功打开网页: {url}")

                # 最大化窗口
                driver.maximize_window()
                logging.info("窗口已最大化")

                # 模拟操作
                element = driver.find_element(By.XPATH, "//a[@id='my-link']")
                ActionChains(driver).move_to_element(element).click().perform()
                logging.info("模拟鼠标点击成功")

                # 模拟随机移动
                actions = ActionChains(driver)
                actions.move_to_element_with_offset(element, 10, 10)
                for _ in range(5):
                    actions.move_by_offset(random.randint(-50, 50), random.randint(-50, 50))
                    actions.perform()
                    time.sleep(1)
                logging.info("模拟随机移动成功")

                # 模拟滚动网页
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(2)
                logging.info("模拟滚动网页成功")

            except Exception as e:
                logging.error(f"执行操作时出现异常: {str(e)}")

    except FileNotFoundError:
        logging.error("URL文件未找到")

    finally:
        # 关闭浏览器
        driver.quit()
        logging.info("浏览器已关闭")

# 在主程序中调用 simulate_operations() 方法
if __name__ == '__main__':
    import sys
    filename = sys.argv[1] if len(sys.argv) > 1 else "urls.txt"
    simulate_operations(filename)
