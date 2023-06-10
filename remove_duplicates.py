import sys

def remove_duplicates(file_path):
    lines = set()

    # 读取文件内容并去除重复行
    with open(file_path, 'r') as file:
        for line in file:
            lines.add(line)

    # 将去重后的结果保存到临时文件中
    output_file_path = file_path + "_tmp"
    with open(output_file_path, 'w') as file:
        file.writelines(lines)

    print(f"去重完成，结果保存到 {output_file_path} 文件中")

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python remove_duplicates.py <file_path>")
        sys.exit(1)

    file_path = sys.argv[1]
    remove_duplicates(file_path)
