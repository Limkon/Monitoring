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
        'title': ''.join(random.choices(string.ascii_uppercase, k=10)),
        'heading': 'Random Heading',
        'content': 'This is some random content.',
        'color': f'#{random.randint(0, 255):02X}{random.randint(0, 255):02X}{random.randint(0, 255):02X}'
    }

def generate_random_filename():
    # 生成随机文件名，可以是包含字母、数字和特殊字符的组合，也可以是纯字母或纯数字
    characters = string.ascii_letters + string.digits + string.punctuation
    filename = ''.join(random.choices(characters, k=random.randint(8, 12)))
    if random.choice([True, False]):
        # 纯字母或纯数字
        filename = ''.join(random.choices(string.ascii_letters + string.digits, k=random.randint(8, 12)))
    return filename

def generate_code_file(directory, code_type):
    # 在指定目录中随机生成指定类型的代码文件
    template_file = f"templates/{code_type}.jinja2"
    output_file = f"{directory}/{generate_random_filename()}.{code_type}"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)  # 创建目录
    with open(template_file, 'r') as file:
        template_content = file.read()
        template = Template(template_content)
        data = generate_random_data()  # 生成随机数据
        code = template.render(data=data)  # 使用随机数据渲染模板
        with open(output_file, 'w') as output:
            output.write(code)
            print(f"生成文件：{os.path.basename(output_file)}")  # 添加这行以显示生成的文件名

def remove_directory_contents(directory):
    # 递归删除目录及其内容
    for root, dirs, files in os.walk(directory, topdown=False):
        for file in files:
            file_path = os.path.join(root, file)
            os.remove(file_path)
        for dir in dirs:
            dir_path = os.path.join(root, dir)
            os.rmdir(dir_path)

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

# 随机选择一个类型（js、html 或 css）来生成代码文件
code_type = random.choice(["js", "html", "css"])
generate_code_file(target_directory, code_type)

# 统计文件数并清空目录及其内容
num_files = count_files_in_directory(target_directory)
print(f"当前文件数：{num_files}")

if num_files > threshold:
    remove_directory_contents(target_directory)
    print("目录已清空")
