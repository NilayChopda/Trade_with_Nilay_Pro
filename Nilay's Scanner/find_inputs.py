from bs4 import BeautifulSoup

def find_inputs(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        html = f.read()
    
    soup = BeautifulSoup(html, 'lxml')
    
    # Check all inputs
    inputs = soup.find_all('input')
    for i in inputs:
        print(f"Input: name={i.get('name')}, type={i.get('type')}, value={i.get('value', '')[:50]}")
    
    # Check for any div with data- attributes
    divs = soup.find_all('div', attrs={'data-clause': True})
    for d in divs:
         print(f"Div with data-clause: {d.get('data-clause')[:50]}")

if __name__ == "__main__":
    find_inputs("chartink_debug.html")
