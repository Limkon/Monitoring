import os
import sys
import requests
import time
from datetime import datetime, timezone
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import traceback # 导入 traceback 模块

# --- 配置常量 ---
REQUEST_TIMEOUT = 10  # seconds
README_FILENAME = "README.md"
USER_AGENT = "WebsiteStatusMonitor/1.0 (+https://github.com/your_username/your_repo)" # 请替换为您的信息
MAX_WORKERS = 10 # 并发检查的最大线程数

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
        "status": "❓ 未知状态" # 默认状态
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

        # 打印信息时使用原始请求的 URL
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
    except requests.RequestException as e_req: # 其他 requests 库相关的错误
        result["status"] = "❌ 请求错误"
        result["error"] = f"请求期间发生错误: {str(e_req).splitlines()[0]}"
    except Exception as e_gen: # 捕获此函数内任何其他未预料的错误
        result["status"] = "❌ 内部处理错误"
        result["error"] = f"检查状态时发生意外错误: {str(e_gen).splitlines()[0]}"
        print(f"--- 在 check_website_status 函数中针对URL {url} 发生意外错误 ---")
        traceback.print_exc() # 在函数内部直接打印追溯，方便定位
        print(f"--- 意外错误结束 {url} ---")
    
    # 如果发生异常，上面的打印语句可能没有执行，这里补上
    print(f"{result['status']} - {url} | 错误: {result.get('error', '未知错误')}")
    return result


def update_readme(results, readme_file=README_FILENAME):
    """将状态结果更新到 README.md"""
    if not results:
        print("⚠️ 没有结果可以更新到README。")
        return

    header = f"# 网站状态监控\n\n最后检查时间: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"
    table_header = "| URL | 状态 | 状态码 | 响应时间 | 最后检查时间 (UTC) |\n|-----|------|---------|----------|--------------------|\n"
    
    rows = []
    for result in results:
        status_code_display = result.get('status_code', 'N/A')
        url_display = result['url']
        if 'final_url' in result and result['final_url'] != result['url']:
            url_display = f"[{result['url']}]({result['url']}) (最终: [{result['final_url']}]({result['final_url']}))"
        else:
             url_display = f"[{result['url']}]({result['url']})"

        row = f"| {url_display} | {result.get('status', '❓')} | {status_code_display} | {result['response_time']} | {result['timestamp']} |"
        rows.append(row)

    content = header + table_header + "\n".join(rows) + "\n\n" \
              f"由 {USER_AGENT} 监控\n"
    
    try:
        with open(readme_file, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✅ 已将最新的网站状态 ({len(results)} 个站点) 更新到 {readme_file}。")
    except IOError as e:
        print(f"❌ 写入 {readme_file} 时发生错误: {e}")

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
        except Exception: # 如果读取用于比较的文件失败，就假设需要更新
            pass 
        
    if unique_urls != current_file_ideal_lines:
        print(f"🔄 正在更新 {filename}: 规范化URL，移除重复项/无效条目...")
        try:
            with open(filename, 'w', encoding='utf-8') as file:
                file.write('\n'.join(unique_urls) + '\n')
            print(f"✅ {filename} 已成功更新，包含 {len(unique_urls)} 个URL。")
        except IOError as e:
            print(f"❌ 更新 {filename} 时写入错误: {e}")
            return initial_urls # 写入失败，返回原始URL避免数据丢失
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
                result = future.get()
                results_map[original_url] = result
            except Exception as exc: # 捕获从 future.get() 抛出的在线程内未处理的异常
                print(f"❌ URL {original_url} 在线程执行期间产生了一个未能捕获的异常:")
                traceback.print_exc() # 确保在这里打印完整的追溯信息
                error_result = {
                    "url": original_url,
                    "status": "❌ 线程执行错误", # 更新了状态信息
                    "status_code": None,
                    "response_time": "N/A",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "error": f"线程内未捕获的异常: {str(exc)}" # 更新了错误信息
                }
                results_map[original_url] = error_result
    
    ordered_results = [results_map[url] for url in urls_to_check if url in results_map]

    print(f"\n--- 第3步: 更新 {README_FILENAME} ---")
    update_readme(ordered_results, readme_file=README_FILENAME)

    print(f"\n--- 第4步: 更新URL文件 {url_source_filename} (移除404状态的URL) ---")
    valid_urls_after_check = []
    removed_404_count = 0
    for result in ordered_results:
        if result.get('status_code') != 404:
            valid_urls_after_check.append(result['url'])
        else:
            print(f"🗑️ 标记 {result['url']} 因为404状态将从 {url_source_filename} 中移除。")
            removed_404_count +=1
    
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
