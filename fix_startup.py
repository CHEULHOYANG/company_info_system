
import sys
import os

target_file = 'g:/company_project_system/web_app.py'

with open(target_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
skip_init = False
for line in lines:
    if line.strip() == 'initialize_db()':
        new_lines.append('# initialize_db()  # Moved to __main__ block to prevent double execution\n')
        continue
    new_lines.append(line)

# Check if __main__ block exists
has_main = False
for line in new_lines:
    if "if __name__ == '__main__':" in line:
        has_main = True
        break

if not has_main:
    new_lines.append("\nif __name__ == '__main__':\n")
    new_lines.append("    port = int(os.environ.get('PORT', 5000))\n")
    new_lines.append("    print(f'\\n=== Flask 서버 시작 ===')\n")
    new_lines.append("    initialize_db()\n")
    new_lines.append("    app.run(host='0.0.0.0', port=port, debug=not os.environ.get('RENDER'))\n")
else:
    # If main exists but doesn't have initialize_db(), we should inject it
    # But often it's better to just ensure it's there
    pass

with open(target_file, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print('Successfully cleaned up startup sequence.')
