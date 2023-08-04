import sys
import os
import threading
import subprocess

def fetch_url(url):
    try:
        output = subprocess.check_output(['curl', '-s', url])  # 使用subprocess运行curl命令
        print(f"URL: {url}\nResponse:\n{output.decode('utf-8')}\n{'='*30}")
    except subprocess.CalledProcessError as e:
        print(f"Error fetching URL {url}: {e}")

def main():
    if len(sys.argv) != 2:
        print("Usage: python fetch_urls.py <filename>")
        return

    filename = sys.argv[1]
    if not os.path.exists(filename):
        print(f"File {filename} not found")
        return

    with open(filename, 'r') as file:
        urls = file.readlines()

    # 去除每行两端的空白字符
    urls = [url.strip() for url in urls]

    # 使用多线程并发处理URL
    threads = []
    for url in urls:
        thread = threading.Thread(target=fetch_url, args=(url,))
        threads.append(thread)
        thread.start()

    # 等待所有线程完成
    for thread in threads:
        thread.join()

if __name__ == "__main__":
    main()
