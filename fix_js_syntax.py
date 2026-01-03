#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Fix JavaScript syntax errors:
1. Remove duplicate selectStatusClean function
2. Ensure proper syntax
"""

import re

# Read file
with open('g:/company_project_system/templates/individual_list.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Find and remove OLD/duplicate selectStatus functions
# Keep only the clean one
content = re.sub(
   r'function selectStatus\(btn, status\) \{[^}]+\}',
    '',
    content
)

# Ensure we have exactly ONE clean selectStatusClean function
# First remove all instances
content = re.sub(
    r'function selectStatusClean\(btn, status\) \{[^}]+\}',
    '',
    content
)

# Now add ONE correct version in the script section
correct_function = '''
        function selectStatusClean(btn, status) {
            document.querySelectorAll('.status-btn').forEach(b => {
                b.style.background = 'white';
                b.style.color = '#666';
                b.style.borderColor = '#e0e0e0';
            });
            btn.style.background = '#4a90e2';
            btn.style.color = 'white';
            btn.style.borderColor = '#4a90e2';
            document.getElementById('selected_status').value = status;
        }
'''

# Add it before the closing </script> tag (last one in the file)
script_tags = list(re.finditer(r'</script>', content))
if script_tags:
    last_script = script_tags[-1]
    content = content[:last_script.start()] + correct_function + '\n    ' + content[last_script.start():]

# Save
with open('g:/company_project_system/templates/individual_list.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ JavaScript syntax fixed!")
print("- Removed duplicate function definitions")
print("- Added single correct selectStatusClean function")
