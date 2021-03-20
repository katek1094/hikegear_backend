import requests
from bs4 import BeautifulSoup
from requests.exceptions import ConnectionError


def scrape_backpack(url):
    results_data = {}
    error_counter = 0
    while True:
        try:
            page = requests.get(url)
        except ConnectionError:
            error_counter += 1
            if error_counter == 10:
                return False
            continue
        break
    if page.status_code == 400:
        return False
    soup = BeautifulSoup(page.text, 'html.parser')
    results_data['name'] = soup.find('h1', class_='lpListName').text
    description = soup.find(id='lpListDescription')
    if description:
        results_data['description'] = description.find('p').text
    else:
        results_data['description'] = ''
    categories = soup.find_all('li', class_='lpCategory')
    results_data['categories'] = []
    for category in categories:
        cat_data = {'name': category.find('h2', class_='lpCategoryName').text}
        items = category.find_all('li', class_='lpItem')
        cat_data['items'] = []
        for item in items:
            item_data = {'name': item.find('span', class_='lpName').text.strip(),
                         'description': item.find('span', class_='lpDescription').text.strip(),
                         'worn': False, 'consumable': False}
            worn = item.find('i', class_='lpSprite lpWorn lpActive')
            if worn:
                item_data['worn'] = True
            consumable = item.find('i', class_='lpSprite lpConsumable lpActive')
            if consumable:
                item_data['consumable'] = True
            item_data['weight'] = item.find('span', class_='lpWeight').text
            item_data['unit'] = item.find('div', class_='lpUnitSelect').find('span', class_='lpDisplay').text
            item_data['quantity'] = item.find('span', class_='lpQtyCell').text.strip()
            cat_data['items'].append(item_data)
        results_data['categories'].append(cat_data)
    return results_data


def import_backpack_from_lp(url):
    scrape_data = scrape_backpack(url)
    if not scrape_data:
        return False
    ready_to_json = {'name': scrape_data['name'], 'description': scrape_data['description'], 'list': []}
    categories_id_counter = 0
    items_id_counter = 0
    for category in scrape_data['categories']:
        ready_to_json['list'].append({
            'id': categories_id_counter,
            'name': category['name'],
            'items': []
        })
        categories_id_counter += 1
        for item in category['items']:
            if item['weight'] == '':
                item['weight'] = 0

            item['weight'] = float(item['weight'])
            if item['unit'] == 'g':
                pass
            elif item['unit'] == 'kg':
                item['weight'] = item['weight'] * 1000
            elif item['unit'] == 'oz':
                item['weight'] = item['weight'] * 28.35
            elif item['unit'] == 'lb':
                item['weight'] = item['weight'] * 453.59
            ready_to_json['list'][-1]['items'].append({
                'id': items_id_counter,
                'name': item['name'],
                'description': item['description'],
                'weight': item['weight'],
                'worn': item['worn'],
                'consumable': item['consumable'],
                'quantity': int(item['quantity']),
            })
            items_id_counter += 1
    return ready_to_json


# import_backpack_from_lp('https://lighterpack.com/r/p4e32a')
"""
python manage.py shell

from app.lpscraper import import_backpack_from_lp

exit()

"""
