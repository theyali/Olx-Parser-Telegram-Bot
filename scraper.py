from bs4 import BeautifulSoup
import aiohttp


async def fetch_and_parse(url: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            html = await response.text()
    soup = BeautifulSoup(html, 'html.parser')
    print(url)
    # Parse the data from the soup object and return it
    async for product_data in parse_all_links(soup):
        yield product_data
    

def truncate_description(description, max_length=1000):
    """Сокращает описание до max_length символов, добавляя многоточие в конце."""
    if len(description) > max_length:
        return description[:max_length] + '.....'
    return description


async def fetch_and_parse_product(url: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            html = await response.text()
    soup = BeautifulSoup(html, 'html.parser')
    title=''
    try:
        title_div = soup.find('div', {'data-cy': 'ad_title'})
        title = title_div.find('h4').text
    except AttributeError:
        title = 'Нет названия'
    description = ''
    try:   
        description_div = soup.find('div', {'data-cy': 'ad_description'})
        description = description_div.find('div').text
        description = truncate_description(description, max_length=1000)
    except AttributeError:
        description = 'Нет описания'
    price = ''
    try:
        price_div = soup.find('div', {'data-testid': 'ad-price-container'})
        price = price_div.find('h3').text
    except:
        price = 'Нет цены'
    imgs =''
    try:
        div_imgs = soup.find('div', {'class': 'swiper'})
        imgs = div_imgs.find_all('img')
        imgs = [img.get('src') for img in imgs]
    except:
        imgs = 'Нет фото'
    return {'title': title, 'description': description, 'price': price, 'images':imgs, 'url': url}

async def parse_all_links(soup):
    links = soup.find_all('a', {'class': 'css-rc5s2u'})
    for link in links:
        href = link.get('href')
        product_url = f"https://www.olx.uz{href}"
        product_data = await fetch_and_parse_product(product_url)
        yield product_data

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
