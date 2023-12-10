from bs4 import BeautifulSoup
import aiohttp

async def fetch_and_parse(url: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            html = await response.text()
    soup = BeautifulSoup(html, 'html.parser')
    # Parse the data from the soup object and return it
    data = await parse_all_links(soup)
    return data

async def fetch_and_parse_product(url: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            html = await response.text()
    soup = BeautifulSoup(html, 'html.parser')
    # Extract the necessary data from the soup object
    title_div = soup.find('div', {'data-cy': 'ad_title'})
    title = title_div.find('h4').text
    description_div = soup.find('div', {'data-cy': 'ad_description'})
    description = description_div.find('div').text
    price_div = soup.find('div', {'data-testid': 'ad-price-container'})
    price = price_div.find('h3').text
    div_imgs = soup.find('div', {'class': 'swiper'})
    imgs = div_imgs.find_all('img')
    imgs = [img.get('src') for img in imgs]
    return {'title': title, 'description': description, 'price': price, 'images':imgs, 'url': url}

async def parse_all_links(soup):
    # Find all the product listings on the page
    div = soup.find('div', {'data-cy': 'l-card'})
    links = div.find_all('a')
    data = []
    for link in links:
        product_url = f"https://www.olx.uz/{link.get('href')}"
        product_data = await fetch_and_parse_product(product_url)
        data.append(product_data)
    return data

async def get_total_pages(url: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            html = await response.text()
    soup = BeautifulSoup(html, 'html.parser')
    # Find the last page number
    if soup.find('span', {'data-testid': 'total-count'}).text.strip() == 'Мы нашли  0 объявлений':
        return 'Мы нашли  0 объявлений'
    try:
        last_page_number = int(soup.find('ul', {'data-testid': 'pagination-list'}).find_all('li')[-1].text)
    except AttributeError:
        last_page_number = 1
    return last_page_number
