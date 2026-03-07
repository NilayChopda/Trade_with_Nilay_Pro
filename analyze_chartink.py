
import re
from bs4 import BeautifulSoup

def analyze_page():
    with open('page_v2.html', 'r', encoding='utf-8') as f:
        html = f.read()
    
    soup = BeautifulSoup(html, 'html.parser')
    
    print("Title:", soup.title.string if soup.title else "No title")
    
    # Look for meta tags
    print("\nMeta tags:")
    for meta in soup.find_all('meta'):
        print(meta.attrs)
        
    # Look for scripts with 'scan' or 'process' or 'clause'
    print("\nInteresting scripts:")
    for script in soup.find_all('script'):
        if script.string:
            if any(word in script.string.lower() for word in ['scan', 'process', 'clause', 'token']):
                print(script.string[:500])
                print("-" * 50)

if __name__ == "__main__":
    analyze_page()
