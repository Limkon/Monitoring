import os
import sys
import requests
import time
from datetime import datetime, timezone
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import traceback
import math

# --- 配置常量 ---
REQUEST_TIMEOUT = 10
README_FILENAME = "README.md"
USER_AGENT = "WebsiteStatusMonitor/1.0 (+https://github.com/your_username/your_repo)"
MAX_WORKERS = 10

# --- 函数定义 (normalize_url, looks_like_url, check_website_status, get_status_priority 保持不变) ---
def normalize_url(url):
    """检查 URL 是否包含协议，如果没有，则添加 https://"""
    parsed_url = urlparse(url.strip())
    if not parsed_url.scheme:
        return "https://" + url.strip()
    return url.strip()

def looks_like_url(url_str):
    """检查字符串是否看起来像 URL"""
    if not isinstance(url_str, str) or not url_str.strip():
        return False
    try:
        parsed_url = urlparse(url_str.strip())
        return bool(parsed_url.netloc and '.' in parsed_url.netloc) and \
               bool(parsed_url.scheme or parsed_url.path or parsed_url.netloc)
    except ValueError:
        return False

def check_website_status(url):
    """检查网站状态并返回结果字典"""
    headers = {'User-Agent': USER_AGENT}
    result = {
        "url": url,
        "status_code": None,
        "response_time": "N/A",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "error": None,
        "status": "❓ 未知状态"
    }
    try:
        start_time = time.time()
        response = requests.get(url, timeout=REQUEST_TIMEOUT, headers=headers, allow_redirects=True)
        end_time = time.time()
        response_time_ms = (end_time - start_time) * 1000
        result["status_code"] = response.status_code
        result["response_time"] = f"{response_time_ms:.2f} ms"
        if response.url != url:
            result["final_url"] = response.url
        if 200 <= response.status_code < 300:
            result["status"] = "✅ 正常"
        elif 300 <= response.status_code < 400:
            result["status"] = f"↪️ 重定向 ({response.status_code})"
        elif response.status_code == 404:
            result["status"] = "🚫 未找到 (404)"
        else:
            result["status"] = f"⚠️ 异常 (状态: {response.status_code})"
        final_url_info = f" | 最终URL: {result['final_url']}" if "final_url" in result else ""
        print(f"{result['status']} - {url} | Code: {result['status_code']} | Time: {result['response_time']}{final_url_info}")
        return result
    except requests.Timeout:
        result["status"] = "❌ 太慢 (超时)"
        result["error"] = "请求超时"
    except requests.exceptions.SSLError as e_ssl:
        result["status"] = "❌ SSL错误"
        result["error"] = f"SSL握手或证书验证失败: {str(e_ssl).splitlines()[0]}"
    except requests.exceptions.ConnectionError as e_conn:
        result["status"] = "❌ 连接错误"
        result["error"] = f"无法连接到服务器: {str(e_conn).splitlines()[0]}"
    except requests.RequestException as e_req: 
        result["status"] = "❌ 请求错误"
        result["error"] = f"请求期间发生错误: {str(e_req).splitlines()[0]}"
    except Exception as e_gen: 
        result["status"] = "❌ 内部处理错误"
        result["error"] = f"检查状态时发生意外错误: {str(e_gen).splitlines()[0]}"
        print(f"--- 在 check_website_status 函数中针对URL {url} 发生意外错误 ---")
        traceback.print_exc() 
        print(f"--- 意外错误结束 {url} ---")
    print(f"{result['status']} - {url} | 错误: {result.get('error', '未知错误')}")
    return result

def get_status_priority(status_str: str) -> int:
    if not status_str: status_str = "❓" 
    if status_str.startswith("❌"): return 0  
    if status_str.startswith("🚫"): return 1  
    if status_str.startswith("⚠️"): return 2  
    if status_str.startswith("↪️"): return 3  
    if status_str.startswith("❓"): return 4  
    if status_str.startswith("✅"): return 5  
    return 6 

