import os
import sys
import tempfile
import shutil
import re
import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService # Selenium 4+
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import (
    NoSuchElementException,
    MoveTargetOutOfBoundsException,
    InvalidArgumentException,
    WebDriverException,
    TimeoutException
)
import traceback

# --- 常量定义 ---
# 随机操作次数
NUM_RANDOM_OPERATIONS = 3
# 每次鼠标移动操作中的小移动次数
NUM_MOUSE_MOVES_PER_OP = 3
# 滚动操作后的暂停时间
SCROLL_PAUSE_DURATION = 1.0
# 主要动作后的暂停时间
ACTION_PAUSE_DURATION = 0.5
# 短暂暂停时间，用于某些动作之间
SHORT_PAUSE_DURATION = 0.2
# Selenium 隐式等待超时时间
IMPLICIT_WAIT_TIMEOUT = 10
# 默认浏览器窗口宽度
DEFAULT_WINDOW_WIDTH = 1920
# 默认浏览器窗口高度
DEFAULT_WINDOW_HEIGHT = 1200
# 用户代理字符串
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"


def remove_duplicates_and_empty_lines_from_file(filename):
    """
    从文件中移除重复行和空行，并确保行是有效的 URL。
    结果写回原文件。
    """
    lines_seen = set()
    output_lines = []
    print(f"开始处理文件: {filename}，进行去重和去空行操作...")
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            for line in file:
                stripped_line = line.strip()
                # 确保是非空行，是有效URL格式，并且未出现过
                if stripped_line and re.match(r'^https?://', stripped_line) and stripped_line not in lines_seen:
                    lines_seen.add(stripped_line)
                    output_lines.append(stripped_line)
    except FileNotFoundError:
        print(f"错误: 文件 {filename} 未找到。")
        return False
    except Exception as e:
        print(f"读取文件 {filename} 时发生错误: {e}")
        return False

    # 使用临时文件写入，然后替换原文件，确保原子性
    temp_fd, temp_filename = tempfile.mkstemp()
    try:
        with os.fdopen(temp_fd, 'w', encoding='utf-8') as temp_file:
            temp_file.write('\n'.join(output_lines))
        shutil.move(temp_filename, filename)
        print(f"文件 {filename} 去重、去空行操作完成，结果已保存。共保留 {len(output_lines)} 个有效URL。")
        return True
    except Exception as e:
        print(f"写入或移动文件时发生错误: {e}")
        # 如果移动失败，尝试删除临时文件
        if os.path.exists(temp_filename):
            os.remove(temp_filename)
        return False
    finally:
        # 确保临时文件在任何情况下都被处理（如果shutil.move失败且上面未删除）
        if os.path.exists(temp_filename) and temp_filename != filename : # 检查是否已经被移动
             try:
                os.remove(temp_filename)
             except OSError: # 如果文件已被移动，删除会失败
                pass


def create_driver(chrome_driver_path=None):
    """
    创建并返回一个配置好的 Chrome WebDriver 实例。
    """
    print("正在配置 Chrome WebDriver...")
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument(f"--window-size={DEFAULT_WINDOW_WIDTH},{DEFAULT_WINDOW_HEIGHT}")
    chrome_options.add_argument("--ignore-certificate-errors") # 忽略证书相关错误
    chrome_options.add_argument("--ignore-ssl-errors=yes") # 忽略SSL错误
    chrome_options.add_argument("--disable-gpu") # 在 headless 模式下推荐
    chrome_options.add_argument("--log-level=3") # 减少控制台不必要的日志输出
    chrome_options.add_argument(f"user-agent={USER_AGENT}")
    # 尝试隐藏 Selenium 的自动化特征
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")

    driver = None
    try:
        if chrome_driver_path:
            print(f"尝试使用指定路径的 ChromeDriver: {chrome_driver_path}")
            service = ChromeService(executable_path=chrome_driver_path)
            driver = webdriver.Chrome(service=service, options=chrome_options)
        else:
            print("尝试使用系统 PATH 中的 ChromeDriver。")
            # 如果不指定路径，Selenium 会自动在 PATH 中查找
            driver = webdriver.Chrome(options=chrome_options)
        
        driver.implicitly_wait(IMPLICIT_WAIT_TIMEOUT)
        print("Chrome WebDriver 初始化成功。")
        return driver
    except WebDriverException as e:
        print(f"WebDriver 初始化失败: {e}")
        if "executable needs to be in PATH" in str(e) and not chrome_driver_path:
            print("错误提示：ChromeDriver 可执行文件需要被添加到系统 PATH 环境变量中，或者通过参数指定其路径。")
        elif chrome_driver_path and "cannot find" in str(e).lower():
             print(f"错误提示：指定的 ChromeDriver 路径 '{chrome_driver_path}' 可能不正确或文件不存在。")
        if driver: # 万一在异常前部分初始化了
            driver.quit()
        return None
    except Exception as e: # 捕获其他可能的初始化错误
        print(f"创建 WebDriver 时发生未知错误: {e}")
        traceback.print_exc()
        if driver:
            driver.quit()
        return None


