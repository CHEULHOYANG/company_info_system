import requests
from bs4 import BeautifulSoup
import re

def _fetch_og_image(url):
    """URL에서 OG:Image 메타 태그를 추출합니다."""
    if not url: return None
    if not url.startswith('http'): return None
    
    print(f"Fetching from: {url}")
    try:
        # User-Agent 설정 (봇 차단 방지)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        
        # Naver Blog Specific Logic: Handle Iframe
        if "blog.naver.com" in url:
            print("Naver Blog detected. Checking for iframe...")
            soup = BeautifulSoup(response.text, 'html.parser')
            iframe = soup.find('iframe', id='mainFrame')
            if iframe:
                iframe_src = iframe.get('src')
                if iframe_src:
                    # Construct full URL for the inner content
                    if iframe_src.startswith("/"):
                        iframe_src = "https://blog.naver.com" + iframe_src
                    print(f"Iframe found. Redirecting to: {iframe_src}")
                    # Recursively fetch from the iframe logic
                    # Simplified here for the script: just do a new request
                    response = requests.get(iframe_src, headers=headers, timeout=5)
                    response.raise_for_status()
        
        # 1. Try to find images in the body content (se-main-container or generally <img>)
        # Prefer 'postfiles.pstatic.net' as they are usually accessible.
        print("Searching for body images...")
        body_images = soup.find_all('img')
        for img in body_images:
            src = img.get('src')
            if src and "postfiles.pstatic.net" in src and "type=w" in src:
                # Filter out tiny icons or stickers if possible (usually w1, w2 are thumbs, w800 is main)
                # But 'gold.png' was w2. 
                # Let's just take the first substantial one.
                print(f"Found Body Image: {src}")
                # return src # Uncomment to test return strategy
        
        # 2. OG Image
        og_image = soup.find('meta', property='og:image')
        
        if og_image and og_image.get('content'):
            print(f"Found OG Image: {og_image['content']}")
            return og_image['content']
            
        # Twitter card fallback
        twitter_image = soup.find('meta', name='twitter:image')
        if twitter_image and twitter_image.get('content'):
            print(f"Found Twitter Image: {twitter_image['content']}")
            return twitter_image['content']
            
        print("No image found.")
        return None
    except Exception as e:
        print(f"Error fetching OG image from {url}: {e}")
        return None

if __name__ == "__main__":
    target_url = "https://blog.naver.com/ssneobiz/223860455825"
    _fetch_og_image(target_url)
