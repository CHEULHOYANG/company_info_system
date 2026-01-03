#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Premium popup design improvements:
1. Replace emoji with sleek icon
2. Align all columns uniformly
3. Add elegant divider lines
4. Reduce spacing between sections
5. Add close button in header
"""

import re

# Read file
with open('g:/company_project_system/templates/individual_list.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Replace calendar emoji with sleek minimal icon
content = content.replace('📅 생년', '🗓 생년')  # More refined icon

# 2. Find the modal header and add close button
# Look for the h2 with company name
modal_header_pattern = r'(<div[^>]*class="modal-content"[^>]*>.*?<h2[^>]*id="modal_company_name"[^>]*>)'
modal_header_replacement = r'\1<button onclick="closeModal()" style="position: absolute; top: 20px; right: 24px; background: none; border: none; font-size: 24px; color: #999; cursor: pointer; padding: 0; line-height: 1; transition: color 0.2s;" onmouseover="this.style.color=\'#333\'" onmouseout="this.style.color=\'#999\'" title="닫기">×</button>'

content = re.sub(modal_header_pattern, modal_header_replacement, content, flags=re.DOTALL)

# 3. Update styles for premium look
premium_styles = '''
        /* Premium modal design */
        .modal-content h2 {
            font-size: 20px;
            font-weight: 600;
            color: #2c3e50;
            margin: 0;
            padding: 20px 24px 16px 24px;
            border-bottom: 2px solid #e8e8e8;
            position: relative;
        }
        
        /* Uniform grid layout for all sections */
        .detail-grid {
            display: grid;
            grid-template-columns: 140px 1fr 140px 1fr;
            gap: 12px 20px;
            padding: 16px 24px;
            border-bottom: 1px solid #f0f0f0;
        }
        
        .detail-grid > div {
            display: contents;
        }
        
        .detail-grid strong {
            color: #5a6c7d;
            font-weight: 500;
            font-size: 13px;
        }
        
        .detail-grid span,
        .detail-grid a {
            color: #2c3e50;
            font-size: 13px;
        }
        
        /* Section headers with elegant style */
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
        
        /* Memo and history sections */
        .memo-section,
        .history-section {
            padding: 16px 24px;
            background: #fafbfc;
        }
        
        .memo-section textarea {
            width: 100%;
            min-height: 100px;
            padding: 12px;
            border: 1px solid #ddd;
            border-radius: 6px;
            font-size: 13px;
            line-height: 1.5;
            resize: vertical;
            font-family: inherit;
        }
        
        .memo-section textarea:focus {
            outline: none;
            border-color: #4a90e2;
            box-shadow: 0 0 0 3px rgba(74, 144, 226, 0.1);
        }
        
        /* Status radio buttons */
        .status-group {
            display: flex;
            gap: 16px;
            align-items: center;
            padding: 12px 0;
        }
        
        .status-group label {
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 13px;
            cursor: pointer;
            color: #5a6c7d;
        }
        
        .status-group input[type="radio"] {
            cursor: pointer;
        }
        
        /* Compact spacing */
        .modal-section {
            padding: 0;
        }
        
        .modal-section:not(:last-child) {
            border-bottom: 1px solid #e8e8e8;
        }
'''

# Insert premium styles
content = content.replace('</style>', premium_styles + '    </style>')

# Save
with open('g:/company_project_system/templates/individual_list.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Premium popup design applied!")
print("\nImprovements:")
print("1. Replaced calendar emoji with sleek icon (🗓)")
print("2. Added close button (×) in top-right corner")
print("3. Applied uniform grid layout for alignment")
print("4. Added elegant section dividers")
print("5. Reduced spacing between sections")
print("6. Enhanced visual hierarchy with gradients and borders")
