import sys
sys.path.append('.')

from src.scrapper.parse_bills import  get_bills_in_text

def test_billparser():
    sample_text = 'A bill (<a href=\"/bill/115th-congress/house-bill/4667\">H.R. 4667</a>) making further supplemental \n     appropriations for the fiscal year ending September 30, 2018,'
    true_bill = '/bill/115th-congress/house-bill/4667'
    true_title = 'H.R.4667 - Making further supplemental appropriations for the fiscal year ending September 30, 2018, for disaster assistance for Hurricanes Harvey, Irma, and Maria, and calendar year 2017 wildfires, and for other purposes.115th Congress (2017-2018)'

    parsed_bill = get_bills_in_text(sample_text)

    assert [(true_bill, true_title)] == parsed_bill

if __name__ == "__main__":
    test_billparser()
    print("Bill parser passed")