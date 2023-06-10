import sys

def remove_duplicates(file_path):
    temp_file_path = file_path + "_no_duplicates"

    with open(file_path, 'r') as file:
        lines = file.readlines()

    lines = list(set(lines))

    with open(temp_file_path, 'w') as file:
        file.writelines(lines)

    # 重命名临时文件为原始文件
    os.rename(temp_file_path, file_path)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python remove_duplicates.py <file_path>")
        sys.exit(1)

    file_path = sys.argv[1]
    remove_duplicates(file_path)
