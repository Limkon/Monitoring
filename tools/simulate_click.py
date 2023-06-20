import random
import subprocess
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
        # 模拟点击页面操作
        subprocess.run(["python", "./tools/simulate_click.py", url], check=True)

        # 执行 curl 请求，并处理响应
        command = ["timeout", "5s", "curl", "-sf", "-o", "/dev/null", "-w", "%{http_code}\\n", url]
        result = subprocess.run(command, capture_output=True, text=True)
        response = result.stdout.strip()

        if response.startswith("2") or response.startswith("3"):
            print(f"{url}: 成功")
            responses.append(f"{url}: 成功")
        else:
            print(f"{url}: 失败 ({response})")
            responses.append(f"{url}: 失败 ({response})")
            failed_urls.append(f"{url}: 失败 ({response})")

    except subprocess.CalledProcessError:
        print(f"{url}: 执行命令失败")
        responses.append(f"{url}: 执行命令失败")
        failed_urls.append(f"{url}: 执行命令失败")

    print("")
