import sys

def remove_duplicates(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()
    
    # 去除每行末尾的换行符
    lines = [line.strip() for line in lines]
    
    # 去重 URL
    lines = list(set(lines))
    
    with open(file_path, 'w') as file:
        file.writelines(line + '\n' for line in lines)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python remove_duplicates.py <file_path>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    remove_duplicates(file_path)
