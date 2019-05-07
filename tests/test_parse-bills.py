import sys
sys.path.append('.')

from src.scrapper.parse_bills import  get_bills_in_text,\
                                      setup_requests_for_bill_list,\
                                      map_requests_for_bill_list,\
                                      process_requests_for_bill_list

base_url = "https://www.congress.gov"
sample_text = 'A bill (<a href=\"/bill/115th-congress/house-bill/4667\">H.R. 4667</a>) making further supplemental \n     appropriations for the fiscal year ending September 30, 2018,'
true_bill = ['/bill/115th-congress/house-bill/4667']
true_title = 'H.R.4667 - Making further supplemental appropriations for the fiscal year ending September 30, 2018, for disaster assistance for Hurricanes Harvey, Irma, and Maria, and calendar year 2017 wildfires, and for other purposes.115th Congress (2017-2018)'


def test_billparser():
    parsed_bill = get_bills_in_text(sample_text)
    assert true_bill == parsed_bill

def test_grequests():
    s_req = setup_requests_for_bill_list(true_bill)
    reqs = map_requests_for_bill_list(s_req)
    bills = process_requests_for_bill_list(reqs, true_bill)
    print(bills)
    assert [(true_bill[0], true_title)] == bills