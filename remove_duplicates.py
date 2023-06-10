import sys
import os
import filecmp
import shutil

def remove_duplicates(file_path):
    lines = []

    # 输出调试信息
    print(f"文件路径: {file_path}")
    print(f"当前工作目录: {os.getcwd()}")

    # 读取文件内容并去除重复行
    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()  # 去除行首和行尾的空格和换行符
            if line and line not in lines:
                lines.append(line)

    # 将去重后的结果保存到临时文件中
    output_file_path = file_path + "_tmp"
    with open(output_file_path, 'w') as file:
        file.write('\n'.join(lines))

    print(f"去重完成，结果保存到 {output_file_path} 文件中")

    # 比较临时文件和原始文件
    if filecmp.cmp(file_path, output_file_path):
        print("文件无变化，跳过更新")
    else:
        # 复制临时文件到原始文件，并覆盖原始文件
        shutil.copyfile(output_file_path, file_path)
        print("文件已更新")

    # 删除临时文件
    os.remove(output_file_path)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python remove_duplicates.py <file_path>")
        sys.exit(1)

    file_path = os.path.abspath(sys.argv[1])
    remove_duplicates(file_path)
