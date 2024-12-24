# -*- coding: utf-8 -*-
import os
import time
import logging
import random
from os import path
from io import StringIO
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    WebDriverException,
)
import shutil

# 配置日志
logger = logging.getLogger()
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

formatter = logging.Formatter(
    "[%(asctime)s %(levelname)s] %(message)s", datefmt="%H:%M:%S"
)

console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# 检查环境变量
missing_configs = []

username_env = os.getenv("LINUXDO_USERNAME")
password_env = os.getenv("LINUXDO_PASSWORD")

if not username_env:
    missing_configs.append("环境变量 'LINUXDO_USERNAME' 未设置或为空")
if not password_env:
    missing_configs.append("环境变量 'LINUXDO_PASSWORD' 未设置或为空")

if missing_configs:
    logging.error(f"缺少必要配置: {', '.join(missing_configs)}，请在环境变量中设置。")
    exit(1)

USERNAME = [line.strip() for line in username_env.splitlines() if line.strip()]
PASSWORD = [line.strip() for line in password_env.splitlines() if line.strip()]
SCROLL_DURATION = int(os.getenv("SCROLL_DURATION", 0))
VIEW_COUNT = int(os.getenv("VIEW_COUNT", 1000))
HOME_URL = os.getenv("HOME_URL", "https://linux.do/")
CONNECT_URL = os.getenv("CONNECT_URL", "https://connect.linux.do/")

browse_count = 0
connect_info = ""
like_count = 0
account_info = []

user_count = len(USERNAME)

if user_count != len(PASSWORD):
    logging.error("用户名和密码的数量不一致，请检查环境变量设置。")
    exit(1)

logging.info(f"共找到 {user_count} 个账户")


def load_send():
    cur_path = path.abspath(path.dirname(__file__))
    if path.exists(cur_path + "/notify.py"):
        try:
            from notify import send
            return send
        except ImportError:
            return False
    else:
        return False


