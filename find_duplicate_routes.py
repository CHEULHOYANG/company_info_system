#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""웹 앱의 중복된 라우트 함수를 찾는 스크립트"""

import re

# web_app.py 파일 읽기
with open('web_app.py', 'r', encoding='utf-8') as f:
    content = f.read()
    lines = content.split('\n')

# 라우트와 함수명 추출
routes = {}
current_route = None
current_line = 0

for i, line in enumerate(lines, 1):
    # @app.route 라인 찾기
    if '@app.route' in line:
        # 라우트 추출 (여러 줄일 수 있음)
        route_match = re.search(r"@app\.route\('([^']+)'", line)
        if route_match:
            current_route = route_match.group(1)
            current_line = i
    
    # def 함수명 라인 찾기
    if line.strip().startswith('def '):
        func_match = re.search(r'def\s+(\w+)\s*\(', line)
        if func_match:
            func_name = func_match.group(1)
            
            if current_route:
                if func_name not in routes:
                    routes[func_name] = []
                routes[func_name].append({
                    'route': current_route,
                    'line': current_line,
                    'func_line': i
                })
                current_route = None

# 중복된 함수 찾기
print("=" * 60)
print("중복된 라우트 함수")
print("=" * 60)

duplicates_found = False
for func_name, route_list in sorted(routes.items()):
    if len(route_list) > 1:
        duplicates_found = True
        print(f"\n❌ 함수명: {func_name}")
        for route_info in route_list:
            print(f"   - 라우트: {route_info['route']} (라인 {route_info['line']}, 함수 {route_info['func_line']})")

if not duplicates_found:
    print("\n✓ 중복된 함수가 없습니다.")

# 통계
print("\n" + "=" * 60)
print(f"총 라우트 함수 개수: {len(routes)}")
print(f"중복된 함수 개수: {sum(1 for v in routes.values() if len(v) > 1)}")
