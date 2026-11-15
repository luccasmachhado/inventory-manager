from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

def scrape_nfce_items(url: str):
    with sync_playwright() as p:
        # Abre um navegador headless (invisível)
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)
        
        # Aguarda a tabela de resultados carregar na página
        try:
            page.wait_for_selector("#tabResult", timeout=10000)
        except Exception:
            pass
            
        html_content = page.content()
        browser.close()
        
    # Agora faz o parse com o BeautifulSoup no HTML renderizado
    soup = BeautifulSoup(html_content, 'html.parser')
    
    items = []
    table = soup.find('table', {'id': 'tabResult'})
    if table:
        for row in table.find_all('tr'):
            try:
                nome = row.find('span', class_='txtTit').get_text(strip=True)
                qtd_elem = row.find('span', class_='Rqtd')
                qtd = qtd_elem.get_text(strip=True).replace('Qtde.:', '') if qtd_elem else "1"
                val_elem = row.find('span', class_='valor')
                valor_total = val_elem.get_text(strip=True) if val_elem else "0.00"

                items.append({
                    "name": nome,
                    "quantity": qtd,
                    "total_value": valor_total
                })
            except Exception:
                continue

    loja_elem = soup.find('div', class_='txtTopo')
    loja_nome = loja_elem.get_text(strip=True) if loja_elem else "Desconhecido"

    return {
        "source": "scraper",
        "store": loja_nome,
        "items": items
    }