import random
import subprocess
import requests
import sys

# 从命令行参数中获取要访问的 URL 列表文件名
url_file = sys.argv[1]

# 从文件中读取要访问的 URL 列表
with open(url_file, "r") as file:
    urls = file.readlines()
urls = [url.strip() for url in urls]
random.shuffle(urls)

responses = []
failed_urls = []

for url in urls:
    try:
        # 执行 HTTP 请求，并处理响应
        response = requests.get(url, timeout=5)
        if response.status_code >= 200 and response.status_code < 300:
            print(f"{url}: 成功")
            responses.append(f"{url}: 成功")
        else:
            print(f"{url}: 失败 ({response.status_code})")
            responses.append(f"{url}: 失败 ({response.status_code})")
            failed_urls.append(f"{url}: 失败 ({response.status_code})")

    except requests.RequestException as e:
        print(f"{url}: 请求失败 ({str(e)})")
        responses.append(f"{url}: 请求失败 ({str(e)})")
        failed_urls.append(f"{url}: 请求失败 ({str(e)})")

    print("")
