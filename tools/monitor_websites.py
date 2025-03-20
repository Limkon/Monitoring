import os
import sys
import requests
import time
from datetime import datetime

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
    
    with open(readme_file, "w") as f:
        f.write(content)
    print(f"Updated {readme_file} with latest website status.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python monitor_websites.py <filename>")
        sys.exit(1)

    filename = sys.argv[1]

    # 读取 URL 文件
    with open(filename, 'r') as file:
        urls = [url.strip() for url in file.readlines() if url.strip()]

    if not urls:
        print("No valid URLs found in the file.")
        sys.exit(1)

    # 检查每个网站的状态
    results = []
    for url in urls:
        result = check_website_status(url)
        results.append(result)

    # 更新 README.md
    update_readme(results)