def _generate_markdown_table_for_column(result_list: list, column_title: str) -> str:
    if not result_list:
        return ""
    table_content = f"### {column_title}\n\n" 
    table_header = "| <small>URL</small> | <small>状态</small> | <small>状态码</small> | <small>响应时间</small> | <small>最后检查 (UTC)</small> |\n"
    table_alignment = "|:-----|:-------|:----------|:---------------|:--------------------|\n" 
    table_content += table_header + table_alignment
    rows_md = []
    for result in result_list:
        status_code_display = f"<small>{result.get('status_code', 'N/A')}</small>"
        response_time_display = f"<small>{result['response_time']}</small>"
        timestamp_display = f"<small>{result['timestamp']}</small>"
        status_display = f"<small>{result.get('status', '❓')}</small>"
        url_display_raw = result['url']
        url_markdown = f"[{url_display_raw}]({url_display_raw})"
        if 'final_url' in result and result['final_url'] != result['url']:
            url_markdown += f"<br><sub>↳ 最终: [{result['final_url']}]({result['final_url']})</sub>"
        url_display_final = f"<small>{url_markdown}</small>"
        row = f"| {url_display_final} | {status_display} | {status_code_display} | {response_time_display} | {timestamp_display} |"
        rows_md.append(row)
    table_content += "\n".join(rows_md) + "\n" 
    return table_content

# vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
# 这是修改后的 update_readme 函数
# vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
def update_readme(results: list, readme_file: str = README_FILENAME):
    """将状态结果更新到 README.md，实现排序、缩小字体和两栏布局"""
    if not results:
        print("⚠️ 没有结果可以更新到README。")
        content = f"# 网站状态监控\n\n最后检查时间: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"
        content += "当前没有监控任何网站，或所有监控结果均为空。\n"
        content += f"\n\n由 {USER_AGENT} 监控\n"
        try:
            with open(readme_file, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"✅ 已使用空状态更新 {readme_file}。")
        except IOError as e:
            print(f"❌ 写入空的 {readme_file} 时发生错误: {e}")
        return

    results.sort(key=lambda r: (get_status_priority(r.get('status', '❓')), r['url']))

    readme_content = f"# 网站状态监控\n\n最后检查时间: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"
    
    # 使用HTML div和Flexbox实现两栏布局
    # gap: 20px; 是栏间距
    # 注意: 这里的 inline style 可能会被某些 Markdown 渲染器部分忽略或修改
    readme_content += '<div style="display: flex; flex-direction: row; flex-wrap: wrap; gap: 1em;">\n' # 使用 em 作为间距单位可能更灵活

    num_results = len(results)
    mid_point = math.ceil(num_results / 2.0)
    
    results_col1 = results[:int(mid_point)]
    results_col2 = results[int(mid_point):]

    # 为每个栏目 div 设置样式
    # flex: 1 1 calc(50% - 0.5em); 表示：允许增长，允许收缩，基础宽度为50%减去一半的gap
    # min-width: 300px; 保底最小宽度
    # box-sizing: border-box; 确保 padding 和 border 不会增加 div 的总宽度
    column_div_style = 'flex: 1 1 calc(50% - 0.5em); min-width: 300px; box-sizing: border-box;'

    readme_content += f'<div style="{column_div_style}">\n\n' 
    readme_content += _generate_markdown_table_for_column(results_col1, "监控列表 (1)")
    readme_content += '\n</div>\n'

    if results_col2:
        readme_content += f'<div style="{column_div_style}">\n\n'
        readme_content += _generate_markdown_table_for_column(results_col2, "监控列表 (2)")
        readme_content += '\n</div>\n'
    
    readme_content += '</div>\n' 
    readme_content += f"\n\n由 {USER_AGENT} 监控\n"

    try:
        with open(readme_file, "w", encoding="utf-8") as f:
            f.write(readme_content)
        print(f"✅ 已将最新的网站状态 ({num_results} 个站点，已排序和分栏) 更新到 {readme_file}。")
    except IOError as e:
        print(f"❌ 写入 {readme_file} 时发生错误: {e}")

