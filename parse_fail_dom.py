from bs4 import BeautifulSoup
html = open('checkbox_fail_dom.html', encoding='utf-8').read()
soup = BeautifulSoup(html, 'html.parser')

print("--- ALL aria-labels on buttons ---")
for btn in soup.find_all(['button', 'div']):
    aria = btn.get('aria-label')
    if aria and ('移除' in aria or '刪除' in aria or '來源' in aria or '選取' in aria):
        print(f"<{btn.name} aria-label='{aria}'> text='{btn.get_text(strip=True)}'")
