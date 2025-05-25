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
USER_AGENT = "WebsiteStatusMonitor/1.0 (+https://github.com/your_username/your_repo)" # 请替换为您的信息
MAX_WORKERS = 10

# --- 函数定义 ---
def normalize_url(url):
    parsed_url = urlparse(url.strip())
    if not parsed_url.scheme:
        return "https://" + url.strip()
    return url.strip()

def looks_like_url(url_str):
    if not isinstance(url_str, str) or not url_str.strip():
        return False
    try:
        parsed_url = urlparse(url_str.strip())
        return bool(parsed_url.netloc and '.' in parsed_url.netloc) and \
               bool(parsed_url.scheme or parsed_url.path or parsed_url.netloc)
    except ValueError:
        return False

def check_website_status(url):
    headers = {'User-Agent': USER_AGENT}
    result = {
        "url": url, "status_code": None, "response_time": "N/A",
        "timestamp": datetime.now(timezone.utc).isoformat(), "error": None, "status": "❓ 未知状态"
    }
    try:
        start_time = time.time()
        response = requests.get(url, timeout=REQUEST_TIMEOUT, headers=headers, allow_redirects=True)
        end_time = time.time()
        response_time_ms = (end_time - start_time) * 1000
        result["status_code"] = response.status_code
        result["response_time"] = f"{response_time_ms:.2f} ms"
        if response.url != url: result["final_url"] = response.url
        if 200 <= response.status_code < 300: result["status"] = "✅ 正常"
        elif 300 <= response.status_code < 400: result["status"] = f"↪️ 重定向 ({response.status_code})"
        elif response.status_code == 404: result["status"] = "🚫 未找到 (404)"
        else: result["status"] = f"⚠️ 异常 (状态: {response.status_code})"
        final_url_info = f" | 最终URL: {result['final_url']}" if "final_url" in result else ""
        print(f"{result['status']} - {url} | Code: {result['status_code']} | Time: {result['response_time']}{final_url_info}")
    except requests.Timeout:
        result["status"] = "❌ 太慢 (超时)"; result["error"] = "请求超时"
    except requests.exceptions.SSLError as e_ssl:
        result["status"] = "❌ SSL错误"; result["error"] = f"SSL问题: {str(e_ssl).splitlines()[0]}"
    except requests.exceptions.ConnectionError as e_conn:
        result["status"] = "❌ 连接错误"; result["error"] = f"连接问题: {str(e_conn).splitlines()[0]}"
    except requests.RequestException as e_req:
        result["status"] = "❌ 请求错误"; result["error"] = f"请求问题: {str(e_req).splitlines()[0]}"
    except Exception as e_gen:
        result["status"] = "❌ 内部处理错误"; result["error"] = f"意外错误: {str(e_gen).splitlines()[0]}"
        print(f"--- check_website_status 意外错误 for {url} ---"); traceback.print_exc(); print(f"--- 错误结束 {url} ---")
    if result["error"]: print(f"{result['status']} - {url} | 错误: {result.get('error', '未知')}")
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

# _generate_markdown_table_for_column 函数被移除，其逻辑整合到 update_readme

def update_readme(results: list, readme_file: str = README_FILENAME):
    """将状态结果更新到 README.md，实现排序和缩小字体（单列表格）"""
    if not results:
        print("⚠️ 没有结果可以更新到README。")
        content = f"# 网站状态监控\n\n最后检查时间: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"
        content += "当前没有监控任何网站，或所有监控结果均为空。\n"
        content += f"\n\n由 {USER_AGENT} 监控\n"
        try:
            with open(readme_file, "w", encoding="utf-8") as f: f.write(content)
            print(f"✅ 已使用空状态更新 {readme_file}。")
        except IOError as e: print(f"❌ 写入空的 {readme_file} 时发生错误: {e}")
        return

    # 1. 排序结果：不正常的在前，优先级相同时按URL字母顺序排序
    results.sort(key=lambda r: (get_status_priority(r.get('status', '❓')), r['url']))

    # 准备README的整体内容
    readme_content = f"# 网站状态监控\n\n最后检查时间: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"
    
    # 生成单个Markdown表格
    # 表头，所有内容用 <small> 包裹
    table_header = "| <small>URL</small> | <small>状态</small> | <small>状态码</small> | <small>响应时间</small> | <small>最后检查 (UTC)</small> |\n"
    table_alignment = "|:-----|:-------|:----------|:---------------|:--------------------|\n" # 指定对齐方式
    readme_content += table_header + table_alignment

    rows_md = []
    for result in results:
        # 表格数据也用 <small> 包裹
        status_code_display = f"<small>{result.get('status_code', 'N/A')}</small>"
        response_time_display = f"<small>{result['response_time']}</small>"
        timestamp_display = f"<small>{result['timestamp']}</small>"
        status_display = f"<small>{result.get('status', '❓')}</small>"

        url_display_raw = result['url']
        # 创建可点击的URL链接
        url_markdown = f"[{url_display_raw}]({url_display_raw})"
        if 'final_url' in result and result['final_url'] != result['url']:
            # 如果发生重定向，使用 <br> 换行并用 <sub> 显示最终URL，使其更小
            url_markdown += f"<br><sub>↳ 最终: [{result['final_url']}]({result['final_url']})</sub>"
        
        url_display_final = f"<small>{url_markdown}</small>"

        row = f"| {url_display_final} | {status_display} | {status_code_display} | {response_time_display} | {timestamp_display} |"
        rows_md.append(row)
    
    readme_content += "\n".join(rows_md) + "\n" # 每个表格后加一个换行
    readme_content += f"\n\n由 {USER_AGENT} 监控\n"

    try:
        with open(readme_file, "w", encoding="utf-8") as f:
            f.write(readme_content)
        print(f"✅ 已将最新的网站状态 ({len(results)} 个站点，已排序) 更新到 {readme_file}。")
    except IOError as e:
        print(f"❌ 写入 {readme_file} 时发生错误: {e}")