# --- process_url_file 和 主程序逻辑 (__main__) 保持不变 ---
def process_url_file(filename):
    """读取、去重、规范化URL，并写回文件（如果发生更改）。返回处理后的URL列表。"""
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            initial_urls = [line.strip() for line in file.readlines()]
    except FileNotFoundError:
        print(f"❌ 错误: 文件 {filename} 未找到。")
        return []
    except Exception as e:
        print(f"❌ 读取 {filename} 时发生错误: {e}")
        return []
    valid_format_urls = [url for url in initial_urls if looks_like_url(url)]
    normalized_urls = [normalize_url(url) for url in valid_format_urls]
    unique_urls = []
    seen = set()
    for url in normalized_urls:
        if url not in seen:
            seen.add(url)
            unique_urls.append(url)
    current_file_ideal_lines = []
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f_check:
                current_file_ideal_lines = [line.strip() for line in f_check if line.strip()]
        except Exception: 
            pass 
    if unique_urls != current_file_ideal_lines:
        print(f"🔄 正在更新 {filename}: 规范化URL，移除重复项/无效条目...")
        try:
            with open(filename, 'w', encoding='utf-8') as file:
                file.write('\n'.join(unique_urls) + '\n')
            print(f"✅ {filename} 已成功更新，包含 {len(unique_urls)} 个URL。")
        except IOError as e:
            print(f"❌ 更新 {filename} 时写入错误: {e}")
            return initial_urls 
    else:
        print(f"✅ {filename} 无需结构性更改，已是最新。")
    return unique_urls

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"用法: python {os.path.basename(__file__)} <url_filename>")
        sys.exit(1)
    url_source_filename = sys.argv[1]
    print(f"--- 第1步: 处理URL文件: {url_source_filename} ---")
    urls_to_check = process_url_file(url_source_filename)
    if not urls_to_check:
        print(f"⚠️ 在 {url_source_filename} 中没有有效的URL可供检查。正在退出。")
        sys.exit(1)
    print(f"找到 {len(urls_to_check)} 个唯一且有效的URL进行监控。")
    print(f"\n--- 第2步: 检查网站状态 (最大并发数={MAX_WORKERS}) ---")
    results_map = {}
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_url = {executor.submit(check_website_status, url): url for url in urls_to_check}
        for future in as_completed(future_to_url):
            original_url = future_to_url[future]
            try:
                result = future.result() 
                results_map[original_url] = result
            except Exception as exc: 
                print(f"❌ URL {original_url} 在线程执行期间产生了一个未能捕获的异常:")
                traceback.print_exc() 
                error_result = {
                    "url": original_url,
                    "status": "❌ 线程执行错误", 
                    "status_code": None,
                    "response_time": "N/A",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "error": f"线程内未捕获的异常: {str(exc)}" 
                }
                results_map[original_url] = error_result
    ordered_results = [results_map[url] for url in urls_to_check if url in results_map]
    print(f"\n--- 第3步: 更新 {README_FILENAME} ---")
    update_readme(ordered_results, readme_file=README_FILENAME)
    print(f"\n--- 第4步: 更新URL文件 {url_source_filename} (移除404状态的URL) ---")
    valid_urls_after_check = []
    removed_404_count = 0
    for result_key in urls_to_check: 
        result = results_map.get(result_key)
        if result: 
            if result.get('status_code') != 404:
                valid_urls_after_check.append(result['url'])
            else:
                print(f"🗑️ 标记 {result['url']} 因为404状态将从 {url_source_filename} 中移除。")
                removed_404_count +=1
        else:
            print(f"⚠️ URL {result_key} 没有找到对应的检查结果，将从文件中保留。")
            valid_urls_after_check.append(result_key)
    if removed_404_count > 0:
        print(f"🔄 正在更新 {url_source_filename}: 移除 {removed_404_count} 个404状态的URL。")
        try:
            with open(url_source_filename, 'w', encoding='utf-8') as file:
                file.write('\n'.join(valid_urls_after_check) + '\n')
            print(f"✅ {url_source_filename} 已更新。现在包含 {len(valid_urls_after_check)} 个URL。")
        except IOError as e:
            print(f"❌ 将更新后的URL列表写入 {url_source_filename} 时发生错误: {e}")
    else:
        print(f"✅ 未发现需要从 {url_source_filename} 中移除的404状态URL。URL列表未作更改。")
    print("\n监控脚本执行完毕。")
