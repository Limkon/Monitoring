import time
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By

# 创建浏览器实例
driver = webdriver.Chrome()

# 打开网页
driver.get("https://www.example.com")

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
