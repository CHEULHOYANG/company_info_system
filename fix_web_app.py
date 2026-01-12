
import os

file_path = 'web_app.py'

# The corrupted block starts with _fetch_og_image definition
start_marker = 'def _fetch_og_image(url):'
# The corrupted block ends before the seminars check, but let's be more specific.
# In the corrupted file, we saw:
#                 if news.get('id'):
#                     conn.execute('''
#                         UPDATE ys_news 
#                         SET title=?, category=?, summary=?, link_url=?, thumbnail_url=?, publish_date=?, updated_at=CURRENT_TIMESTAMP
#                         WHERE id=?
#                     ''', (news.get('title'), news.get('category'), news.get('summary'),
#                           news.get('link_url'), final_thumbnail, news.get('publish_date'), news.get('id')))
#                 else:
#                     # ...
#                     conn.execute('''
#                         INSERT INTO ys_news ...
#                     ''', ...)
#         
#         # 세미나 정보 업데이트
#         if 'seminars' in data:

end_marker = "        # 세미나 정보 업데이트"

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

start_idx = -1
end_idx = -1

for i, line in enumerate(lines):
    if start_marker in line:
        start_idx = i
    if end_marker in line and start_idx != -1 and i > start_idx:
        end_idx = i
        break

if start_idx != -1 and end_idx != -1:
    print(f"Found corrupted block from line {start_idx+1} to {end_idx+1}")
    
    # Construct the new content
    new_content = []
    
    # Add lines before the block
    new_content.extend(lines[:start_idx])
    
    # Add the corrected code
    new_content.append('# Helper: Fetch OG Image\n')
    new_content.append('def _fetch_og_image(url):\n')
    new_content.append('    """URL에서 OG:Image 메타 태그를 추출합니다 (네이버 블로그 지원)."""\n')
    new_content.append('    if not url: return None\n')
    new_content.append("    if not url.startswith('http'): return None\n")
    new_content.append('    \n')
    new_content.append('    try:\n')
    new_content.append('        # User-Agent 설정 (봇 차단 방지)\n')
    new_content.append('        headers = {\n')
    new_content.append("            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'\n")
    new_content.append('        }\n')
    new_content.append('        response = requests.get(url, headers=headers, timeout=5)\n')
    new_content.append('        response.raise_for_status()\n')
    new_content.append('        \n')
    new_content.append("        soup = BeautifulSoup(response.text, 'html.parser')\n")
    new_content.append('\n')
    new_content.append('        # 네이버 블로그 Iframe 처리\n')
    new_content.append('        if "blog.naver.com" in url:\n')
    new_content.append("            iframe = soup.find('iframe', id='mainFrame')\n")
    new_content.append('            if iframe:\n')
    new_content.append("                iframe_src = iframe.get('src')\n")
    new_content.append('                if iframe_src:\n')
    new_content.append('                    if iframe_src.startswith("/"):\n')
    new_content.append('                        iframe_src = "https://blog.naver.com" + iframe_src\n')
    new_content.append('                    # 내부 프레임 내용 재요청\n')
    new_content.append('                    response = requests.get(iframe_src, headers=headers, timeout=5)\n')
    new_content.append('                    response.raise_for_status()\n')
    new_content.append("                    soup = BeautifulSoup(response.text, 'html.parser')\n")
    new_content.append('\n')
    new_content.append('        # 1. Body Image Priority (postfiles.pstatic.net) -> More reliable than blogthumb\n')
    new_content.append('        try:\n')
    new_content.append("            body_imgs = soup.find_all('img')\n")
    new_content.append('            for img in body_imgs:\n')
    new_content.append("                src = img.get('src')\n")
    new_content.append("                if src and 'postfiles.pstatic.net' in src and 'type=w' in src:\n")
    new_content.append('                    return src\n')
    new_content.append('        except:\n')
    new_content.append('            pass\n')
    new_content.append('\n')
    new_content.append("        og_image = soup.find('meta', property='og:image')\n")
    new_content.append('        \n')
    new_content.append("        if og_image and og_image.get('content'):\n")
    new_content.append("            return og_image['content']\n")
    new_content.append('            \n')
    new_content.append('        # Twitter card fallback\n')
    new_content.append("        twitter_image = soup.find('meta', name='twitter:image')\n")
    new_content.append("        if twitter_image and twitter_image.get('content'):\n")
    new_content.append("            return twitter_image['content']\n")
    new_content.append('            \n')
    new_content.append('        return None\n')
    new_content.append('    except Exception as e:\n')
    new_content.append('        print(f"Error fetching OG image from {url}: {e}")\n')
    new_content.append('        return None\n')
    new_content.append('\n')
    new_content.append("@app.route('/api/lys/save-all', methods=['POST'])\n")
    new_content.append('def api_lys_save_all():\n')
    new_content.append('    """전체 데이터 저장 API (팀원+뉴스)"""\n')
    new_content.append('    conn = get_db_connection()\n')
    new_content.append('    try:\n')
    new_content.append('        # === Auto-Migration & Schema Initialization ===\n')
    new_content.append('        # Ensure all tables exist (Idempotent)\n')
    new_content.append("        conn.execute('''\n")
    new_content.append('            CREATE TABLE IF NOT EXISTS ys_team_members (\n')
    new_content.append('                id INTEGER PRIMARY KEY AUTOINCREMENT,\n')
    new_content.append('                name TEXT NOT NULL,\n')
    new_content.append('                position TEXT NOT NULL,\n')
    new_content.append('                phone TEXT,\n')
    new_content.append('                bio TEXT,\n')
    new_content.append('                photo_url TEXT,\n')
    new_content.append('                display_order INTEGER DEFAULT 1,\n')
    new_content.append('                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,\n')
    new_content.append('                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP\n')
    new_content.append('            )\n')
    new_content.append("        ''')\n")
    new_content.append('        \n')
    new_content.append("        conn.execute('''\n")
    new_content.append('            CREATE TABLE IF NOT EXISTS ys_news (\n')
    new_content.append('                id INTEGER PRIMARY KEY AUTOINCREMENT,\n')
    new_content.append('                title TEXT NOT NULL,\n')
    new_content.append('                category TEXT,\n')
    new_content.append('                summary TEXT,\n')
    new_content.append('                link_url TEXT,\n')
    new_content.append('                thumbnail_url TEXT,\n')
    new_content.append('                publish_date DATE,\n')
    new_content.append('                display_order INTEGER DEFAULT 1,\n')
    new_content.append('                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,\n')
    new_content.append('                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP\n')
    new_content.append('            )\n')
    new_content.append("        ''')\n")
    new_content.append('        \n')
    new_content.append("        conn.execute('''\n")
    new_content.append('            CREATE TABLE IF NOT EXISTS ys_seminars (\n')
    new_content.append('                id INTEGER PRIMARY KEY AUTOINCREMENT,\n')
    new_content.append('                title TEXT NOT NULL,\n')
    new_content.append('                date TEXT NOT NULL,\n')
    new_content.append('                time TEXT NOT NULL,\n')
    new_content.append('                location TEXT NOT NULL,\n')
    new_content.append('                description TEXT,\n')
    new_content.append('                max_attendees INTEGER DEFAULT 0,\n')
    new_content.append('                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP\n')
    new_content.append('            )\n')
    new_content.append("        ''')\n")
    new_content.append('        \n')
    new_content.append("        conn.execute('''\n")
    new_content.append('            CREATE TABLE IF NOT EXISTS ys_seminar_sessions (\n')
    new_content.append('                id INTEGER PRIMARY KEY AUTOINCREMENT,\n')
    new_content.append('                seminar_id INTEGER NOT NULL,\n')
    new_content.append('                time_range TEXT NOT NULL,\n')
    new_content.append('                title TEXT NOT NULL,\n')
    new_content.append('                speaker TEXT,\n')
    new_content.append('                description TEXT,\n')
    new_content.append('                location_note TEXT,\n')
    new_content.append('                display_order INTEGER DEFAULT 1,\n')
    new_content.append('                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP\n')
    new_content.append('            )\n')
    new_content.append("        ''')\n")
    new_content.append('\n')
    new_content.append('        # Check and add thumbnail_url to ys_news if missing\n')
    new_content.append('        try:\n')
    new_content.append('            conn.execute("SELECT thumbnail_url FROM ys_news LIMIT 1")\n')
    new_content.append('        except:\n')
    new_content.append('            print("Auto-migrating: Adding thumbnail_url to ys_news")\n')
    new_content.append('            conn.execute("ALTER TABLE ys_news ADD COLUMN thumbnail_url TEXT")\n')
    new_content.append('            \n')
    new_content.append('        # Check and add max_attendees to ys_seminars if missing\n')
    new_content.append('        try:\n')
    new_content.append('            conn.execute("SELECT max_attendees FROM ys_seminars LIMIT 1")\n')
    new_content.append('        except:\n')
    new_content.append('            print("Auto-migrating: Adding max_attendees to ys_seminars")\n')
    new_content.append('            conn.execute("ALTER TABLE ys_seminars ADD COLUMN max_attendees INTEGER DEFAULT 0")\n')
    new_content.append('        \n')
    new_content.append('        conn.commit()\n')
    new_content.append('        # ==========================================\n')
    new_content.append('\n')
    new_content.append('        data = request.get_json()\n')
    new_content.append('        \n')
    new_content.append('        # 팀원 정보 업데이트\n')
    new_content.append("        if 'team' in data:\n")
    new_content.append("            for member in data['team']:\n")
    new_content.append("                if member.get('id'):\n")
    new_content.append("                    conn.execute('''\n")
    new_content.append('                        UPDATE ys_team_members \n')
    new_content.append('                        SET name=?, position=?, phone=?, bio=?, photo_url=?, updated_at=CURRENT_TIMESTAMP\n')
    new_content.append('                        WHERE id=?\n')
    new_content.append("                    ''', (member.get('name'), member.get('position'), member.get('phone'),\n")
    new_content.append("                          member.get('bio'), member.get('photo_url'), member.get('id')))\n")
    new_content.append('        \n')
    new_content.append('        # 뉴스 정보 업데이트\n')
    new_content.append("        if 'news' in data:\n")
    new_content.append("            for news in data['news']:\n")
    new_content.append('                # 링크 URL 변경 시 또는 썸네일이 없을 때 이미지 자동 추출\n')
    new_content.append("                new_thumbnail_url = news.get('thumbnail_url')\n")
    new_content.append("                link_url = news.get('link_url')\n")
    new_content.append('                \n')
    new_content.append('                # 기존 데이터 조회 (URL 변경 확인용) - 최적화: ID가 있을 때만\n')
    new_content.append('                current_thumbnail = None\n')
    new_content.append('                current_link = None\n')
    new_content.append('                \n')
    new_content.append("                if news.get('id'):\n")
    new_content.append("                    row = conn.execute('SELECT link_url, thumbnail_url FROM ys_news WHERE id = ?', (news.get('id'),)).fetchone()\n")
    new_content.append('                    if row:\n')
    new_content.append('                        current_link = row[0]\n')
    new_content.append('                        current_thumbnail = row[1]\n')
    new_content.append('                \n')
    new_content.append('                # 썸네일 자동 업데이트 조건:\n')
    new_content.append('                # 1. 링크가 새로 입력되었거나 변경되었을 때\n')
    new_content.append('                # 2. 썸네일이 비어있고 링크가 있을 때\n')
    new_content.append('                should_fetch = False\n')
    new_content.append('                if link_url and (link_url != current_link):\n')
    new_content.append('                    should_fetch = True\n')
    new_content.append('                elif link_url and not current_thumbnail and not new_thumbnail_url:\n')
    new_content.append('                    should_fetch = True\n')
    new_content.append('                \n')
    new_content.append('                fetched_thumbnail = None\n')
    new_content.append('                if should_fetch:\n')
    new_content.append('                    print(f"Fetching OG image for: {link_url}")\n')
    new_content.append('                    fetched_thumbnail = _fetch_og_image(link_url)\n')
    new_content.append('                \n')
    new_content.append('                # 최종 저장할 썸네일 결정 (새로 가져온 것 > 입력된 것 > 기존 것)\n')
    new_content.append('                final_thumbnail = fetched_thumbnail or new_thumbnail_url or current_thumbnail\n')
    new_content.append('                \n')
    new_content.append("                if news.get('id'):\n")
    new_content.append("                    conn.execute('''\n")
    new_content.append('                        UPDATE ys_news \n')
    new_content.append('                        SET title=?, category=?, summary=?, link_url=?, thumbnail_url=?, publish_date=?, updated_at=CURRENT_TIMESTAMP\n')
    new_content.append('                        WHERE id=?\n')
    new_content.append("                    ''', (news.get('title'), news.get('category'), news.get('summary'),\n")
    new_content.append("                          news.get('link_url'), final_thumbnail, news.get('publish_date'), news.get('id')))\n")
    new_content.append('                else:\n')
    new_content.append('                    # 신규 생성 시에도 썸네일 페치\n')
    new_content.append('                    if not final_thumbnail and link_url:\n')
    new_content.append('                        final_thumbnail = _fetch_og_image(link_url)\n')
    new_content.append('                        \n')
    new_content.append("                    conn.execute('''\n")
    new_content.append('                        INSERT INTO ys_news (title, category, summary, link_url, thumbnail_url, publish_date)\n')
    new_content.append('                        VALUES (?, ?, ?, ?, ?, ?)\n')
    new_content.append("                    ''', (news.get('title'), news.get('category'), news.get('summary'),\n")
    new_content.append("                          news.get('link_url'), final_thumbnail, news.get('publish_date')))\n")
    new_content.append('\n')

    # Add lines after the block
    new_content.extend(lines[end_idx:])
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(new_content)
    
    print("Successfully patched web_app.py")
else:
    print("Could not find the corrupted block markers.")
