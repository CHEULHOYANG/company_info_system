#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Fix missing endif tag in company_detail.html
"""

# Read file
with open('g:/company_project_system/templates/company_detail.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Add missing {% endif %} before </body>
# The file should end properly with all tags closed
if not content.strip().endswith('</html>'):
    print("Warning: File doesn't end with </html>")

# Find the last </body> tag and add {% endif %} before it
import re

# Count if/endif to confirm mismatch
ifs = len(re.findall(r'{%\s*if\s+', content))
endifs = len(re.findall(r'{%\s*endif\s*%}', content))
print(f"Before fix: {ifs} if tags, {endifs} endif tags")

# Add missing endif before </body>
if '</body>' in content:
    # Find last </body> and add endif before it
    parts = content.rsplit('</body>', 1)
    if len(parts) == 2:
        content = parts[0] + '\n{% endif %}\n</body>' + parts[1]
        print("Added {% endif %} before </body>")
else:
    # If no </body>, add at the end before </html>
    if '</html>' in content:
        parts = content.rsplit('</html>', 1)
        if len(parts) == 2:
            content = parts[0] + '\n{% endif %}\n</html>' + parts[1]
            print("Added {% endif %} before </html>")

# Verify
ifs_after = len(re.findall(r'{%\s*if\s+', content))
endifs_after = len(re.findall(r'{%\s*endif\s*%}', content))
print(f"After fix: {ifs_after} if tags, {endifs_after} endif tags")

if ifs_after == endifs_after:
    print("✅ SUCCESS: All if tags are now properly closed!")
    # Write back
    with open('g:/company_project_system/templates/company_detail.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ File saved successfully")
else:
    print(f"❌ ERROR: Still {ifs_after - endifs_after} missing endif tags")
