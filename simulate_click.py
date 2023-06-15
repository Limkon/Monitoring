from selenium import webdriver
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

    # 执行你想要的点击操作，例如点击一个按钮
    button = driver.find_element_by_id('my-button')
    button.click()

    # 关闭浏览器
    driver.quit()

except Exception as e:
    print(f"发生错误：{str(e)}")

finally:
    # 不管是否发生异常都会执行的代码
    pass
