from bs4 import BeautifulSoup
import re
import json

def analyze_html(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        html = f.read()
    
    soup = BeautifulSoup(html, 'lxml')
    
    print(f"HTML Length: {len(html)}")
    
    # Check for CSRF token
    csrf = soup.find('meta', {'name': 'csrf-token'})
    if csrf:
        print(f"CSRF Token: {csrf.get('content')}")
    
    # Search for script tags containing JSON or scan_clause
    scripts = soup.find_all('script')
    print(f"Found {len(scripts)} scripts")
    
    for i, script in enumerate(scripts):
        content = script.get_text()
        if 'scan_clause' in content or 'clause' in content or 'obj' in content:
            print(f"--- Script {i} matches ---")
            # Print a snippet
            print(content[:500] if len(content) > 500 else content)
            
            # Try to regex out the scan_clause
            match = re.search(r'scan_clause\s*:\s*["\']([^"\']+)["\']', content)
            if match:
                print(f"FOUND scan_clause: {match.group(1)}")
            
            # Look for JSON-like objects
            if 'var obj = ' in content:
                print("Found 'var obj = '")

if __name__ == "__main__":
    analyze_html("chartink_debug.html")
