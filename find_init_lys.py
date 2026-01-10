
def find_lines(filename, search_str):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except UnicodeDecodeError:
        with open(filename, 'r', encoding='cp949') as f:
            lines = f.readlines()
            
    for i, line in enumerate(lines):
        if search_str in line:
            print(f"{i+1}: {line.strip()}")

if __name__ == "__main__":
    find_lines('web_app.py', 'def init_lys_tables')
