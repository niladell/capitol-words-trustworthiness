from bs4 import BeautifulSoup as BSoup  # HTML data structure
import requests
import grequests
from tqdm import tqdm
import json


def get_text(req, link):
    try:
        bs = BSoup(req.text, "html.parser")
        corpus = bs\
            .find('main', {'id': 'content', 'role': 'main'})\
            .find('div', {'class': 'main-wrapper'})\
            .find('pre', {'class': 'styled'})
    except AttributeError:
        # if 'Page Not Found' in bs.find('main', {'id': 'content'}).text:
        #     return []
        # else:
        tqdm.write(f'Something weird with {req} from {link}')
        return ''
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
            tqdm.write(f'Saomething weird with {year}-{month}-{day}/{section}')
            return []
    elements = []

    section_reqs = []
    for row in tqdm(table.findAll('tr'), desc='Making requests', disable=True):
        cols = row.findAll('td')
        if len(cols) != 2:
            print(f'Warning in {cols}')
        link = cols[0]
        link = link.findAll('a', href=True)[0]['href']
        section_reqs.append(grequests.get(base_url + link))
        idp = cols[1].text
        elements.append({'link': link, 'page': idp})

    section_responses = grequests.map(section_reqs)
    for idx, resp in tqdm(enumerate(section_responses), desc='recv. section'):
        text = get_text(resp, elements[idx]['link'])
        elements[idx]['text'] = text
    return elements


year = 2018
months = range(1, 13)
days = range(1, 32)

records = []

# Not completely sure how this affects the process while in parallel.
s = requests.Session()

for month in tqdm(months, desc='Months'):
    for day in tqdm(days, desc='Days  '):
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
