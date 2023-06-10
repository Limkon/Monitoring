def remove_duplicates(input_file, output_file):
    with open(input_file, 'r') as file:
        lines = file.readlines()

    unique_lines = set(lines)

    with open(output_file, 'w') as file:
        file.writelines(unique_lines)

    print("去除重复行完成！")

# 使用示例
remove_duplicates('urls', 'urls_no_duplicates')
