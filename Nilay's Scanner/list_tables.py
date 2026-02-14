from bs4 import BeautifulSoup

def list_tables(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        html = f.read()
    
    soup = BeautifulSoup(html, 'lxml')
    tables = soup.find_all('table')
    print(f"Total tables found: {len(tables)}")
    
    for i, table in enumerate(tables):
        classes = table.get('class', [])
        id = table.get('id', 'No ID')
        print(f"\nTable {i}: ID={id}, Classes={classes}")
        
        thead = table.find('thead')
        if thead:
            headers = [th.get_text(strip=True) for th in thead.find_all('th')]
            print(f"Headers: {headers}")
        else:
            print("No thead found")
        
        tbody = table.find('tbody')
        if tbody:
            rows = tbody.find_all('tr')
            print(f"Body Rows: {len(rows)}")
            if rows:
                print(f"Sample row: {[td.get_text(strip=True) for td in rows[0].find_all('td')]}")
        else:
            print("No tbody found")

if __name__ == "__main__":
    list_tables("chartink_debug.html")
