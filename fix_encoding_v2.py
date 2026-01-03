#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
More robust script to fix Korean encoding in detail.html
Try backup file first, then original
"""

import codecs
import os
import sys

file_path = 'g:/company_project_system/templates/detail.html'
backup_path = file_path + '.backup'

print("Step 1: Trying to read backup file with CP949...")
try:
    with codecs.open(backup_path, 'r', encoding='cp949') as f:
        content = f.read()
    print("✅ Successfully read backup with CP949")
    
    # Check for Korean text
    if '기업' in content or '조회' in content:
        print("✅ Korean characters found in content!")
    else:
        print("⚠️  Korean characters NOT found - checking first 500 chars:")
        print(content[:500])
        
    # Write as UTF-8
    with codecs.open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"\n✅ File saved as UTF-8 successfully!")
    
    # Verify
    with codecs.open(file_path, 'r', encoding='utf-8') as f:
        verify = f.read()
    if '기업' in verify or '조회' in verify:
        print("✅ VERIFICATION SUCCESS: Korean text readable in UTF-8!")
    else:
        print("❌ VERIFICATION FAILED: Korean text NOT readable")
        print("First 500 chars of converted file:")
        print(verify[:500])
        
except Exception as e:
    print(f"❌ Error: {e}")
    print("\nStep 2: Checking file with chardet library...")
    
    try:
        import chardet
        with open(backup_path, 'rb') as f:
            raw_data = f.read()
        detected = chardet.detect(raw_data)
        print(f"Detected encoding: {detected}")
        
        # Try detected encoding
        content = raw_data.decode(detected['encoding'])
        with codecs.open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Converted using {detected['encoding']} -> UTF-8")
        
    except ImportError:
        print("chardet not available, trying manual approach...")
        # Read as binary and try to decode
        with open(backup_path, 'rb') as f:
            raw = f.read()
        
        # Try different encodings
        for enc in ['cp949', 'euc-kr', 'utf-16', 'shift-jis']:
            try:
                decoded = raw.decode(enc)
                if '기' in decoded or '조' in decoded or '회' in decoded:
                    print(f"✅ Found Korean text with encoding: {enc}")
                    with codecs.open(file_path, 'w', encoding='utf-8') as f:
                        f.write(decoded)
                    print(f"✅ Saved as UTF-8")
                    break
            except:
                continue
