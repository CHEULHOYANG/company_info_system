#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Fix popup design issues:
1. Remove double border lines
2. Align memo and contact history titles
3. Remove birth year emoji completely
"""

import re

# Read file
with open('g:/company_project_system/templates/individual_list.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Remove birth year emoji completely
content = content.replace('🗓 생년', '생년')

# 2. Fix double border issue - update CSS to have single borders only
# Remove conflicting border-bottom rules
css_fixes = '''
        /* Fix: Single border lines only */
        .modal-section {
            padding: 0;
            border-bottom: none !important;
        }
        
        .detail-grid {
            border-bottom: 1px solid #e8e8e8;
        }
        
        .section-header {
            border-bottom: 1px solid #e8e8e8;
        }
        
        /* Fix: Align section titles properly */
        .section-header {
            background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
            padding: 14px 24px;
            border-bottom: 1px solid #e8e8e8;
            font-size: 14px;
            font-weight: 600;
            color: #4a90e2;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .section-header::before {
            content: '';
            width: 3px;
            height: 16px;
            background: #4a90e2;
            border-radius: 2px;
        }
        
        /* Ensure memo and history sections are properly aligned */
        .memo-section,
        .history-section {
            padding: 16px 24px;
            background: #fafbfc;
        }
        
        /* Use section-header class for memo and history titles */
        h3.section-title {
            background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
            padding: 14px 24px;
            margin: 0;
            border-bottom: 1px solid #e8e8e8;
            font-size: 14px;
            font-weight: 600;
            color: #4a90e2;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        h3.section-title::before {
            content: '';
            width: 3px;
            height: 16px;
            background: #4a90e2;
            border-radius: 2px;
        }
'''

# Replace the conflicting styles
# Find and remove old modal-section border rules
content = re.sub(
    r'\.modal-section:not\(:last-child\) \{[^}]+\}',
    '',
    content
)

# Add the fixed CSS
if 'h3.section-title {' not in content:
    content = content.replace('</style>', css_fixes + '\n    </style>')

# 3. Update memo and history h3 tags to use section-title class
content = re.sub(
    r'<h3[^>]*>■ 메모</h3>',
    '<h3 class="section-title">메모</h3>',
    content
)

content = re.sub(
    r'<h3[^>]*>■ 접촉 히스토리</h3>',
    '<h3 class="section-title">접촉 히스토리</h3>',
    content
)

# Save
with open('g:/company_project_system/templates/individual_list.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Popup design refined!")
print("\nChanges:")
print("1. Removed birth year emoji (🗓) completely")
print("2. Fixed double border lines → single clean borders")
print("3. Aligned memo and contact history titles properly")
print("4. Applied consistent section header styling")
