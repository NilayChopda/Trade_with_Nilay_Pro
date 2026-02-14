from bs4 import BeautifulSoup

def find_pagination(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        html = f.read()
    
    soup = BeautifulSoup(html, 'lxml')
    
    # Look for any text containing "Next" or "Previous"
    buttons = soup.find_all(['button', 'a', 'li'])
    for b in buttons:
        text = b.get_text(strip=True)
        if "Next" in text or "Prev" in text:
            print(f"Potential Pagination: Tag={b.name}, Class={b.get('class')}, ID={b.get('id')}, Text={text}")

    # Look for "showing 1 to 20 of 271"
    text_nodes = soup.find_all(string=re.compile(r'of \d+ stocks'))
    for node in text_nodes:
        print(f"Total count text: {node}")

if __name__ == "__main__":
    import re
    find_pagination("chartink_debug.html")