def process_url(driver, url, url_index):
    """
    使用给定的 WebDriver 实例处理单个 URL。
    执行随机点击、鼠标移动、滚动等操作。
    """
    print(f"\n--- 开始处理第 {url_index + 1} 个 URL: {url} ---")
    ssl_error_occurred = False
    try:
        # 验证并修复 URL (虽然文件处理阶段已做过一次，这里多一层保险)
        url = url.strip()
        if not re.match(r'^https?://', url):
            print(f"URL '{url}' 格式不正确，尝试添加 https:// 前缀。")
            url = 'https://' + url
        
        print(f"尝试加载 URL: {url}")
        try:
            driver.get(url)
            print(f"成功打开网页: {url}")
        except TimeoutException:
            print(f"加载 URL 超时: {url}")
            # 页面可能部分加载，尝试继续，或者直接返回失败
            # return False # 如果超时则认为失败
        except WebDriverException as e:
            if "net::ERR_SSL_PROTOCOL_ERROR" in str(e) or "ssl_error" in str(e).lower():
                print(f"加载 {url} 时发生 SSL 协议错误，但尝试继续操作: {e}")
                ssl_error_occurred = True # 标记发生了SSL错误，后续逻辑可能需要
            else:
                print(f"加载 {url} 时发生 WebDriver 错误: {e}")
                return False # 其他 WebDriver 错误，此URL处理失败

        # 检查页面是否基本可用
        try:
            ready_state = driver.execute_script("return document.readyState;")
            print(f"页面状态: {ready_state}")
            if not (ready_state == "complete" or ready_state == "interactive" or not ssl_error_occurred):
                print(f"页面状态为 '{ready_state}' 且非SSL错误导致，可能无法完全操作，但仍尝试继续。")
        except Exception as e_rs:
            print(f"无法检查页面状态，尝试继续操作: {e_rs}")

        # 获取实际窗口尺寸 (可能与设置的不完全一致)
        try:
            window_width = driver.execute_script("return window.innerWidth;")
            window_height = driver.execute_script("return window.innerHeight;")
            print(f"当前浏览器窗口内部尺寸: {window_width}x{window_height}")
        except Exception:
            window_width, window_height = DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT
            print(f"无法获取实际窗口尺寸，使用默认值: {window_width}x{window_height}")

        # 执行一系列随机操作
        for i in range(NUM_RANDOM_OPERATIONS):
            operation_type = random.randint(1, 3)
            print(f"  执行第 {i+1}/{NUM_RANDOM_OPERATIONS} 次随机操作...")

            if operation_type == 1:  # 模拟点击
                print("    操作类型: 模拟点击")
                try:
                    body_element = driver.find_element("tag name", "body")
                    # 将元素滚动到视图中央，增加可见性和可点击性
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", body_element)
                    time.sleep(SHORT_PAUSE_DURATION) # 等待滚动完成

                    body_size = body_element.size
                    eff_width = body_size.get('width', 0)
                    eff_height = body_size.get('height', 0)

                    if eff_width > 0 and eff_height > 0:
                        # 在 body 元素内随机选择偏移量
                        offset_x = random.randint(0, eff_width - 1)
                        offset_y = random.randint(0, eff_height - 1)
                        ActionChains(driver).move_to_element_with_offset(body_element, offset_x, offset_y).click().perform()
                        print(f"    模拟点击 body 元素成功: 元素内偏移量({offset_x}, {offset_y})")
                    elif body_element.is_displayed(): # 如果元素大小为0但可见，尝试直接点击
                        ActionChains(driver).move_to_element(body_element).click().perform()
                        print("    模拟点击 body 元素成功 (元素大小为0，直接点击)")
                    else:
                        print("    Body 元素不可见或大小为0，无法进行有效点击。")
                    time.sleep(ACTION_PAUSE_DURATION)
                except (NoSuchElementException, MoveTargetOutOfBoundsException) as e_click:
                    print(f"    点击操作失败: {e_click}")
                except Exception as e_click_other:
                    print(f"    点击操作时发生未知错误: {e_click_other}")


            elif operation_type == 2:  # 模拟移动鼠标
                print("    操作类型: 模拟鼠标移动")
                try:
                    actions = ActionChains(driver)
                    body_element = driver.find_element("tag name", "body")
                    # 首先将鼠标移动到 body 元素的中心（或其他可交互区域的起点）
                    actions.move_to_element(body_element)
                    print("      鼠标移动: 计划初始移动到 body 元素中心")

                    for _ in range(NUM_MOUSE_MOVES_PER_OP):
                        x_offset = random.randint(-150, 150) # 增大移动范围
                        y_offset = random.randint(-150, 150)
                        actions.move_by_offset(x_offset, y_offset)
                        actions.pause(SHORT_PAUSE_DURATION) # 在连续移动中加入短暂的停顿
                        print(f"      鼠标移动: 计划增量移动，偏移量({x_offset}, {y_offset})")
                    
                    actions.perform() # 执行所有链式鼠标动作
                    print("    模拟鼠标系列移动操作完成。")
                    time.sleep(ACTION_PAUSE_DURATION)
                except (NoSuchElementException, MoveTargetOutOfBoundsException) as e_move:
                    print(f"    鼠标移动失败: {e_move}")
                except Exception as e_move_other:
                    print(f"    鼠标移动时发生未知错误: {e_move_other}")

            else:  # 模拟滚动网页
                print("    操作类型: 模拟滚动网页")
                try:
                    # 滚动到底部
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    print("      模拟滚动到页面底部。")
                    time.sleep(SCROLL_PAUSE_DURATION / 2)
                    # 滚动到顶部
                    driver.execute_script("window.scrollTo(0, 0);")
                    print("      模拟滚动到页面顶部。")
                    time.sleep(SCROLL_PAUSE_DURATION / 2)
                except Exception as e_scroll:
                    print(f"    滚动操作失败: {e_scroll}")
        
        # 操作完成后尝试刷新页面
        try:
            print(f"  尝试刷新页面: {url}")
            driver.refresh()
            print("  页面刷新成功。")
            time.sleep(ACTION_PAUSE_DURATION)
        except Exception as e_refresh:
            print(f"  刷新页面失败: {e_refresh}")
        
        print(f"--- URL {url} 处理完毕 ---")
        return True # 表示此URL处理成功

    except InvalidArgumentException as e_arg:
        print(f"处理 URL '{url}' 时发生无效参数错误: {e_arg}")
    except WebDriverException as e_wd: # 捕获此 URL 处理过程中的通用 WebDriver 错误
        print(f"处理 URL '{url}' 时发生 WebDriver 错误: {e_wd}")
        traceback.print_exc()
        # 尝试导航到空白页，重置浏览器状态，为下一个URL做准备
        try:
            print("尝试导航到 about:blank 以重置浏览器状态...")
            driver.get("about:blank")
        except Exception as e_blank:
            print(f"导航到 about:blank 失败: {e_blank}. WebDriver 可能不稳定。")
            # 如果导航到 about:blank 都失败，可能需要重启 WebDriver，这里先标记失败
            return False 
    except Exception as e_gen:
        print(f"处理 URL '{url}' 时发生未知异常: {e_gen}")
        traceback.print_exc()
    finally:
        # 无论成功与否，都尝试记录到 GITHUB_ENV (如果环境变量存在)
        # 这是基于原脚本的行为，即使处理失败也记录。
        # 如果只想记录成功的，可以将此部分移到 try 块的末尾，return True 之前。
        if "GITHUB_ENV" in os.environ:
            output_var_name = f"PROCESSED_URL_{url_index}"
            try:
                with open(os.environ["GITHUB_ENV"], "a", encoding='utf-8') as env_file:
                    env_file.write(f"{output_var_name}={url}\n")
                print(f"已将 URL '{url}' (索引 {url_index}) 作为 {output_var_name} 保存到 GITHUB_ENV。")
            except Exception as e_env:
                print(f"写入 GITHUB_ENV 失败: {e_env}")
        else:
            # print(f"GITHUB_ENV 未设置，跳过为 URL '{url}' 写入环境变量。") # 此日志可能过于频繁
            pass
    
    return False # 如果没有在 try 块中成功返回 True，则表示此 URL 处理失败


