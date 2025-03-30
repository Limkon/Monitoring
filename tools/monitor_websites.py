import os
import sys
import requests
import time
from datetime import datetime
from urllib.parse import urlparse

def normalize_url(url):
    """检查 URL 是否包含协议，如果没有，则添加 https://"""
    parsed_url = urlparse(url)
    if not parsed_url.scheme:
        return "https://" + url
    return url

def check_website_status(url):
    """检查网站状态并返回结果"""
    try:
        start_time = time.time()
        response = requests.get(url, timeout=10)
        end_time = time.time()
        response_time = (end_time - start_time) * 1000

        status_code = response.status_code
        status = "✅ Up" if status_code == 200 else f"⚠️ Down (Status: {status_code})"

        result = {
            "url": url,
            "status": status,
            "status_code": status_code,
            "response_time": f"{response_time:.2f} ms",
            "timestamp": datetime.utcnow().isoformat()
        }
        print(f"{result['status']} - {url} | Code: {status_code} | Time: {result['response_time']}")
        return result

    except requests.RequestException as e:
        result = {
            "url": url,
            "status": "❌ Down (Error)",
            "status_code": None,
            "response_time": "N/A",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }
        print(f"❌ Down - {url} | Error: {str(e)}")
        return result

def update_readme(results, readme_file="README.md"):
    """将状态结果更新到 README.md"""
    header = "# Website Status\n\nBelow is the latest status of monitored websites:\n\n"
    table_header = "| URL | Status | Status Code | Response Time | Last Checked |\n|-----|--------|-------------|---------------|--------------|\n"
    
    rows = []
    for result in results:
        status_code = result.get('status_code', 'N/A')
        row = f"| {result['url']} | {result['status']} | {status_code} | {result['response_time']} | {result['timestamp']} |"
        rows.append(row)

    content = header + table_header + "\n".join(rows) + "\n"
    
    with open(readme_file, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ Updated {readme_file} with latest website status.")

def remove_duplicates_and_update_file(filename):
    """去除 URL 里的重复项、空行，并确保 URL 规范化"""
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            urls = [line.strip() for line in file.readlines()]

        # 去除空行
        urls = [url for url in urls if url]

        if not urls:
            print(f"⚠️ No valid URLs found in {filename}. Exiting.")
            return []

        # 规范化 URL 并去重（保持原始顺序）
        normalized_urls = list(dict.fromkeys(normalize_url(url) for url in urls))

        # 检查是否有修改
        if normalized_urls != urls:
            print(f"🔄 Updating {filename}: Fixing URLs, removing {len(urls) - len(normalized_urls)} duplicates and blank lines...")
            with open(filename, 'w', encoding='utf-8') as file:
                file.write('\n'.join(normalized_urls) + '\n')
            print(f"✅ {filename} has been updated successfully.")
        else:
            print(f"✅ No changes needed for {filename}. Already clean.")

        return normalized_urls

    except Exception as e:
        print(f"❌ Error processing {filename}: {e}")
        return []

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python monitor_websites.py <filename>")
        sys.exit(1)

    filename = sys.argv[1]

    # 1️⃣ 去重、去空行并规范 URL
    unique_urls = remove_duplicates_and_update_file(filename)

    if not unique_urls:
        sys.exit(1)

    # 2️⃣ 检查每个网站的状态
    results = []
    for url in unique_urls:
        result = check_website_status(url)
        results.append(result)

    # 3️⃣ 更新 README.md
    update_readme(results)

    # 4️⃣ 重新保存处理后的 URLs
    with open(filename, 'w', encoding='utf-8') as file:
        file.write('\n'.join(unique_urls) + '\n')
    print(f"✅ Updated {filename} with cleaned URLs.")
