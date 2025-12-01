import re

# 파일 읽기
with open(r'g:\company_project_system\templates\detail.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 이미 전역에 있는 loadContactHistory 함수 찾기 (라인 45 근처)
# displayContactHistory와 다른 접촉이력 관련 함수들 찾기 (라인 1130 근처)

# 1. displayContact History 함수 찾기
display_start = None
for i, line in enumerate(lines):
    if 'function displayContactHistory(historyList)' in line:
        display_start = i
        print(f"✅ displayContactHistory 함수 찾음: 라인 {i+1}")
        break

if display_start:
    # displayContactHistory 함수의 끝 찾기
    # 다음 함수 또는 스크립트 태그 끝까지
    brace_count = 0
    display_end = display_start
    found_start = False
    
    for i in range(display_start, len(lines)):
        line = lines[i]
        if '{' in line:
            found_start = True
            brace_count += line.count('{')
        if '}' in line:
            brace_count -= line.count('}')
        
        if found_start and brace_count == 0:
            display_end = i + 1
            break
    
    print(f"✅ displayContactHistory 함수 끝: 라인 {display_end}")
    
    # 함수 추출
    display_function_lines = lines[display_start:display_end]
    
    # 들여쓰기 수정 (20칸 → 4칸)
    fixed_lines = []
    for line in display_function_lines:
        # 20칸 들여쓰기를 4칸으로
        if line.startswith('                    '):  # 20 spaces
            fixed_lines.append('    ' + line[20:])
        elif line.startswith('                        '):  # 24 spaces
            fixed_lines.append('        ' + line[24:])
        else:
            fixed_lines.append(line)
    
    # loadContactHistory 함수 바로 다음에 삽입 (라인 66 다음)
    insert_position = 66  # loadContactHistory 함수가 66번 라인에서 끝남
    
    # 원본에서 제거
    del lines[display_start:display_end]
    
    # 새 위치에 삽입
    for i, line in enumerate(fixed_lines):
        lines.insert(insert_position + i, line)
    
    # 파일 저장
    with open(r'g:\company_project_system\templates\detail.html', 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print("\n✅ detail.html 파일이 수정되었습니다!")
    print(f"✅ displayContactHistory 함수가 라인 {insert_position+1}로 이동되었습니다!")
else:
    print("❌ displayContactHistory 함수를 찾을 수 없습니다")
