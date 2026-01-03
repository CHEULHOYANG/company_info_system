#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Final popup design adjustments:
1. Remove line under company name
2. Make revenue and net income numbers larger and bold
"""

import re

# Read file
with open('g:/company_project_system/templates/individual_list.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Remove border-bottom from company name h2
# Find the h2 style and remove border-bottom
content = re.sub(
    r'\.modal-content h2 \{([^}]*border-bottom:[^;]+;[^}]*)\}',
    lambda m: '.modal-content h2 {\n' + 
              re.sub(r'border-bottom:[^;]+;', '', m.group(1)) + 
              '}',
    content
)

# Also update the inline h2 style if exists
content = re.sub(
    r'(<h2[^>]*style="[^"]*)(border-bottom:[^;"]+;?)([^"]*")',
    r'\1\3',
    content
)

# 2. Add CSS to make revenue and net income values larger and bold
financial_emphasis_css = '''
        /* Emphasize financial values */
        #detail_revenue,
        #detail_net_income {
            font-size: 15px !important;
            font-weight: 700 !important;
            color: #2c3e50 !important;
        }
'''

# Add the CSS
if '#detail_revenue' not in content:
    content = content.replace('</style>', financial_emphasis_css + '\n    </style>')

# Save
with open('g:/company_project_system/templates/individual_list.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Final design adjustments completed!")
print("\nChanges:")
print("1. Removed line under company name")
print("2. Made revenue and net income values:")
print("   - Larger (15px, +2px from base 13px)")
print("   - Bold (font-weight: 700)")
