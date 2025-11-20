import os

def convert_file(path):
    encodings = ['cp949', 'utf-8', 'euc-kr', 'latin-1']
    content = None
    read_encoding = None

    # Try to read
    for enc in encodings:
        try:
            with open(path, 'r', encoding=enc) as f:
                content = f.read()
            read_encoding = enc
            break
        except UnicodeDecodeError:
            continue
    
    if content is None:
        print(f"Failed to read {path} with any encoding.")
        return

    # Write as UTF-8
    try:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Converted {path} from {read_encoding} to utf-8")
    except Exception as e:
        print(f"Failed to write {path}: {e}")

def main():
    template_dir = 'templates'
    for f in os.listdir(template_dir):
        if f.endswith('.html'):
            path = os.path.join(template_dir, f)
            convert_file(path)

if __name__ == '__main__':
    main()
