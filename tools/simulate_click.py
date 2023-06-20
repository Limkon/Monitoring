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

    # 获取页面上的所有可点击元素
    clickable_elements = driver.find_elements(By.XPATH, '//*[@onclick]')

    # 如果存在可点击元素，则执行随机点击和移动操作
    if clickable_elements:
        # 随机选择一个可点击元素
        random_element = random.choice(clickable_elements)

        # 获取元素的位置和尺寸
        element_location = random_element.location
        element_size = random_element.size

        # 计算点击位置的偏移量
        click_offset_x = random.randint(0, element_size['width'])
        click_offset_y = random.randint(0, element_size['height'])

        # 计算移动位置的偏移量
        move_offset_x = random.randint(-element_location['x'], element_size['width'])
        move_offset_y = random.randint(-element_location['y'], element_size['height'])

        # 创建 ActionChains 对象，执行随机点击和移动操作
        actions = ActionChains(driver)
        actions.move_to_element(random_element)
        actions.move_by_offset(move_offset_x, move_offset_y)
        actions.click(random_element).perform()
        print("执行点击和移动操作")

    # 模拟滚动页面
    scroll_amount = random.randint(100, 500)
    driver.execute_script(f"window.scrollBy(0, {scroll_amount})")
    print("执行页面滚动操作")

except Exception as e:
    print(f"发生错误：{str(e)}")

finally:
    # 不管是否发生异常都会执行的代码
    driver.quit()
    print("浏览器已关闭")
