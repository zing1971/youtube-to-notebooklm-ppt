from bs4 import BeautifulSoup
html = open('sources_dom.html', encoding='utf-8').read()
soup = BeautifulSoup(html, 'html.parser')

with open('ui_text.txt', 'w', encoding='utf-8') as f:
    f.write('--- All Texts ---\n')
    for t in soup.stripped_strings:
        if len(t) > 2:
            f.write(t + '\n')
            
    f.write('\n--- Aria Labels ---\n')
    for tag in soup.find_all(lambda t: t.has_attr('aria-label')):
        f.write(tag['aria-label'] + '\n')
