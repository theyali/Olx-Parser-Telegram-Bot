from bs4 import BeautifulSoup
import aiohttp
import asyncio
import sys

async def get_html(url: str, should_continue, chat_id=None, home_url='https://www.olx.uz', retries: int = 10, delay: int = 1, long_delay: int = 240, bot= None):
    session = aiohttp.ClientSession()
    try:
        attempt = 0
        while attempt < retries:
            if not should_continue():
                return None

            try:
                async with session.get(home_url) as response:
                    pass
                async with session.get(url) as response:
                    if response.status == 200:
                        html = await response.text()
                        return html
                    else:
                        print(f"Attempt {attempt + 1} failed with status: {response.status}")
            except Exception as e:
                print(f"Attempt {attempt + 1} failed with exception: {e}")

            attempt += 1
            if attempt >= 10:
                if chat_id is not None:
                    await bot.send_message(chat_id, "⏳Ожидаем 4 минуты ⏳перед следующими попытками...")
                print("Ждем 4 минуты перед следующими попытками")
                await asyncio.sleep(long_delay)
                attempt = 0 
            else:
                await asyncio.sleep(delay)

        raise Exception(f"All {retries} retries failed")
    finally:
        await session.close()


async def fetch_and_parse(url: str, should_continue, chat_id, bot, keyword, processed_ids):
    html = await get_html(url, should_continue, chat_id=chat_id, bot=bot)
    try:
        soup = BeautifulSoup(html, 'html.parser')
    except:
        soup = None
    print(url)
    if chat_id is not None:
        await bot.send_message(chat_id, "Ожидаем новые объявления... ⏰")
    async for product_data in parse_all_links(soup, should_continue, keyword, processed_ids=processed_ids):
        yield product_data
    

def truncate_description(description, max_length=1000):
    """Сокращает описание до max_length символов, добавляя многоточие в конце."""
    if len(description) > max_length:
        return description[:max_length] + '.....'
    return description


async def fetch_and_parse_product(url: str, should_continue, keyword):
    html = await get_html(url, should_continue)
    try:
        soup = BeautifulSoup(html, 'html.parser')
    except:
        soup = None
    title=''
    try:
        title_div = soup.find('div', {'data-cy': 'ad_title'})
        title = title_div.find('h4').text
        if keyword.lower() not in title.lower():
            return None
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
    return {'id': url, 'title': title, 'description': description, 'price': price, 'images': imgs, 'url': url}

async def parse_all_links(soup, should_continue, keyword, processed_ids):
    links = soup.find_all('a', {'class': 'css-rc5s2u'})
    for link in links:
        href = link.get('href')
        product_url = f"https://www.olx.uz{href}"
        product_data = await fetch_and_parse_product(product_url, should_continue, keyword)
        if product_data and product_data['id'] not in processed_ids:
            processed_ids.add(product_data['id'])
            yield product_data

async def get_total_pages(url: str, should_continue, chat_id, bot):
    html = await get_html(url, should_continue, chat_id=chat_id, bot=bot)
    try:
        soup = BeautifulSoup(html, 'html.parser')
    except:
        soup = None
    if soup is not None:
        if soup.find('span', {'data-testid': 'total-count'}).text.strip() == 'Мы нашли  0 объявлений':
            return 'Мы нашли  0 объявлений'
        try:
            last_page_number = int(soup.find('ul', {'data-testid': 'pagination-list'}).find_all('li')[-1].text)
        except AttributeError:
            last_page_number = 1

        if last_page_number > 10:
            last_page_number = 10
        return last_page_number