if __name__ == "__main__":
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("用法: python script.py <url_filename> [chrome_driver_path]")
        print("  <url_filename>: 包含URL列表的文本文件名。")
        print("  [chrome_driver_path]: (可选) ChromeDriver可执行文件的路径。")
        sys.exit(1)

    url_filename = sys.argv[1]
    chrome_driver_executable_path = sys.argv[2] if len(sys.argv) == 3 else None

    if not os.path.exists(url_filename):
        print(f"错误: URL文件 '{url_filename}' 不存在。")
        sys.exit(1)

    if not remove_duplicates_and_empty_lines_from_file(url_filename):
        print("文件预处理失败，脚本终止。")
        sys.exit(1)

    urls_to_process = []
    try:
        with open(url_filename, 'r', encoding='utf-8') as file:
            urls_to_process = [line.strip() for line in file if line.strip()]
        if not urls_to_process:
            print(f"文件 '{url_filename}' 中没有有效的URL可供处理。")
            sys.exit(0)
        print(f"从 '{url_filename}' 读取到 {len(urls_to_process)} 个URL准备处理。")
    except Exception as e:
        print(f"读取URL文件 '{url_filename}' 失败: {e}")
        sys.exit(1)
    
    main_driver = None
    processed_count = 0
    failed_count = 0
    try:
        main_driver = create_driver(chrome_driver_executable_path)
        if main_driver is None:
            print("无法初始化 WebDriver，脚本终止。")
            sys.exit(1)

        for index, current_url in enumerate(urls_to_process):
            if process_url(main_driver, current_url, index):
                processed_count +=1
            else:
                failed_count +=1
                print(f"URL {current_url} 处理失败。可能需要检查具体错误信息。")
                # 可选：如果一个URL失败导致driver不稳定，可以在这里尝试重启driver
                # print("尝试重启 WebDriver...")
                # main_driver.quit()
                # main_driver = create_driver(chrome_driver_executable_path)
                # if main_driver is None:
                #     print("重启 WebDriver 失败，终止后续处理。")
                #     break 

    except Exception as e_main:
        print(f"脚本主逻辑执行过程中发生严重错误: {e_main}")
        traceback.print_exc()
    finally:
        if main_driver:
            print("\n正在关闭主 WebDriver 实例...")
            main_driver.quit()
            print("主 WebDriver 已关闭。")
        
        print(f"\n--- 处理总结 ---")
        print(f"总共URL数量: {len(urls_to_process)}")
        print(f"成功处理URL数量: {processed_count}")
        print(f"失败处理URL数量: {failed_count}")
        print("脚本执行完毕。")
