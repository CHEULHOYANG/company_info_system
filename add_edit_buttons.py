#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re
import codecs

# Try different encodings
encodings = ['utf-8', 'cp949', 'euc-kr', 'utf-8-sig', 'latin1']
content = None
used_encoding = None

for enc in encodings:
    try:
        with open(r'g:\company_project_system\templates\detail.html', 'r', encoding=enc, errors='ignore') as f:
            content = f.read()
        used_encoding = enc
        print(f"✓ Successfully read file with {enc} encoding")
        break
    except Exception as e:
        print(f"✗ Failed with {enc}: {e}")
        continue

if content is None:
    print("ERROR: Could not read file with any encoding!")
    exit(1)

# Pattern 1: Replace simple <td>{{ rep.name }}</td> with edit button
pattern1 = r'<td>(\{\{[\s]*rep\.name[\s]*\}\})</td>'
replacement1 = r'''<td>
                            <div id="rep-name-display-{{ loop.index }}" style="display: inline-block;">
                                <span id="rep-name-text-{{ loop.index }}">{{ rep.name }}</span>
                                {% if rep.name and '*' in rep.name %}
                                <button id="edit-rep-btn-{{ loop.index }}" onclick="editRepresentativeName({{ loop.index }}, '{{ rep.name }}')"
                                    style="margin-left: 8px; padding: 4px 12px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px;">수정</button>
                                {% endif %}
                            </div>
                            <div id="rep-name-edit-{{ loop.index }}" style="display: none;">
                                <input type="text" id="rep-name-input-{{ loop.index }}" value="{{ rep.name }}"
                                    style="padding: 6px; border: 2px solid #007bff; border-radius: 4px; font-size: 14px; width: 120px;">
                                <button onclick="saveRepresentativeName({{ loop.index }}, '{{ rep.name }}')"
                                    style="margin-left: 4px; padding: 6px 12px; background: #28a745; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px;">저장</button>
                                <button onclick="cancelEditRepresentativeName({{ loop.index }})"
                                    style="margin-left: 4px; padding: 6px 12px; background: #6c757d; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px;">취소</button>
                            </div>
                        </td>'''

matches1 = re.findall(pattern1, content)
print(f"Found {len(matches1)} rep.name matches")
content = re.sub(pattern1, replacement1, content)

# Pattern 2: Replace <td>{{ holder.shareholder_name }}</td> with edit button  
pattern2 = r'<td>(\{\{[\s]*holder\.shareholder_name[\s]*\}\})</td>'
replacement2 = r'''<td>
                            <div id="shareholder-name-display-{{ loop.index }}" style="display: inline-block;">
                                <span id="shareholder-name-text-{{ loop.index }}">{{ holder.shareholder_name }}</span>
                                {% if holder.shareholder_name and '*' in holder.shareholder_name %}
                                <button id="edit-shareholder-btn-{{ loop.index }}" onclick="editShareholderName({{ loop.index }}, '{{ holder.shareholder_name }}')"
                                    style="margin-left: 8px; padding: 4px 12px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px;">수정</button>
                                {% endif %}
                            </div>
                            <div id="shareholder-name-edit-{{ loop.index }}" style="display: none;">
                                <input type="text" id="shareholder-name-input-{{ loop.index }}" value="{{ holder.shareholder_name }}"
                                    style="padding: 6px; border: 2px solid #007bff; border-radius: 4px; font-size: 14px; width: 120px;">
                                <button onclick="saveShareholderName({{ loop.index }}, '{{ holder.shareholder_name }}')"
                                    style="margin-left: 4px; padding: 6px 12px; background: #28a745; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px;">저장</button>
                                <button onclick="cancelEditShareholderName({{ loop.index }})"
                                    style="margin-left: 4px; padding: 6px 12px; background: #6c757d; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px;">취소</button>
                            </div>
                        </td>'''

matches2 = re.findall(pattern2, content)
print(f"Found {len(matches2)} holder.shareholder_name matches")
content = re.sub(pattern2, replacement2, content)

# Write back using UTF-8
with codecs.open(r'g:\company_project_system\templates\detail.html', 'w', encoding='utf-8', errors='ignore') as f:
    f.write(content)

print(f"\n✓ Edit buttons added successfully!")
print(f"  - Used encoding: {used_encoding}")
print(f"  - Modified {len(matches1)} representative fields")
print(f"  - Modified {len(matches2)} shareholder fields")
print("\nPlease restart the server to see changes.")
