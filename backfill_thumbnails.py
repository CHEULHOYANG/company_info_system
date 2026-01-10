import sqlite3
import requests
from bs4 import BeautifulSoup
import time

def _fetch_og_image(url):
    """URL에서 OG:Image 메타 태그를 추출합니다 (네이버 블로그 지원)."""
    if not url: return None
    if not url.startswith('http'): return None
    
    print(f"Fetching: {url}")
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')

        # 네이버 블로그 Iframe 처리
        if "blog.naver.com" in url:
            iframe = soup.find('iframe', id='mainFrame')
            if iframe:
                iframe_src = iframe.get('src')
                if iframe_src:
                    if iframe_src.startswith("/"):
                        iframe_src = "https://blog.naver.com" + iframe_src
                    print(f"  -> Redirecting to iframe: {iframe_src}")
                    response = requests.get(iframe_src, headers=headers, timeout=5)
                    response.raise_for_status()
                    soup = BeautifulSoup(response.text, 'html.parser')

        # 1. Body Image Priority (postfiles.pstatic.net)
        try:
            body_imgs = soup.find_all('img')
            for img in body_imgs:
                src = img.get('src')
                if src and 'postfiles.pstatic.net' in src and 'type=w' in src:
                    return src
        except:
            pass

        og_image = soup.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            return og_image['content']
            
        twitter_image = soup.find('meta', name='twitter:image')
        if twitter_image and twitter_image.get('content'):
            return twitter_image['content']
            
        return None
    except Exception as e:
        print(f"  Error: {e}")
        return None

def update_all_thumbnails():
    db_path = 'g:/company_project_system/company_database.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, title, link_url, thumbnail_url FROM ys_news")
    rows = cursor.fetchall()
    
    print(f"Found {len(rows)} news items.")
    
    updated_count = 0
    for row in rows:
        id, title, link_url, current_thumb = row
        
        # 강제 업데이트 (기존 썸네일 있어도 다시 가져옴)
        if link_url:
            print(f"Processing ID {id}: {title}")
            new_thumb = _fetch_og_image(link_url)
            
            if new_thumb:
                print(f"  -> Found thumbnail: {new_thumb[:50]}...")
                cursor.execute("UPDATE ys_news SET thumbnail_url = ? WHERE id = ?", (new_thumb, id))
                updated_count += 1
            else:
                print("  -> No thumbnail found.")
            
            time.sleep(1) # 부하 방지
            
    conn.commit()
    conn.close()
    print(f"\nCompleted. Updated {updated_count} items.")

if __name__ == "__main__":
    update_all_thumbnails()
