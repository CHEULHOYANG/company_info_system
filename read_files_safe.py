import sys

def read_file(path, search_term=None):
    content = ""
    encoding = 'utf-8'
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        try:
            with open(path, 'r', encoding='cp949') as f:
                content = f.read()
                encoding = 'cp949'
        except Exception as e:
            print(f"Error reading {path}: {e}")
            return

    print(f"--- START {path} ({encoding}) ---")
    if search_term:
        lines = content.splitlines()
        for i, line in enumerate(lines):
            if search_term.lower() in line.lower():
                print(f"{i+1}: {line}")
    else:
        print(content)
    print(f"--- END {path} ---")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python read_files_safe.py <file_path> [search_term]")
        sys.exit(1)
    
    path = sys.argv[1]
    search_term = sys.argv[2] if len(sys.argv) > 2 else None
    read_file(path, search_term)
