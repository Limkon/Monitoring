from selenium import webdriver
import sys

try:
    # 从命令行参数获取要访问的 URL
    url = sys.argv[1]

    # 创建浏览器驱动，例如使用 Chrome 浏览器
    driver = webdriver.Chrome()

    # 打开网页
    driver.get(url)

    # 执行你想要的点击操作，例如点击一个按钮
    button = driver.find_element_by_id('my-button')
    button.click()

    # 关闭浏览器
    driver.quit()
except Exception as e:
    print(e)
finally:
    # 不管是否发生异常都会执行的代码
    pass
