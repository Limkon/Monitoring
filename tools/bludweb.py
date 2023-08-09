import os
import random
import string
import sys
from jinja2 import Template

def count_files_in_directory(directory):
    file_count = sum(1 for _ in os.scandir(directory) if _.is_file())
    return file_count

def generate_random_data():
    return {
        'title': ''.join(random.choices(string.ascii_uppercase, k=10)),
        'heading': 'Random Heading',
        'content': 'This is some random content.',
        'color': f'#{random.randint(0, 255):02X}{random.randint(0, 255):02X}{random.randint(0, 255):02X}'
    }

def generate_random_filename():
    characters = string.ascii_letters + string.digits + string.punctuation
    filename = ''.join(random.choices(characters, k=random.randint(8, 12)))
    if random.choice([True, False]):
        filename = ''.join(random.choices(string.ascii_letters + string.digits, k=random.randint(8, 12)))
    return filename

def generate_code_file(directory):
    code_type = random.choice(["html", "css", "js"])
    template_file = f"templates/{code_type}.jinja2"
    output_file = f"{directory}/{generate_random_filename()}.{code_type}"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(template_file, 'r') as file:
        template_content = file.read()
        template = Template(template_content)
        data = generate_random_data()
        code = template.render(data=data)
        with open(output_file, 'w') as output:
            output.write(code)
            print(f"Generated file: {os.path.basename(output_file)}")

def remove_directory_contents(directory):
    for root, dirs, files in os.walk(directory, topdown=False):
        for file in files:
            file_path = os.path.join(root, file)
            os.remove(file_path)
        for dir in dirs:
            dir_path = os.path.join(root, dir)
            os.rmdir(dir_path)

if len(sys.argv) < 3:
    print("Please provide the directory and file count threshold as command line arguments")
    sys.exit(1)

target_directory = sys.argv[1]
threshold = int(sys.argv[2])

if not os.path.exists(target_directory):
    os.makedirs(target_directory)
    print(f"Directory {target_directory} created successfully")

for _ in range(threshold):
    generate_code_file(target_directory)

num_files = count_files_in_directory(target_directory)
print(f"Current file count: {num_files}")

if num_files > threshold:
    remove_directory_contents(target_directory)
    print("Directory cleared")
