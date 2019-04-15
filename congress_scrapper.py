from bs4 import BeautifulSoup as BSoup  # HTML data structure
import requests
import numpy as np
from tqdm import tqdm
import json


def get_text(url):
    req = requests.get(url)
    try:
        corpus = BSoup(req.text, "html.parser")\
            .find('main', {'id': 'content', 'role': 'main'})\
            .find('div', {'class': 'main-wrapper'})\
            .find('pre', {'class': 'styled'})
    except AttributeError:
        if 'Page Not Found' in corpus.find('main', {'id': 'content'}).text:
            return []
        else:
            print(f'Something weird with {url}')
    return corpus.decode()


def get_session(s, year, month, day):
    base_url = "https://www.congress.gov"
    # year = '2019'
    # month = '4'
    # day = '4'
    section = 'senate-section'

    page_url =\
        f'{base_url}/congressional-record/{year}/{month}/{day}/{section}'
    # print(page_url)
    req = requests.get(page_url)
    sp = BSoup(req.content, "html.parser")
    try:
        table = sp.find('body')\
            .find('div', {'class': 'main-wrapper'})\
            .find('table')\
            .find('tbody')
        if not table:
            return []
    except AttributeError:
        if 'Page Not Found' in sp.find('main', {'id': 'content'}).text:
            return []
        else:
            print(f'Something weird with {year}-{month}-{day}/{section}')
            return []
    elements = []
    for row in tqdm(table.findAll('tr')):
        cols = row.findAll('td')
        if len(cols) != 2:
            print(f'Warning in {cols}')
        # element = [e.text for e in cols]
        link = cols[0]
        link = link.findAll('a', href=True)[0]['href']
        text = get_text(base_url + link)
        idp = cols[1].text
        elements.append([text, idp])
    return elements


year = 2018
months = range(1, 13)
days = range(1, 32)

records = []

# Not completely sure how this affects the process while in parallel.
s = requests.Session()

for month in tqdm(months):
    for day in tqdm(days):
        data = get_session(s, year, month, day)
        if not data:
            continue
        record = {
            'd': day,
            'm': month,
            'y': year,
            'data': data
        }
        records.append(record)

    with open('records.data', 'wb') as f:
        f.write(json.dumps(records).encode('ascii'))
# In[9]:

