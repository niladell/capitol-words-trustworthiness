import re
import argparse
from collections import defaultdict
import grequests
from bs4 import BeautifulSoup as BSoup  # HTML data structure
from tqdm import tqdm


def download_bill(req):
    bs = BSoup(req.text, "html.parser")

    title = bs.find('h1', {'class': 'legDetail'})
    if title is not None:
        title = title.text
    else:
        tqdm.write(f'Weird thing with ')
        title = ''
    return title


def get_bills_in_text(text):
    base_url = "https://www.congress.gov"
    pattern = re.compile(r"\<a href=\"(\/bill.+)\"\>.+\>")
    bill_names = []
    bill_reqs = []
    for match in re.finditer(pattern, text):
        bill = match.groups()[0]
        bill_names.append(bill)
        bill_reqs.append(grequests.get(f"{base_url}{bill}"))

    mentioned_bills = []
    for req, bill in zip(bill_reqs, mentioned_bills):
        bill_title = download_bill(req)
        mentioned_bills.append((bill, bill_title))
    if __debug__:
        tqdm.write('\n'.join([' -- '.join(itm) for itm in mentioned_bills]))
    return mentioned_bills