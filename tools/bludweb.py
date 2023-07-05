import os
import random
import string
import sys
from jinja2 import Template

def count_files_in_directory(directory):
    # 统计目录中的文件数
    file_count = sum(1 for _ in os.scandir(directory) if _.is_file())
    return file_count

def generate_random_data():
    # 随机生成一些数据，用于在代码模板中使用
    return {
        'name': ''.join(random.choices(string.ascii_uppercase, k=5)),
        'color': random.choice(['red', 'green', 'blue']),
        'number': random.randint(1, 10)
    }

def generate_code_file(directory):
    # 在指定目录中随机生成代码文件
    code_type = random.choice(["html", "css", "js"])
    template_file = f"templates/{code_type}.jinja2"
    output_file = f"{directory}/code.{code_type}"
    with open(template_file, 'r') as file:
        template_content = file.read()
        template = Template(template_content)
        data = generate_random_data()
        code = template.render(data=data)
        with open(output_file, 'w') as output:
            output.write(code)
    print(f"生成文件：code.{code_type}")

# 通过命令行参数获取目录和文件数阈值
if len(sys.argv) < 3:
    print("请提供目录和文件数阈值作为命令行参数")
    sys.exit(1)

target_directory = sys.argv[1]
threshold = int(sys.argv[2])

# 如果目录不存在，则创建目录
if not os.path.exists(target_directory):
    os.makedirs(target_directory)
    print(f"目录 {target_directory} 创建成功")

# 生成代码文件
generate_code_file(target_directory)

# 统计文件数并清空目录
num_files = count_files_in_directory(target_directory)
print(f"当前文件数：{num_files}")

if num_files > threshold:
    clear_directory(target_directory)
    print("目录已清空")
