import sys
import random
import requests

def visit_urls(urls):
    failed_urls = []

    for url in urls:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"{url}: 成功 ({response.status_code})")
            else:
                print(f"{url}: 失败 ({response.status_code})")
                failed_urls.append(f"{url}: 失败 ({response.status_code})")
        except requests.RequestException as e:
            print(f"{url}: 失败 ({str(e)})")
            failed_urls.append(f"{url}: 失败 ({str(e)})")

    # 将失败的 URL 写入 README.md 文件
    with open("README.md", "w") as readme:
        readme.write("# 失败网址\n")
        for failed_url in failed_urls:
            readme.write(f"- {failed_url}\n")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("请提供 URLs 文件名作为命令行参数")
        sys.exit(1)

    filename = sys.argv[1]

    # 读取 URL 文件并随机打乱顺序
    with open(filename, "r") as file:
        urls = file.read().splitlines()
        random.shuffle(urls)

    # 访问 URL 并处理响应
    visit_urls(urls)
