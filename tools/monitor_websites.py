import os
import sys
import requests
import time
from datetime import datetime, timezone # 引入 timezone
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed # 用于并发

# --- 配置常量 ---
REQUEST_TIMEOUT = 10  # seconds
README_FILENAME = "README.md"
USER_AGENT = "WebsiteStatusMonitor/1.0 (+https://github.com/your_username/your_repo)" # 替换为您的信息
MAX_WORKERS = 10 # 并发检查的最大线程数 (可以根据CPU核心数调整, e.g., os.cpu_count() * 2)

def normalize_url(url):
    """检查 URL 是否包含协议，如果没有，则添加 https://"""
    parsed_url = urlparse(url.strip()) # strip url before parsing
    if not parsed_url.scheme:
        return "https://" + url.strip()
    return url.strip()

def looks_like_url(url_str):
    """检查字符串是否看起来像 URL"""
    if not isinstance(url_str, str) or not url_str.strip():
        return False
    try:
        parsed_url = urlparse(url_str.strip())
        # 确保有网络位置 (netloc) 并且有协议 (scheme) 或路径 (path)
        # 进一步检查 netloc 是否包含点，以排除像 "localhost" 这样的简单词（除非确实需要监控localhost）
        return bool(parsed_url.netloc and '.' in parsed_url.netloc) and \
               bool(parsed_url.scheme or parsed_url.path or parsed_url.netloc)
    except ValueError: # urlparse can raise ValueError for very malformed URLs
        return False

def check_website_status(url):
    """检查网站状态并返回结果字典"""
    headers = {'User-Agent': USER_AGENT}
    result = {
        "url": url,
        "status_code": None,
        "response_time": "N/A",
        "timestamp": datetime.now(timezone.utc).isoformat(), # 使用 timezone-aware UTC time
        "error": None
    }
    try:
        start_time = time.time()
        # 允许重定向，但记录最终的URL（requests默认处理重定向）
        response = requests.get(url, timeout=REQUEST_TIMEOUT, headers=headers, allow_redirects=True)
        end_time = time.time()
        response_time_ms = (end_time - start_time) * 1000

        result["status_code"] = response.status_code
        result["response_time"] = f"{response_time_ms:.2f} ms"
        # 如果发生重定向，response.url 会是最终的URL
        if response.url != url:
            result["final_url"] = response.url # 记录最终URL

        if 200 <= response.status_code < 300:
            result["status"] = "✅ Up"
        elif 300 <= response.status_code < 400:
            result["status"] = f"↪️ Redirect ({response.status_code})"
        elif response.status_code == 404:
            result["status"] = "🚫 Not Found (404)"
        else:
            result["status"] = f"⚠️ Down (Status: {response.status_code})"

        # 打印时使用原始请求的 URL
        print(f"{result['status']} - {url} | Code: {result['status_code']} | Time: {result['response_time']}" +
              (f" | Final URL: {result['final_url']}" if "final_url" in result else ""))
        return result

    except requests.Timeout:
        result["status"] = "❌ Down (Timeout)"
        result["error"] = "Request timed out"
    except requests.RequestException as e:
        result["status"] = "❌ Down (Error)"
        result["error"] = str(e).splitlines()[0] #取错误信息的第一行，避免过长
    
    print(f"{result['status']} - {url} | Error: {result.get('error', 'Unknown')}")
    return result


