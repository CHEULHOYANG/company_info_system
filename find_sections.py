import re

# Read the template file
with open(r'g:\company_project_system\templates\detail.html', 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# Find and print representative table section
rep_idx = content.find('rep.name')
if rep_idx > 0:
    start = max(0, rep_idx - 500)
    end = min(len(content), rep_idx + 500)
    print("=== REPRESENTATIVE SECTION ===")
    print(content[start:end])
    print("\n" + "="*50 + "\n")

# Find and print shareholder table section  
holder_idx = content.find('holder.shareholder_name')
if holder_idx > 0:
    start = max(0, holder_idx - 500)
    end = min(len(content), holder_idx + 500)
    print("=== SHAREHOLDER SECTION ===")
    print(content[start:end])
