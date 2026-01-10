
import sys

def delete_lines(filename, start_line, end_line):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except UnicodeDecodeError:
        with open(filename, 'r', encoding='cp949') as f:
            lines = f.readlines()
            
    # lines are 0-indexed, start_line/end_line are 1-indexed
    # We want to delete from start_line to end_line (inclusive)
    
    new_lines = lines[:start_line-1] + lines[end_line:]
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    print(f"Deleted lines {start_line} to {end_line}")

if __name__ == "__main__":
    delete_lines('web_app.py', 7638, 7835)