# --- process_url_file 和 主程序逻辑 (__main__) 保持不变 ---
def process_url_file(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            initial_urls = [line.strip() for line in file.readlines()]
    except FileNotFoundError:
        print(f"❌ 错误: 文件 {filename} 未找到。"); return []
    except Exception as e:
        print(f"❌ 读取 {filename} 时发生错误: {e}"); return []
    valid_format_urls = [url for url in initial_urls if looks_like_url(url)]
    normalized_urls = [normalize_url(url) for url in valid_format_urls]
    unique_urls = []
    seen = set()
    for url in normalized_urls:
        if url not in seen: seen.add(url); unique_urls.append(url)
    current_file_ideal_lines = []
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f_check:
                current_file_ideal_lines = [line.strip() for line in f_check if line.strip()]
        except Exception: pass
    if unique_urls != current_file_ideal_lines:
        print(f"🔄 正在更新 {filename}: ...")
        try:
            with open(filename, 'w', encoding='utf-8') as file: file.write('\n'.join(unique_urls) + '\n')
            print(f"✅ {filename} 已成功更新，包含 {len(unique_urls)} 个URL。")
        except IOError as e: print(f"❌ 更新 {filename} 时写入错误: {e}"); return initial_urls
    else: print(f"✅ {filename} 无需结构性更改，已是最新。")
    return unique_urls

if __name__ == "__main__":
    if len(sys.argv) != 2: print(f"用法: python {os.path.basename(__file__)} <url_filename>"); sys.exit(1)
    url_source_filename = sys.argv[1]
    print(f"--- 第1步: 处理URL文件: {url_source_filename} ---")
    urls_to_check = process_url_file(url_source_filename)
    if not urls_to_check: print(f"⚠️ 在 {url_source_filename} 中没有有效的URL可供检查。正在退出。"); sys.exit(1)
    print(f"找到 {len(urls_to_check)} 个唯一且有效的URL进行监控。")
    print(f"\n--- 第2步: 检查网站状态 (最大并发数={MAX_WORKERS}) ---")
    results_map = {}
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_url = {executor.submit(check_website_status, url): url for url in urls_to_check}
        for future in as_completed(future_to_url):
            original_url = future_to_url[future]
            try: result = future.result(); results_map[original_url] = result
            except Exception as exc:
                print(f"❌ URL {original_url} 在线程执行期间产生了一个未能捕获的异常:"); traceback.print_exc()
                error_result = {"url": original_url, "status": "❌ 线程执行错误", "status_code": None, "response_time": "N/A",
                                "timestamp": datetime.now(timezone.utc).isoformat(), "error": f"线程内未捕获: {str(exc)}"}
                results_map[original_url] = error_result
    ordered_results = [results_map[url] for url in urls_to_check if url in results_map]
    print(f"\n--- 第3步: 更新 {README_FILENAME} ---")
    update_readme(ordered_results, readme_file=README_FILENAME) # update_readme内部会进行排序
    print(f"\n--- 第4步: 更新URL文件 {url_source_filename} (移除404) ---")
    valid_urls_after_check = []
    removed_404_count = 0
    for result_key in urls_to_check:
        result = results_map.get(result_key)
        if result:
            if result.get('status_code') != 404: valid_urls_after_check.append(result['url'])
            else: print(f"🗑️ 标记 {result['url']} 因404将移除。"); removed_404_count +=1
        else: print(f"⚠️ URL {result_key} 无检查结果，将保留。"); valid_urls_after_check.append(result_key)
    if removed_404_count > 0:
        print(f"🔄 更新 {url_source_filename}: 移除 {removed_404_count} 个404 URL。")
        try:
            with open(url_source_filename, 'w', encoding='utf-8') as file: file.write('\n'.join(valid_urls_after_check) + '\n')
            print(f"✅ {url_source_filename} 已更新，含 {len(valid_urls_after_check)} URL。")
        except IOError as e: print(f"❌ 写入 {url_source_filename} 失败: {e}")
    else: print(f"✅ 无404 URL需移除于 {url_source_filename}。")
    print("\n监控脚本执行完毕。")
