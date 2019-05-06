import re
import argparse
from collections import defaultdict
import grequests
from bs4 import BeautifulSoup as BSoup  # HTML data structure
from tqdm import tqdm


def parse_bill_request(req, bill=None):
    if req is None:
        log_msg = f'Request was None for {bill}'
        tqdm.write(log_msg)
        write_log(log_msg)
        return 'REQUEST ERROR'
    bs = BSoup(req.text, "html.parser")

    title = bs.find('h1', {'class': 'legDetail'})
    if title is not None:
        title = title.text
    else:
        log_msg = f'BSoup parse of request was None for {bill}'
        tqdm.write(log_msg)
        write_log(log_msg)
        title = 'PARSE REQUEST ERROR'
    return title


def get_bills_in_text(text):
    pattern = re.compile(r"\<a href=\"(\/bill.+)\"\>.+\>")
    bill_names = []
    for match in re.finditer(pattern, text):
        bill = match.groups()[0]
        bill_names.append(bill)
    return bill_names


def setup_requests_for_bill_list(bill_list):
    base_url = "https://www.congress.gov"
    return [grequests.get(f'{base_url}{bill}') for bill in bill_list]


def map_requests_for_bill_list(bill_reqs):
    bill_responses = grequests.map(bill_reqs)
    return bill_responses


def process_requests_for_bill_list(bill_responses, bill_names):
    mentioned_bills = []
    for req, bill in zip(bill_responses, bill_names):
        bill_title = parse_bill_request(req, bill)
        mentioned_bills.append((bill, bill_title))
    if __debug__:
        tqdm.write('\n'.join([' -- '.join(itm) for itm in mentioned_bills]))
    return mentioned_bills


def write_log(log_msg):
    with open('parse_bill.log', 'a') as f:
        f.write(log_msg)
