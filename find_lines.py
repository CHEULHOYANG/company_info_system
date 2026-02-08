# View context around representative section
content = open('g:/company_project_system/templates/detail.html', encoding='cp949').read()
lines = content.split('\n')

with open('g:/company_project_system/context_output.txt', 'w', encoding='utf-8') as f:
    f.write("=== Representative section (Lines 255-275) ===\n")
    for i in range(254, 280):
        if i < len(lines):
            f.write(f"Line {i+1}: {lines[i]}\n")
    
    f.write("\n=== Shareholder section (Lines 305-330) ===\n")
    for i in range(304, 335):
        if i < len(lines):
            f.write(f"Line {i+1}: {lines[i]}\n")

print("Context written to context_output.txt")
