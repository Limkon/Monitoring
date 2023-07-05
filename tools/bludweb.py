import os
import random
import string
import sys

def generate_random_code():
    # 生成随机的网页代码
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    return f"<html><body>{code}</body></html>"

def generate_webpage_files(directory, num_files):
    # 在指定目录中随机生成网页文件
    for i in range(num_files):
        filename = f"webpage{i+1}.html"
        filepath = os.path.join(directory, filename)
        with open(filepath, 'w') as file:
            file.write(generate_random_code())

def count_files_in_directory(directory):
    # 统计目录中的文件数
    file_count = sum(1 for _ in os.scandir(directory) if _.is_file())
    return file_count

def clear_directory(directory):
    # 清空目录中的文件
    for file in os.scandir(directory):
        if file.is_file():
            os.remove(file.path)

# 通过命令行参数获取目录和文件数阈值
if len(sys.argv) < 3:
    print("请提供目录和文件数阈值作为命令行参数")
    sys.exit(1)

target_directory = sys.argv[1]
threshold = int(sys.argv[2])

# 如果目录不存在，则创建目录
if not os.path.exists(target_directory):
    os.makedirs(target_directory)

# 生成网页文件并统计文件数
generate_webpage_files(target_directory, 10)
num_files = count_files_in_directory(target_directory)
print(f"当前文件数：{num_files}")

# 如果文件数超过阈值，则清空目录
if num_files > threshold:
    clear_directory(target_directory)
    print("目录已清空")
