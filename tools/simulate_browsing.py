import time
import random
from selenium import webdriver

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
                print(f"成功打开网页: {url}")

                # 最大化窗口
                driver.maximize_window()
                print("窗口已最大化")

                # 模拟随机点击
                for _ in range(5):
                    # 随机生成点击位置的坐标
                    x = random.randint(0, driver.get_window_size()['width'])
                    y = random.randint(0, driver.get_window_size()['height'])
                    # 执行JavaScript代码模拟点击
                    driver.execute_script(f"window.scrollTo({x}, {y});")
                    print(f"模拟点击成功：坐标({x}, {y})")
                    time.sleep(1)

            except Exception as e:
                print(f"打开网页时出现异常: {str(e)}")

    except FileNotFoundError:
        print("URL文件未找到")

    finally:
        # 关闭浏览器
        driver.quit()
        print("浏览器已关闭")

# 在主程序中调用 simulate_operations() 方法
if __name__ == '__main__':
    import sys
    filename = sys.argv[1] if len(sys.argv) > 1 else "urls.txt"
    simulate_operations(filename)
