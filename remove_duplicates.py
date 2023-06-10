import sys

def remove_duplicates(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()
    
    lines = list(set(lines))
    
    with open(file_path, 'w') as file:
        file.writelines(lines)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python remove_duplicates.py <file_path>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    remove_duplicates(file_path)
