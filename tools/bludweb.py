import os
import random
import string
import sys
import datetime
from jinja2 import Template

# 可选：添加调试开关
DEBUG = True

def debug_print(*args):
    """打印调试信息，仅在 DEBUG=True 时生效"""
    if DEBUG:
        print(*args)

def ensure_directory_exists(directory):
    """确保目录存在，不存在则创建"""
    if not os.path.exists(directory):
        os.makedirs(directory)
        debug_print(f"目录 {directory} 不存在，已创建。")
    else:
        debug_print(f"目录 {directory} 已存在。")

def count_files_in_directory(directory):
    """统计目录中的文件数"""
    try:
        file_count = sum(1 for entry in os.scandir(directory) if entry.is_file())
        return file_count
    except FileNotFoundError:
        debug_print(f"目录 {directory} 不存在，返回文件数 0")
        return 0
    except Exception as e:
        debug_print(f"统计文件数出错: {e}")
        raise

def generate_random_data():
    """生成随机数据，确保每次都有明显的随机性"""
    now = datetime.datetime.now()
    random_suffix = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
    return {
        'title': f"Title_{random_suffix}",
        'heading': f"Heading_{random_suffix}",
        'content': f"Content generated at {now.strftime('%H:%M:%S')}: {random_suffix}",
        'color': f'#{random.randint(0, 255):02X}{random.randint(0, 255):02X}{random.randint(0, 255):02X}',
        'created_at': now.isoformat(),
        'updated_at': now.isoformat(),
        'generated_on': now.strftime('%Y-%m-%d')
    }

def generate_random_filename(length=10):
    """生成随机文件名，支持字母和数字"""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choices(characters, k=length))

def generate_code_file(directory, code_type):
    """在指定目录中生成指定类型的代码文件"""
    template_file = f"templates/{code_type}.jinja2"
    output_file = f"{directory}/{generate_random_filename()}.{code_type}"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    default_templates = {
        'js': "console.log('{{ data.heading }}');\nconsole.log('{{ data.content }}');",
        'html': "<!DOCTYPE html>\n<html><head><title>{{ data.title }}</title></head><body><h1>{{ data.heading }}</h1><p>{{ data.content }}</p></body></html>",
        'css': "body { background-color: {{ data.color }}; }\nh1 { color: #{{ '%06X' % random.randint(0, 0xFFFFFF) }}; }",
        'py': """# {{ data.title }}
import random

def main():
    print("{{ data.heading }}")
    print("{{ data.content }}")

if __name__ == "__main__":
    main()
""",
        'json': """{
    "title": "{{ data.title }}",
    "heading": "{{ data.heading }}",
    "content": "{{ data.content }}",
    "metadata": {
        "created_at": "{{ data.created_at }}",
        "updated_at": "{{ data.updated_at }}"
    }
}""",
        'yaml': """---
title: {{ data.title }}
heading: {{ data.heading }}
content: {{ data.content }}
metadata:
  created_at: {{ data.created_at }}
  updated_at: {{ data.updated_at }}
""",
        'md': """# {{ data.heading }}

{{ data.content }}

*Generated on {{ data.generated_on }}*
"""
    }

    try:
        with open(template_file, 'r', encoding='utf-8') as file:
            template_content = file.read()
        debug_print(f"加载外部模板: {template_file}")
    except FileNotFoundError:
        template_content = default_templates.get(code_type, "/* No template available for {{ data.title }} */")
        debug_print(f"使用默认模板: {code_type}")
    except Exception as e:
        debug_print(f"加载模板出错: {e}")
        raise

    try:
        data = generate_random_data()
        template = Template(template_content)
        code = template.render(data=data)
        debug_print(f"随机数据: {data}")
        debug_print(f"渲染结果: \n{code}")
    except Exception as e:
        debug_print(f"模板渲染出错: {e}")
        raise

    try:
        with open(output_file, 'w', encoding='utf-8') as output:
            output.write(code)
        print(f"生成文件: {os.path.basename(output_file)}")
        debug_print(f"文件路径: {output_file}")
    except Exception as e:
        debug_print(f"写入文件出错: {e}")
        raise

def remove_directory_contents(directory):
    """递归删除目录及其内容"""
    try:
        for root, dirs, files in os.walk(directory, topdown=False):
            for file in files:
                os.remove(os.path.join(root, file))
            for dir in dirs:
                os.rmdir(os.path.join(root, dir))
        print(f"目录 {directory} 已清空")
    except Exception as e:
        debug_print(f"清空目录出错: {e}")
        raise

def main():
    """主函数，处理命令行参数并执行逻辑"""
    if len(sys.argv) < 3:
        print("请提供目录和文件数阈值作为命令行参数")
        print("示例: python script.py target_dir 5")
        sys.exit(1)

    target_directory = sys.argv[1]
    try:
        threshold = int(sys.argv[2])
    except ValueError:
        print("文件数阈值必须是整数")
        sys.exit(1)

    ensure_directory_exists(target_directory)

    code_types = ["js", "html", "css", "py", "json", "yaml", "md"]
    code_type = random.choice(code_types)
    generate_code_file(target_directory, code_type)

    num_files = count_files_in_directory(target_directory)
    print(f"当前文件数: {num_files}")

    if num_files > threshold:
        remove_directory_contents(target_directory)

if __name__ == "__main__":
    main()