def update_readme(results, readme_file=README_FILENAME):
    """将状态结果更新到 README.md"""
    if not results:
        print("⚠️ No results to update README with.")
        return

    # 按原始URL排序（如果结果是字典的话），或者如果传入的是列表就直接用
    # results.sort(key=lambda r: r['url']) # 可选：如果需要按URL字母顺序排序

    header = f"# Website Status\n\nLast checked: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"
    table_header = "| URL | Status | Status Code | Response Time | Last Checked (UTC) |\n|-----|--------|-------------|---------------|--------------------|\n"
    
    rows = []
    for result in results:
        status_code_display = result.get('status_code', 'N/A')
        # 处理 final_url，如果存在则显示，并指向原始请求的 URL
        url_display = result['url']
        if 'final_url' in result and result['final_url'] != result['url']:
            url_display = f"[{result['url']}]({result['url']}) ( 최종: [{result['final_url']}]({result['final_url']}) )" # Markdown link
        else:
             url_display = f"[{result['url']}]({result['url']})"


        row = f"| {url_display} | {result['status']} | {status_code_display} | {result['response_time']} | {result['timestamp']} |"
        rows.append(row)

    content = header + table_header + "\n".join(rows) + "\n\n" \
              f"Monitored with {USER_AGENT}\n"
    
    try:
        with open(readme_file, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✅ Updated {readme_file} with latest website status ({len(results)} sites).")
    except IOError as e:
        print(f"❌ Error writing to {readme_file}: {e}")

def process_url_file(filename):
    """读取、去重、规范化URL，并写回文件（如果发生更改）。返回处理后的URL列表。"""
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            # strip() each line during read
            initial_urls = [line.strip() for line in file.readlines()]
    except FileNotFoundError:
        print(f"❌ Error: File {filename} not found.")
        return []
    except Exception as e:
        print(f"❌ Error reading {filename}: {e}")
        return []

    # 过滤看起来不像URL的行和空行
    valid_format_urls = [url for url in initial_urls if looks_like_url(url)]
    
    # 规范化URL (补全协议)
    normalized_urls = [normalize_url(url) for url in valid_format_urls]

    # 去重 (保持原始顺序)
    unique_urls = []
    seen = set()
    for url in normalized_urls:
        if url not in seen:
            seen.add(url)
            unique_urls.append(url)

    # 检查是否有实际内容更改 (不仅仅是行数变化，还要考虑顺序和内容)
    # 最简单的方式是比较处理后的URL列表和初始有效URL列表（经过同样处理流程）
    # 或者比较最终的 unique_urls 字符串形式和初始文件内容（去除无效行后）
    # 这里采用一种直接的方式：如果 unique_urls 和 initial_urls（仅包含有效格式、规范化和去重后）不同，则更新。
    
    # 为了准确判断是否需要写回，我们可以比较生成的 unique_urls 和文件原始内容处理后的结果
    # 如果原始文件已经完美，则 initial_urls 处理后应该等于 unique_urls
    # initial_urls_as_processed_for_comparison = []
    # seen_initial = set()
    # for url_orig in [normalize_url(u) for u in initial_urls if looks_like_url(u)]:
    #     if url_orig not in seen_initial:
    #         seen_initial.add(url_orig)
    #         initial_urls_as_processed_for_comparison.append(url_orig)

    # if unique_urls != initial_urls_as_processed_for_comparison:

    # 更简单的方式：比较写入内容和原始读取内容（去除空白行）
    # 另一种简单方法：如果 unique_urls 的数量或内容与原始有效URL列表（处理前）不同
    # 或者，直接比较最终生成的 unique_urls 列表和从文件读入并初步处理（strip）的列表。
    # 如果文件内容与 `\n`.join(unique_urls) + `\n` 不同，则写入。
    
    original_content_as_string = "\n".join(initial_urls) # 保存原始完整内容用于比较
    new_content_as_string = "\n".join(unique_urls)

    # 只有当处理后的内容与原始（经过strip的）内容不同时才更新
    # 为避免因尾部换行符问题误判，比较列表本身或者处理后的字符串
    if unique_urls != [normalize_url(u) for u in [s for s in initial_urls if looks_like_url(s)] if u not in seen] or \
       len(unique_urls) != len([s for s in initial_urls if looks_like_url(s) and normalize_url(s) in seen]): # 检查是否真的有变化
        # More robust: compare the string to be written with current file content (after basic cleaning for comparison)
        # For simplicity, if the list of unique URLs is different from what one would get by just reading and stripping, update.
        # This check might be complex. A simpler heuristic: if counts changed or if the actual strings changed.

        # 重新读取文件，并构建一个“理想的”当前文件内容列表
        current_file_ideal_lines = []
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f_check:
                current_file_ideal_lines = [line.strip() for line in f_check if line.strip()]
        
        # 如果 unique_urls 与当前文件中的有效行列表不同，则更新
        if unique_urls != current_file_ideal_lines:
            print(f"🔄 Updating {filename}: Normalizing URLs, removing duplicates/invalid entries...")
            try:
                with open(filename, 'w', encoding='utf-8') as file:
                    file.write('\n'.join(unique_urls) + '\n') #确保末尾有换行
                print(f"✅ {filename} has been updated successfully with {len(unique_urls)} URLs.")
            except IOError as e:
                print(f"❌ Error writing updates to {filename}: {e}")
                return initial_urls # 返回原始URLs，因为写入失败
        else:
            print(f"✅ No structural changes needed for {filename}. Already clean.")
    else:
        print(f"✅ No changes needed for {filename}. Already clean.")
    return unique_urls


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: python {os.path.basename(__file__)} <url_filename>")
        sys.exit(1)

    url_source_filename = sys.argv[1]

    # 1️⃣ 去重、去空行并规范 URL
    print(f"--- Step 1: Processing URL file: {url_source_filename} ---")
    urls_to_check = process_url_file(url_source_filename)

    if not urls_to_check:
        print(f"⚠️ No valid URLs to check in {url_source_filename}. Exiting.")
        sys.exit(1)
    print(f"Found {len(urls_to_check)} unique and valid URLs to monitor.")

    # 2️⃣ 并发检查每个网站的状态
    print(f"\n--- Step 2: Checking website statuses (max_workers={MAX_WORKERS}) ---")
    all_results = [] # 存储所有结果，包括错误
    
    # 使用 ThreadPoolExecutor 进行并发请求
    # 为了保持README中URL的顺序与输入文件一致，先获取结果，再按原顺序整理
    results_map = {} # 使用字典以URL为键存储结果，方便后续按原顺序排序
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_url = {executor.submit(check_website_status, url): url for url in urls_to_check}
        for future in as_completed(future_to_url):
            original_url = future_to_url[future]
            try:
                result = future.get()
                results_map[original_url] = result
            except Exception as exc:
                print(f"❌ URL {original_url} generated an exception during threaded execution: {exc}")
                # 创建一个错误结果条目
                error_result = {
                    "url": original_url, "status": "❌ Error (Thread Exception)", "status_code": None,
                    "response_time": "N/A", "timestamp": datetime.now(timezone.utc).isoformat(), "error": str(exc)
                }
                results_map[original_url] = error_result
    
    # 按 urls_to_check 的原始顺序整理结果
    ordered_results = [results_map[url] for url in urls_to_check if url in results_map]


    # 3️⃣ 更新 README.md
    print(f"\n--- Step 3: Updating {README_FILENAME} ---")
    update_readme(ordered_results, readme_file=README_FILENAME)

    # 4️⃣ 筛选出非404的URLs，并更新原始URL文件
    print(f"\n--- Step 4: Updating URL file {url_source_filename} by removing 404s ---")
    valid_urls_after_check = []
    removed_404_count = 0
    for result in ordered_results: # 使用有序的结果来决定哪些URL保留
        # 保留非404的，或者那些虽然出错但不是因为404（例如超时、连接错误）
        # 如果要严格只保留成功的，可以调整条件为 result.get('status_code') and 200 <= result.get('status_code') < 300
        if result.get('status_code') != 404 :
             # 如果URL重定向了，我们应该保留原始的、用户提供的URL（如果它是列表的一部分）
             # result['url'] 始终是原始请求的URL
            valid_urls_after_check.append(result['url'])
        else:
            print(f"🗑️ Marking {result['url']} for removal from {url_source_filename} due to 404 status.")
            removed_404_count +=1
    
    # 只有当存活的URL列表与检查前的URL列表不同时才重写文件
    # （即，确实有404的URL被移除了）
    if removed_404_count > 0:
        print(f"🔄 Updating {url_source_filename}: Removing {removed_404_count} URLs with 404 status.")
        try:
            with open(url_source_filename, 'w', encoding='utf-8') as file:
                file.write('\n'.join(valid_urls_after_check) + '\n') #确保末尾有换行
            print(f"✅ {url_source_filename} updated. Now contains {len(valid_urls_after_check)} URLs.")
        except IOError as e:
            print(f"❌ Error writing updated URL list to {url_source_filename}: {e}")
    else:
        print(f"✅ No URLs with 404 status found to remove from {url_source_filename}. No changes made to URL list.")
    
    print("\n监测脚本执行完毕。")
