import re

# 파일 읽기
with open(r'g:\company_project_system\templates\detail.html', 'r', encoding='utf-8') as f:
    content = f.read()

# loadContactHistory 함수와 관련 다른 함수들을 찾아서 전역 스코프로 이동

# 1. 먼저 990번 라인 근처의 <script> 태그 위치 찾기
script_marker = content.find('    <script>', content.find('접촉이력'))

# 2. loadContactHistory부터 파일 끝의 함수들을 찾기
# 라인 1099부터 함수 정의 시작
start_marker = "    // 접촉이력 관련 함수들\n    let contactEditingId = null;\n\n                    // 접촉이력 목록 로드\n                    async function loadContactHistory()"

# 이 마커를 찾아서
start_pos = content.find(start_marker)

if start_pos > 0:
    print(f"✅ loadContactHistory 함수 시작 위치를 찾았습니다: {start_pos}")
    
    # DOMContentLoaded 리스너의 끝을 찾기 (라인 1357 근처의 </script> 직전)
    # "    </script>" 를 찾되, loadContactHistory 이후에 있는 것
    script_end_marker = "    </script>"
    script_end_pos = content.find(script_end_marker, start_pos)
    
    if script_end_pos > 0:
        print(f"✅ </script> 태그 위치를 찾았습니다: {script_end_pos}")
        
        # 함수들을 전역으로 만들기 위해서는 들여쓰기를 줄여야 함
        # 현재 들여쓰기가 너무 많음 (20칸)
        # "                    async function" → "    async function"으로 변경
        
        # 간단한 방법: loadContactHistory 함수만 전역으로 이동
        # 1. loadContactHistory 함수 전체를 추출
        load_contact_start = content.find("async function loadContactHistory()", start_pos)
        
        # 함수 끝을 찾기 - 다음 함수 시작 전까지
        # displayContactHistory 함수 시작 찾기
        next_func = content.find("function displayContactHistory(", load_contact_start)
        
        if next_func > 0:
            # loadContactHistory 함수 전체
            load_contact_function = content[load_contact_start:next_func]
            
            # 들여쓰기 수정 (20칸 → 4칸)
            fixed_function = load_contact_function.replace('\n                    ', '\n    ')
            
            print(f"함수 길이: {len(load_contact_function)} → {len(fixed_function)}")
            print("함수 미리보기:", fixed_function[:200])
            
            # 이제 전체 파일에서 수정:
            # 1. 원래 함수 제거
            content = content[:load_contact_start] + content[next_func:]
            
            # 2. <script> 태그 직후에 전역 함수로 추가
            script_start = content.find('    <script>')
            if script_start > 0:
                insert_pos = content.find('\n', script_start) + 1
                content = content[:insert_pos] + "    // 접촉이력 관리 함수 (전역)\n    " + fixed_function.lstrip() + "\n\n" + content[insert_pos:]
                
                # 파일 저장
                with open(r'g:\company_project_system\templates\detail.html', 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print("\n✅ detail.html 파일이 수정되었습니다!")
                print("✅ loadContactHistory 함수가 전역 스코프로 이동되었습니다!")
        else:
            print("❌ displayContactHistory 함수를 찾을 수 없습니다")
    else:
        print("❌ </script> 태그를 찾을 수 없습니다")
else:
    print("❌ loadContactHistory 함수 시작 마커를 찾을 수 없습니다")
