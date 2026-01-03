#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Add JavaScript to sync dropdown value from URL parameter
"""

# Read file
with open('g:/company_project_system/templates/individual_list.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Check if script already exists
if 'URL 파라미터로 검색 폼 초기화' in content:
    print("Script already exists! Skipping.")
else:
    # JavaScript to add
    new_script = '''
    <!-- URL 파라미터로 검색 폼 초기화 -->
    <script>
        // 페이지 로드 시 URL 파라미터로 검색 폼 값 복원
        window.addEventListener('DOMContentLoaded', function() {
            const urlParams = new URLSearchParams(window.location.search);
            
            // 진행상태 드롭다운 복원
            const statusParam = urlParams.get('status');
            if (statusParam) {
                const statusSelect = document.querySelector('select[name="status"]');
                if (statusSelect) {
                    statusSelect.value = statusParam;
                }
            }
        });
    </script>
'''
    
    # Insert before </body>
    content = content.replace('</body>', new_script + '</body>')
    
    # Save
    with open('g:/company_project_system/templates/individual_list.html', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ JavaScript added successfully!")
    print("Will sync dropdown value from URL parameter on page load")