class LinuxDoBrowser:
    def __init__(self) -> None:
        logging.info("启动 Selenium")

        global chrome_options
        chrome_options = webdriver.ChromeOptions()

        # 青龙面板特定的 Chrome 选项
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument('--headless=new')  # 使用新的 headless 模式
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument('--allow-running-insecure-content')
        chrome_options.add_argument("--disable-popup-blocking")

        # 添加 user-agent
        chrome_options.add_argument(
            '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

        # 禁用自动化标志
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        # 设置页面加载策略
        chrome_options.page_load_strategy = 'normal'

        # 检查 chromedriver 路径
        global chromedriver_path
        chromedriver_path = shutil.which("chromedriver")

        if not chromedriver_path:
            logging.error("chromedriver 未找到，请确保已安装并配置正确的路径。")
            exit(1)

        self.driver = None

    def create_driver(self):
        try:
            service = Service(chromedriver_path)
            self.driver = webdriver.Chrome(service=service, options=chrome_options)

            # 删除 navigator.webdriver 标志
            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    })
                '''
            })

            # 设置页面加载超时
            self.driver.set_page_load_timeout(30)
            self.driver.implicitly_wait(10)

            return True

        except Exception as e:
            logging.error(f"创建 WebDriver 失败: {e}")
            return False

    def simulate_typing(self, element, text, typing_speed=0.1, random_delay=True):
        for char in text:
            element.send_keys(char)
            if random_delay:
                time.sleep(typing_speed + random.uniform(0, 0.1))
            else:
                time.sleep(typing_speed)

    def login(self) -> bool:
        try:
            logging.info(f"--- 开始尝试登录：{self.username}---")

            # 先等待页面加载完成
            WebDriverWait(self.driver, 20).until(
                lambda driver: driver.execute_script('return document.readyState') == 'complete'
            )

            # 确保在点击之前页面已完全加载
            time.sleep(3)

            try:
                login_button = WebDriverWait(self.driver, 20).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, ".login-button .d-button-label"))
                )
                self.driver.execute_script("arguments[0].click();", login_button)
            except:
                logging.info("尝试备用登录按钮选择器")
                login_button = WebDriverWait(self.driver, 20).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button.login-button"))
                )
                self.driver.execute_script("arguments[0].click();", login_button)

            # 等待登录表单出现
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.ID, "login-form"))
            )

            # 输入用户名
            username_field = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.ID, "login-account-name"))
            )
            username_field.clear()
            time.sleep(1)
            self.simulate_typing(username_field, self.username)

            # 输入密码
            password_field = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.ID, "login-account-password"))
            )
            password_field.clear()
            time.sleep(1)
            self.simulate_typing(password_field, self.password)

            # 提交登录
            submit_button = WebDriverWait(self.driver, 20).until(
                EC.element_to_be_clickable((By.ID, "login-button"))
            )
            time.sleep(1)
            self.driver.execute_script("arguments[0].click();", submit_button)

            # 验证登录结果
            try:
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#current-user"))
                )
                logging.info("登录成功")
                return True
            except TimeoutException:
                error_element = self.driver.find_elements(By.CSS_SELECTOR, "#modal-alert.alert-error")
                if error_element:
                    logging.error(f"登录失败：{error_element[0].text}")
                else:
                    logging.error("登录失败：无法验证登录状态")
                return False

        except Exception as e:
            logging.error(f"登录过程发生错误：{str(e)}")
            # 保存截图以便调试
            try:
                self.driver.save_screenshot("login_error.png")
                logging.info("已保存错误截图到 login_error.png")
            except:
                pass
            return False

    def load_all_topics(self):
        end_time = time.time() + SCROLL_DURATION
        actions = ActionChains(self.driver)

        while time.time() < end_time:
            actions.scroll_by_amount(0, 500).perform()
            time.sleep(0.1)

        logging.info("页面滚动完成，已停止加载更多帖子")

    def click_topic(self):
        try:
            logging.info("--- 开始滚动页面加载更多帖子 ---")
            self.load_all_topics()
            topics = self.driver.find_elements(By.CSS_SELECTOR, "#list-area .title")
            total_topics = len(topics)
            logging.info(f"共找到 {total_topics} 个帖子")

            logging.info("--- 开始浏览帖子 ---")
            global browse_count

            for idx, topic in enumerate(topics):
                try:
                    parent_element = topic.find_element(By.XPATH, "./ancestor::tr")

                    is_pinned = parent_element.find_elements(
                        By.CSS_SELECTOR, ".topic-statuses .pinned"
                    )

                    if is_pinned:
                        logging.info(f"跳过置顶的帖子：{topic.text.strip()}")
                        continue

                    views_element = parent_element.find_element(
                        By.CSS_SELECTOR, ".num.views .number"
                    )
                    views_title = views_element.get_attribute("title")

                    if "此话题已被浏览 " in views_title and " 次" in views_title:
                        views_count_str = views_title.split("此话题已被浏览 ")[1].split(" 次")[0]
                        views_count = int(views_count_str.replace(",", ""))
                    else:
                        logging.warning(f"无法解析浏览次数，跳过该帖子: {views_title}")
                        continue

                    article_title = topic.text.strip()
                    logging.info(f"打开第 {idx + 1}/{total_topics} 个帖子 ：{article_title}")
                    article_url = topic.get_attribute("href")

                    try:
                        self.driver.execute_script("window.open('');")
                        self.driver.switch_to.window(self.driver.window_handles[-1])

                        browse_start_time = time.time()
                        self.driver.set_page_load_timeout(10)  # 设置页面加载超时时间
                        try:
                            self.driver.get(article_url)
                        except TimeoutException:
                            logging.warning(f"加载帖子超时: {article_title}")
                            raise  # 重新抛出异常，让外层catch处理

                        browse_count += 1
                        start_time = time.time()
                        if views_count > VIEW_COUNT:
                            logging.info(f"📈 当前帖子浏览量为{views_count} 大于设定值 {VIEW_COUNT}，🥳 开始进行点赞操作")
                            self.click_like()

                        scroll_duration = random.uniform(5, 10)
                        try:
                            while time.time() - start_time < scroll_duration:
                                self.driver.execute_script(
                                    "window.scrollBy(0, window.innerHeight);"
                                )
                                time.sleep(1)
                        except Exception as e:
                            logging.warning(f"在滚动过程中发生错误: {e}")

                        browse_end_time = time.time()
                        total_browse_time = browse_end_time - browse_start_time
                        logging.info(f"浏览该帖子时间: {total_browse_time:.2f}秒")

                    except Exception as e:
                        logging.error(f"处理帖子时发生错误: {e}")

                    finally:
                        # 确保无论如何都会关闭新打开的标签页
                        if len(self.driver.window_handles) > 1:
                            self.driver.close()
                            self.driver.switch_to.window(self.driver.window_handles[0])
                        logging.info(f"已关闭第 {idx + 1}/{total_topics} 个帖子 ： {article_title}")

                except Exception as e:
                    logging.error(f"处理帖子 {idx + 1} 时发生错误: {e}")
                    continue  # 继续处理下一个帖子

            logging.info("所有帖子处理完毕")

        except Exception as e:
            logging.error(f"click_topic 方法发生错误: {e}")

    def run(self):
        """主运行函数"""
        global browse_count
        global connect_info
        global like_count

        for i in range(user_count):
            start_time = time.time()
            self.username = USERNAME[i]
            self.password = PASSWORD[i]

            logging.info(f"▶️▶️▶️  开始执行第{i + 1}个账号: {self.username}")

            try:
                # 初始化 WebDriver
                self.driver = webdriver.Chrome(
                    service=Service(chromedriver_path), options=chrome_options
                )
                logging.info("导航到 LINUX DO 首页")
                self.driver.get(HOME_URL)

                # 登录
                if not self.login():
                    logging.error(f"{self.username} 登录失败")
                    continue

                # 浏览帖子
                self.click_topic()
                logging.info(f"🎉 恭喜：{self.username}，帖子浏览全部完成")
                # 获取 Connect 信息
                self.print_connect_info()

                # 登出
                self.logout()

            except WebDriverException as e:
                logging.error(f"WebDriver 初始化失败: {e}")
                logging.info("请尝试重新搭建青龙面板或换个机器运行, 更新Chrome和chromedriver")
                exit(1)
            except Exception as e:
                logging.error(f"运行过程中出错: {e}")
            finally:
                if self.driver is not None:
                    self.driver.quit()

            end_time = time.time()
            spend_time = int((end_time - start_time) // 60)

            # 记录账户信息
            account_info.append(
                {
                    "username": self.username,
                    "browse_count": browse_count,
                    "like_count": like_count,
                    "spend_time": spend_time,
                    "connect_info": connect_info,
                }
            )

            # 重置状态
            browse_count = 0
            like_count = 0
            connect_info = ""

        logging.info("所有账户处理完毕")
        # 构建推送信息
        summary = ""
        for info in account_info:
            summary += (
                f"用户：{info['username']}\n\n"
                f"本次共浏览 {info['browse_count']} 个帖子\n"
                f"共点赞{info['like_count']} 个帖子\n"
                f"共用时 {info['spend_time']} 分钟\n"
                f"{info['connect_info']}\n\n"
            )
        send = load_send()
        if callable(send):
            send("Linux.do浏览帖子", summary)
        else:
            print("\n通知推送失败")

    def click_like(self):
        try:
            global like_count
            like_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, ".btn-toggle-reaction-like")
                )
            )

            if "移除此赞" in like_button.get_attribute("title"):
                logging.info("该帖子已点赞，跳过点赞操作。")
            else:
                self.driver.execute_script("arguments[0].click();", like_button)
                like_count += 1
                logging.info("点赞帖子成功")

        except TimeoutException:
            logging.error("点赞操作失败：点赞按钮定位超时")
        except WebDriverException as e:
            logging.error(f"点赞操作失败: {e}")
        except Exception as e:
            logging.error(f"未知错误导致点赞操作失败: {e}")

    def print_connect_info(self):
        try:
            self.driver.execute_script("window.open('');")
            self.driver.switch_to.window(self.driver.window_handles[-1])
            logging.info("导航到LINUX DO Connect页面")
            self.driver.get(CONNECT_URL)

            global connect_info

            rows = self.driver.find_elements(By.CSS_SELECTOR, "table tr")
            info = []

            for row in rows:
                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) >= 3:
                    project = cells[0].text.strip()
                    current = cells[1].text.strip()
                    requirement = cells[2].text.strip()
                    info.append([project, current, requirement])

            column_widths = [24, 22, 16]

            def calculate_content_width(content):
                return sum(2 if ord(char) > 127 else 1 for char in content)

            def format_cell(content, width, alignment="left"):
                content_length = calculate_content_width(content)
                padding = width - content_length
                if padding > 0:
                    if alignment == "left":
                        return content + " " * padding
                    elif alignment == "right":
                        return " " * padding + content
                    elif alignment == "center":
                        left_padding = padding // 2
                        right_padding = padding - left_padding
                        return " " * left_padding + content + " " * right_padding
                else:
                    return content[:width]

            def build_row(cells):
                return "| " + " | ".join(cells) + " |"

            def build_separator():
                return "+" + "+".join(["-" * (width + 2) for width in column_widths]) + "+"

            formatted_info = [
                build_row(
                    [
                        format_cell(row[0], column_widths[0]),
                        format_cell(row[1], column_widths[1], "center"),
                        format_cell(row[2], column_widths[2], "center"),
                    ]
                )
                for row in info
            ]

            header = build_row(
                [
                    format_cell("项目", column_widths[0]),
                    format_cell("当前", column_widths[1], "center"),
                    format_cell("要求", column_widths[2], "center"),
                ]
            )

            separator = build_separator()

            output = StringIO()
            output.write("在过去 💯 天内：\n")
            output.write(separator + "\n")
            output.write(header + "\n")
            output.write(separator.replace("-", "=") + "\n")
            output.write("\n".join(formatted_info) + "\n")
            output.write(separator + "\n")

            table_output = output.getvalue()
            output.close()

            print(table_output)

            connect_info = "\n在过去 💯 天内：\n" + "\n".join(
                [f"{row[0]}（{row[2]}）：{row[1]}" for row in info]
            )

        except Exception as e:
            logging.error(f"获取 Connect 信息时发生错误：{e}")
        finally:
            if len(self.driver.window_handles) > 1:
                self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[0])

    def logout(self):
        try:
            user_menu_button = self.driver.find_element(By.ID, "toggle-current-user")
            user_menu_button.click()

            profile_tab_button = WebDriverWait(self.driver, 20).until(
                EC.element_to_be_clickable((By.ID, "user-menu-button-profile"))
            )
            profile_tab_button.click()

            logout_button = WebDriverWait(self.driver, 20).until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "li.logout button.profile-tab-btn")
                )
            )
            logout_button.click()

            time.sleep(2)
            self.driver.refresh()

            elements = self.driver.find_elements(
                By.CSS_SELECTOR, ".header-buttons .login-button"
            )
            if elements:
                logging.info(f"{self.username}登出成功")
            else:
                logging.info(f"{self.username}登出失败")

        except (TimeoutException, NoSuchElementException) as e:
            logging.error(f"登出失败，可能由于元素未找到或超时: {e}")
        except Exception as e:
            logging.error(f"登出过程中发生错误: {e}")

    def run(self):
        global browse_count
        global connect_info
        global like_count

        for i in range(user_count):
            start_time = time.time()
            self.username = USERNAME[i]
            self.password = PASSWORD[i]

            logging.info(f"▶️▶️▶️  开始执行第{i + 1}个账号: {self.username}")

            try:
                if not self.create_driver():
                    logging.error("创建浏览器实例失败，跳过当前账号")
                    continue

                logging.info("导航到 LINUX DO 首页")
                self.driver.get(HOME_URL)

                if not self.login():
                    logging.error(f"{self.username} 登录失败")
                    continue

                self.click_topic()
                logging.info(f"🎉 恭喜：{self.username}，帖子浏览全部完成")
                self.print_connect_info()

                self.logout()

            except WebDriverException as e:
                logging.error(f"WebDriver 初始化失败: {e}")
                logging.info("请尝试重新搭建青龙面板或换个机器运行")
                exit(1)
            except Exception as e:
                logging.error(f"运行过程中出错: {e}")
            finally:
                if self.driver is not None:
                    self.driver.quit()

            end_time = time.time()
            spend_time = int((end_time - start_time) // 60)

            account_info.append(
                {
                    "username": self.username,
                    "browse_count": browse_count,
                    "like_count": like_count,
                    "spend_time": spend_time,
                    "connect_info": connect_info,
                }
            )

            # 重置状态
            browse_count = 0
            like_count = 0
            connect_info = ""

        logging.info("所有账户处理完毕")
        summary = ""
        for info in account_info:
            summary += (
                f"用户：{info['username']}\n\n"
                f"本次共浏览 {info['browse_count']} 个帖子\n"
                f"共点赞{info['like_count']} 个帖子\n"
                f"共用时 {info['spend_time']} 分钟\n"
                f"{info['connect_info']}\n\n"
            )
        send = load_send()
        if callable(send):
            send("Linux.do浏览帖子", summary)
        else:
            print("\n加载通知服务失败")


if __name__ == "__main__":
    linuxdo_browser = LinuxDoBrowser()
    linuxdo_browser.run()
