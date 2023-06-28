import time
import random
import concurrent.futures
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException
import os

def process_url(url):
    # 创建浏览器实例
    driver = webdriver.Chrome()

    try:
        # 打开网页
        driver.get(url)
        print(f"成功打开网页: {url}")

        # 最大化窗口
        driver.maximize_window()
        print("窗口已最大化")

        window_size = driver.get_window_size()  # 获取窗口大小

        # 模拟随机点击
        for _ in range(5):
            try:
                # 随机生成点击位置的坐标
                x = random.randint(0, window_size['width'])
                y = random.randint(0, window_size['height'])
                # 执行点击操作
                element = driver.find_element("tag name", "body")
                ActionChains(driver).move_to_element_with_offset(element, x, y).click().perform()
                print(f"模拟点击成功：坐标({x}, {y})")
                time.sleep(1)
            except NoSuchElementException:
                print("无法找到元素")

        # 模拟随机移动鼠标
        actions = ActionChains(driver)
        for _ in range(5):
            x_offset = random.randint(-100, 100)
            y_offset = random.randint(-100, 100)
            actions.move_by_offset(x_offset, y_offset)
            print(f"模拟鼠标移动成功：偏移量({x_offset}, {y_offset})")
            time.sleep(1)
        actions.perform()

        # 模拟滚动网页
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);"
                              "window.scrollTo(0, 0);")
        print("模拟滚动到页面底部和顶部")
        time.sleep(2)

    except Exception as e:
        print(f"执行操作时出现异常: {str(e)}")

    finally:
        # 关闭浏览器
        driver.quit()
        print("浏览器已关闭")

        # 设置输出值为成功打开的网页URL
        output_name = f"URL_{url}"
        os.environ[output_name] = url

def simulate_operations(filename):
    try:
        # 读取URL文件
        with open(filename, 'r') as file:
            urls = file.readlines()

        # 创建线程池，最大线程数为10（可根据实际情况调整）
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            # 提交每个URL的处理任务到线程池
            futures = [executor.submit(process_url, url.strip()) for url in urls]

            # 等待所有任务完成
            concurrent.futures.wait(futures)

        # 保存输出到环境文件
        with open("outputs.env", "w") as env_file:
            for url in urls:
                output_name = f"URL_{url.strip()}"
                env_file.write(f"{output_name}={os.environ.get(output_name, '')}\n")

    except FileNotFoundError:
        print("URL文件未找到")

# 在主程序中调用 simulate_operations() 方法
if __name__ == '__main__':
    import sys
    filename = sys.argv[1] if len(sys.argv) > 1 else "urls.txt"
    simulate_operations(filename)
