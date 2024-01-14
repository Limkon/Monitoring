import sys
import os
import threading
import subprocess

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

    # 检查 URL 是否有效
    valid_lines = []
    for line in lines:
        if line.startswith("GET ") or line.startswith("POST "):
            url = line[4:] if line.startswith("GET ") else line[5:]
            if url.startswith("https://") and "." in url[8:]:  # 检查 URL 是否包含有效的域名部分
                valid_lines.append(line)
            else:
                print(f"Invalid URL: {url}")
        else:
            print(f"Invalid line: {line}")

    # 使用多线程并发处理URL
    threads = []
    for line in valid_lines:
        if line.startswith("GET "):  # 如果行以 "GET " 开头，执行获取操作
            url = line[4:]  # 去掉 "GET " 后的部分
            thread = threading.Thread(target=fetch_url, args=(url,))
        elif line.startswith("POST "):  # 如果行以 "POST " 开头，执行发送请求操作
            parts = line[5:].split(" ", maxsplit=1)  # 去掉 "POST " 后的部分，然后分割出 URL 和数据
            url = parts[0]
            data = parts[1]
            thread = threading.Thread(target=send_request, args=(url, data))

        threads.append(thread)
        thread.start()

    # 等待所有线程完成
    for thread in threads:
        thread.join()

if __name__ == "__main__":
    main()
