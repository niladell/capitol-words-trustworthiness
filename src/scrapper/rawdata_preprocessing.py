import argparse
import json
import re
from tqdm import tqdm
from collections import OrderedDict
from ast import literal_eval
from parse_bills import get_bills_in_text,\
                        setup_requests_for_bill_list,\
                        map_requests_for_bill_list,\
                        process_requests_for_bill_list


def load_rawdata(filename):
    with open(filename, 'rb') as f:
        return json.load(f)


def array2datedic(raw):
    datedict = OrderedDict()
    for element in raw:
        datedict[(element['y'], element['m'], element['d'])] = element['data']
    return datedict


def keys_tuple2str(data):
    return {str(k): v for k, v in data.items()}


def keys_str2tuple(data):
    return {literal_eval(k): v for k, v in data.items()}


def save_data(filename, data):
    data = keys_tuple2str(data)
    with open(filename, 'wb') as f:
        f.write(json.dumps(data).encode('ascii'))


def load_data(filename):
    with open(filename, 'rb') as f:
        raw = json.load(f, object_pairs_hook=OrderedDict)
    return keys_str2tuple(raw)


def join_session(element):
    """Joins all the text files for a particular session"""
    if type(element) == str:
        return element
    return '\n'.join([a['text'] for a in element])


def join_multiple_sessions(raw, n, joining_element='\n______________\n1'):
    """Join several sessions into a single one

    Args:
        raw: Raw text
        n  : Indices of the segments to retireve
        joining_element (optional): How to join the elements

    Retruns:
        Single string of the selected snippet
    """
    return joining_element.join([join_session(element) for element in raw[n]])


def remove_record_head(text):
    """Delete the specific headers added by the GPO"""
    regex = r"<pre(.+?)the Government Publishing Office \[www.gpo.gov\]"
    regex = re.compile(regex, re.DOTALL)
    text = regex.sub("", text)
    text = re.sub(r'</pre>', '', text)
    return text


def remove_record_hlink(text):
    """Delete the link to the congressional record volume page"""
    regex = r"\[\[<a href=\"\/congressional-record(.+?)\]\]"
    regex = re.compile(regex, re.DOTALL)
    text = regex.sub("", text)
    return text


def remove_unnecessary_segment(session):
    # separator = '____________________'
    fragments_dictionary = [
        'PLEDGE OF ALLEGIANCE',
        'PRAY',
        'RECOGNITION OF THE MAJORITY LEADER'
    ]
    pruned_session = []
    for idx, record in enumerate(session):
        add = True
        for fragment in fragments_dictionary:
            # We are working with the "raw" format, meaning
            # that we have not yet unified all the text in a
            # single block... it may be a bit overcomplciated
            if fragment in record['text']:  # TODO Write tests/quite tricky format here
                add = False
        if add:
            pruned_session.append(session[idx])
    return pruned_session


def clean_session(session):
    session = remove_unnecessary_segment(session)
    return session


def clean_text(text):
    text = remove_record_head(text)
    text = remove_record_hlink(text)
    return text


def group_list_by_indices(ungrouped_list, indices, forced_length=None):
    """Groups list of elements into a list of lists based on the indices.
    E.g. ungrouped list: ['a','b','c','d','e'], indices: [0, 0, 1, 1, 2]
         output: [['a','b'], ['c','d'], ['e']]

         Disclaimer: The indices list is assumed to be ordered, meaning that
          it is assumed that indices[i] >= indices[j] if i>j. Also the order
          of the elements inside the final sub-lists is gonna be preserved.
    """
    if not ungrouped_list:
        return [[]]
    if not forced_length:
        forced_length = len(indices)
    grouped_list = []
    sub_list = []
    index_counter = 0
    i = 0
    while i < forced_length:
        if indices[index_counter] == i:
            sub_list.append(ungrouped_list[index_counter])
            index_counter += 1
            if index_counter >= len(indices):
                break
        else:
            grouped_list.append(sub_list[:])
            sub_list = []
            i += 1
    grouped_list.append(sub_list)
    # Extend the list with empty sub-lists till the required lenght
    assert len(grouped_list) <= forced_length,\
            'List is larger than required length'
    grouped_list.extend([
        [] for i in range(forced_length - len(grouped_list))
                            ])
    return grouped_list


def convert_rawfile(filename):
    data = load_rawdata(filename)
    data = array2datedic(data)
    for key, element in tqdm(data.items()):
        element = clean_session(element)  # Element: [{link: , page:, text:}]
        # text = join_session(element)  # Join session segments into unique txt

        # We need to use a bit of a more convoluted structure as doing
        # individual requests is usually very slow. We try to first extract
        # the bills from several segments (snippets) and then parallely do the
        # website requests.
        bill_names = []
        bill_requests = []
        bill_request_indices = []
        snippets_list = []
        for idx, snippet in tqdm(enumerate(element)):
            snippet = clean_text(snippet['text'])
            snippets_list.append(snippet)
            # Parse the bill names
            bills_in_snippet = get_bills_in_text(snippet)
            bill_names.append(bills_in_snippet)
            # DO grequests.get for each of the mentioned bills
            bill_requests += setup_requests_for_bill_list(bills_in_snippet)
            bill_request_indices += [idx]*len(bills_in_snippet)
        # Map all requests and re-group list by the snippet index
        bill_responses = map_requests_for_bill_list(bill_requests)
        n_element = len(element)
        bill_responses = group_list_by_indices(bill_responses,
                                               bill_request_indices,
                                               n_element)

        new_element = []
        for snippet, name, response in\
                tqdm(zip(snippets_list, bill_names, bill_responses)):
            bills = process_requests_for_bill_list(response, name)
            new_element.append({'text': snippet, 'bills': bills})
        # tqdm.write('\n'.join(bills_list))  # Redundant right now
        data[key] = new_element
    save_data(filename + '.clean', data)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Convert the raw scrapped' +
                                     'data into an orderedDict by date')
    parser.add_argument('filename', type=str,
                        help='Name of the raw data file.')

    args = parser.parse_args()
    convert_rawfile(args.filename)
