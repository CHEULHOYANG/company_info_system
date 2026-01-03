#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Direct file edit - replace radio buttons with button grid
"""

# Read file
with open('g:/company_project_system/templates/individual_list.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Define new status selector (lines 796-814)
new_lines = [
    '                <div style="margin-top: 16px;">\r\n',
    '                    <!-- Status Selector -->\r\n',
    '                    <div style="margin-bottom: 8px; font-size: 13px; font-weight: 600; color: #5a6c7d;">진행 상태:</div>\r\n',
    '                    <div style="display: grid; grid-template-columns: repeat(5, 1fr); gap: 8px; margin-bottom: 14px;">\r\n',
    '                        <button type="button" class="status-btn" data-status="접촉대기" \r\n',
    '                                onclick="selectStatus(this, \'접촉대기\')"\r\n',
    '                                style="padding: 10px 6px; border: 2px solid #e0e0e0; background: white; border-radius: 6px; cursor: pointer; font-size: 13px; font-weight: 500; transition: all 0.2s; color: #666; white-space: nowrap;">\r\n',
    '                            접촉대기\r\n',
    '                        </button>\r\n',
    '                        <button type="button" class="status-btn" data-status="접촉중"\r\n',
    '                                onclick="selectStatus(this, \'접촉중\')"\r\n',
    '                                style="padding: 10px 6px; border: 2px solid #e0e0e0; background: white; border-radius: 6px; cursor: pointer; font-size: 13px; font-weight: 500; transition: all 0.2s; color: #666; white-space: nowrap;">\r\n',
    '                            접촉중\r\n',
    '                        </button>\r\n',
    '                        <button type="button" class="status-btn" data-status="접촉해제"\r\n',
    '                                onclick="selectStatus(this, \'접촉해제\')"\r\n',
    '                                style="padding: 10px 6px; border: 2px solid #e0e0e0; background: white; border-radius: 6px; cursor: pointer; font-size: 13px; font-weight: 500; transition: all 0.2s; color: #666; white-space: nowrap;">\r\n',
    '                            접촉해제\r\n',
    '                        </button>\r\n',
    '                        <button type="button" class="status-btn" data-status="완료"\r\n',
    '                                onclick="selectStatus(this, \'완료\')"\r\n',
    '                                style="padding: 10px 6px; border: 2px solid #4a90e2; background: #4a90e2; color: white; border-radius: 6px; cursor: pointer; font-size: 13px; font-weight: 500; transition: all 0.2s; white-space: nowrap;">\r\n',
    '                            완료\r\n',
    '                        </button>\r\n',
    '                        <button type="button" class="status-btn" data-status="실패"\r\n',
    '                                onclick="selectStatus(this, \'실패\')"\r\n',
    '                                style="padding: 10px 6px; border: 2px solid #e0e0e0; background: white; border-radius: 6px; cursor: pointer; font-size: 13px; font-weight: 500; transition: all 0.2s; color: #666; white-space: nowrap;">\r\n',
    '                            실패\r\n',
    '                        </button>\r\n',
    '                    </div>\r\n',
    '                    <input type="hidden" id="selected_status" value="완료">\r\n',
    '                    <button onclick="saveMemo()" \r\n',
    '                            style="width: 100%; padding: 13px; background: linear-gradient(135deg, #28a745 0%, #34ce57 100%); color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 14px; font-weight: 600; box-shadow: 0 3px 6px rgba(40,167,69,0.25); transition: all 0.2s; display: flex; align-items: center; justify-content: center; gap: 8px;"\r\n',
    '                            onmouseover="this.style.transform=\'translateY(-1px)\'; this.style.boxShadow=\'0 5px 10px rgba(40,167,69,0.35)\'"\r\n',
    '                            onmouseout="this.style.transform=\'translateY(0)\'; this.style.boxShadow=\'0 3px 6px rgba(40,167,69,0.25)\'">\r\n',
    '                        <span style="font-size: 16px;">💾</span>\r\n',
    '                        메모 및 상태 저장\r\n',
    '                    </button>\r\n',
    '                </div>\r\n',
]

# Replace lines 796-814 (indices 795-813)
lines[795:814] = new_lines

# Save
with open('g:/company_project_system/templates/individual_list.html', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("✅ Status selector replaced successfully!")
print(f"Replaced {814-796+1} lines with {len(new_lines)} new lines")
print("\nNew features:")
print("- 5 equal-width status buttons (Grid layout)")
print("- Green gradient save button with 💾 icon")
print("- Hidden input for status tracking")
