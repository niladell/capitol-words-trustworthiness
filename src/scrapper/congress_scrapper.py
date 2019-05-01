from bs4 import BeautifulSoup as BSoup  # HTML data structure
import argparse
import requests
import grequests
from tqdm import tqdm
import json


def get_text(req, link='<link not defined>', idx='<idx not defined>'):
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
        error_text = f'Something weird with {req} from {link}'
        with open('failed_records.log', 'a') as f:
            f.write(error_text + '\n')
        tqdm.write(error_text)
        return '<ERROR IN REQUEST>'
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
            error_text = f'Something weird with {year}-{month}-{day}/{section}'
            tqdm.write(error_text)
            with open('failed_sessions.log', 'a') as f:
                f.write(error_text)
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
        identifier = f'<({year}/{month}/{day} -- {idx})>'
        text = get_text(resp, elements[idx]['link'], identifier)
        elements[idx]['text'] = text
    return elements


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Scrap data from the US ' +
                                     'Congressional Records.')
    parser.add_argument('start', type=str,
                        help='Start date (format YYYY/MM/DD).')
    parser.add_argument('end',  type=str,
                        help='End date (same format as start).')

    args = parser.parse_args()

    (year_s, month_s, day_s) = map(int, args.start.split('/'))
    (year_e, month_e, day_e) = map(int, args.end.split('/'))

    years = range(year_s, year_e + 1)
    months = range(month_s, month_e + 1)
    # days = range(day_s, day_e + 1) # Useless right now

    records = []

    # Not completely sure how this affects the process while in parallel.
    s = requests.Session()
    year = list(years)[0]  # TODO Add loop for years
    for month in tqdm(months, desc='Months'):
        # TODO isn't there a nicer way to do this
        if month == month_s and month == month_e:
            days = range(day_s, day_e + 1)
        elif month == month_s:
            days = range(day_s, 32)
        elif month == month_e:
            days = range(1, day_e + 1)
        else:
            days = range(1, 32)

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

        with open('records_{}-to-{}.data'.format(args.start.replace('/', '-'),
                                                 args.end.replace('/', '-')),
                  'wb') as f:
            f.write(json.dumps(records).encode('ascii'))
