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

def send_request(url, data):
    try:
        output = subprocess.check_output(['curl', '-s', '-X', 'POST', '-d', data, url])  # 发送POST请求
        print(f"URL: {url}\nRequest Data: {data}\nResponse:\n{output.decode('utf-8')}\n{'='*30}")
    except subprocess.CalledProcessError as e:
        print(f"Error sending request to URL {url}: {e}")

def main():
    if len(sys.argv) != 2:
        print("Usage: python fetch_urls.py <filename>")
        return

    filename = sys.argv[1]
    if not os.path.exists(filename):
        print(f"File {filename} not found")
        return

    with open(filename, 'r') as file:
        lines = file.readlines()

    # 去除每行两端的空白字符
    lines = [line.strip() for line in lines]

    # 使用多线程并发处理URL
    threads = []
    for line in lines:
        if line.startswith("GET "):  # 如果行以 "GET " 开头，执行获取操作
            url = line[4:]  # 去掉 "GET " 后的部分
            thread = threading.Thread(target=fetch_url, args=(url,))
        elif line.startswith("POST "):  # 如果行以 "POST " 开头，执行发送请求操作
            parts = line[5:].split(" ", 1)  # 去掉 "POST " 后的部分，然后分割出 URL 和数据
            url = parts[0]
            data = parts[1]
            thread = threading.Thread(target=send_request, args=(url, data))
        else:
            print(f"Invalid line: {line}")
            continue

        threads.append(thread)
        thread.start()

    # 等待所有线程完成
    for thread in threads:
        thread.join()

if __name__ == "__main__":
    main()
