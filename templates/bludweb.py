import os
import random
import string
import sys
import datetime
from pathlib import Path
from jinja2 import Template

# 调试开关
DEBUG = True

def debug_print(*args):
    if DEBUG:
        print("[DEBUG]", *args)

class ContentGenerator:
    """内容生成器类"""

    def __init__(self, target_directory: str):
        self.target_directory = Path(target_directory)
        self.ensure_directory_exists()

    def ensure_directory_exists(self):
        """确保目标目录存在"""
        if not self.target_directory.exists():
            self.target_directory.mkdir(parents=True, exist_ok=True)
            debug_print(f"目录 {self.target_directory} 不存在，已创建。")
        else:
            debug_print(f"目录 {self.target_directory} 已存在。")

    def count_files(self) -> int:
        """统计文件数量"""
        try:
            return sum(1 for entry in self.target_directory.iterdir() if entry.is_file())
        except FileNotFoundError:
            debug_print(f"目录 {self.target_directory} 不存在，返回文件数 0")
            return 0
        except Exception as e:
            debug_print(f"统计文件数出错: {e}")
            raise

    def generate_random_data(self) -> dict:
        """生成随机模板数据"""
        now = datetime.datetime.now()
        random_suffix = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
        return {
            'title': f"Title_{random_suffix}",
            'heading': f"Heading_{random_suffix}",
            'content': f"Content generated at {now.strftime('%H:%M:%S')}: {random_suffix}",
            'color': f'#{random.randint(0, 255):02X}{random.randint(0, 255):02X}{random.randint(0, 255):02X}',
            'text_color': f'#{random.randint(0, 255):02X}{random.randint(0, 255):02X}{random.randint(0, 255):02X}',
            'size': random.randint(12, 36),
            'name': random_suffix,
            'created_at': now.isoformat(),
            'updated_at': now.isoformat(),
            'generated_on': now.strftime('%Y-%m-%d')
        }

    def generate_random_filename(self, length=10) -> str:
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

    def get_default_template(self, code_type: str) -> str:
        """获取默认模板内容"""
        templates = {
            'js': "console.log('{{ data.heading }}');\nconsole.log('{{ data.content }}');",
            'html': "<!DOCTYPE html><html><head><title>{{ data.title }}</title></head><body><h1>{{ data.heading }}</h1><p>{{ data.content }}</p></body></html>",
            'css': "body { background-color: {{ data.color }}; }\nh1 { color: #{{ '%06X' % random.randint(0, 0xFFFFFF) }}; }",
            'py': "# {{ data.title }}\nimport random\ndef main():\n    print(\"{{ data.heading }}\")\n    print(\"{{ data.content }}\")\nif __name__ == \"__main__\":\n    main()",
            'json': "{\n    \"title\": \"{{ data.title }}\",\n    \"heading\": \"{{ data.heading }}\",\n    \"content\": \"{{ data.content }}\"\n}",
            'yaml': "---\ntitle: {{ data.title }}\nheading: {{ data.heading }}\ncontent: {{ data.content }}\n",
            'md': "# {{ data.heading }}\n\n{{ data.content }}\n\n*Generated on {{ data.generated_on }}*"
        }
        return templates.get(code_type, "/* No template available */")

    def generate_file(self, code_type: str):
        """生成文件"""
        template_file = Path("templates") / f"{code_type}.jinja2"
        output_file = self.target_directory / f"{self.generate_random_filename()}.{code_type}"

        try:
            if template_file.exists():
                template_content = template_file.read_text(encoding='utf-8')
                debug_print(f"加载外部模板: {template_file}")
            else:
                template_content = self.get_default_template(code_type)
                debug_print(f"使用默认模板: {code_type}")
        except Exception as e:
            debug_print(f"加载模板出错: {e}")
            raise

        try:
            data = self.generate_random_data()
            code = Template(template_content).render(data=data, random=random)
            debug_print("生成的数据摘要:", data['title'])
        except Exception as e:
            debug_print(f"模板渲染出错: {e}")
            raise

        try:
            output_file.write_text(code, encoding='utf-8')
            print(f"✅ 生成文件: {output_file.name}")
        except Exception as e:
            debug_print(f"写入文件出错: {e}")
            raise

    def clean_directory(self):
        """清空目录"""
        try:
            for item in self.target_directory.iterdir():
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)
            print(f"🧹 目录 {self.target_directory} 已清空")
        except Exception as e:
            debug_print(f"清空目录出错: {e}")
            raise

def main():
    if len(sys.argv) < 3:
        print("❗ 用法：python script.py <目录> <文件数阈值>")
        sys.exit(1)

    target_dir = sys.argv[1]
    try:
        threshold = int(sys.argv[2])
    except ValueError:
        print("❗ 文件数阈值必须是整数")
        sys.exit(1)

    generator = ContentGenerator(target_dir)
    
    code_types = ["js", "html", "css", "py", "json", "yaml", "md"]
    generator.generate_file(random.choice(code_types))

    num_files = generator.count_files()
    print(f"📄 当前文件数: {num_files}")

    if num_files > threshold:
        generator.clean_directory()

if __name__ == "__main__":
    main()
