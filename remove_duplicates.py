import sys
import filecmp
import shutil

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
    temp_file_path = file_path + '_no_duplicates'
    
    # Remove duplicates and save to temporary file
    remove_duplicates(file_path)
    remove_duplicates(temp_file_path)
    
    # Compare temporary file with original file
    if not filecmp.cmp(file_path, temp_file_path):
        # If different, update the original file
        shutil.move(temp_file_path, file_path)
        print("URLs file updated.")
    else:
        # If same, remove the temporary file
        shutil.rmtree(temp_file_path)
        print("URLs file unchanged.")
