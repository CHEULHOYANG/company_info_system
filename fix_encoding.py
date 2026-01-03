#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script to fix Korean character encoding in detail.html
Convert from CP949/EUC-KR to UTF-8
"""

import codecs
import os

file_path = 'g:/company_project_system/templates/detail.html'

# Create backup first
backup_path = file_path + '.backup'
print(f"Creating backup at {backup_path}...")

# Try to detect and read the file with different encodings
encodings_to_try = ['cp949', 'euc-kr', 'utf-8', 'latin-1']
content = None
detected_encoding = None

for enc in encodings_to_try:
    try:
        with codecs.open(file_path, 'r', encoding=enc) as f:
            content = f.read()
        detected_encoding = enc
        print(f"✅ Successfully read file with encoding: {enc}")
        break
    except (UnicodeDecodeError, LookupError) as e:
        print(f"❌ Failed to read with {enc}: {e}")
        continue

if content is None:
    print("ERROR: Could not read file with any encoding!")
    exit(1)

# Create backup
with codecs.open(backup_path, 'w', encoding=detected_encoding) as f:
    f.write(content)
print(f"✅ Backup created successfully")

# Save as UTF-8 with BOM to ensure proper recognition
with codecs.open(file_path, 'w', encoding='utf-8-sig') as f:
    f.write(content)

print(f"\n✅ File converted successfully!")
print(f"   Original encoding: {detected_encoding}")
print(f"   New encoding: UTF-8 with BOM")
print(f"   Backup: {backup_path}")

# Verify the conversion
try:
    with codecs.open(file_path, 'r', encoding='utf-8') as f:
        verify_content = f.read()
    print("✅ Verification: File can be read as UTF-8 successfully!")
    
    # Check for common Korean characters
    if '기업' in verify_content or '조회' in verify_content or '정보' in verify_content:
        print("✅ Verification: Korean characters detected correctly!")
    else:
        print("⚠️  Warning: Expected Korean characters not found")
        
except Exception as e:
    print(f"❌ Verification failed: {e}")
