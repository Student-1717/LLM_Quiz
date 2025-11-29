from bs4 import BeautifulSoup

def extract_tables_from_html(html):
    soup = BeautifulSoup(html, "lxml")
    tables = soup.find_all("table")
    return tables
