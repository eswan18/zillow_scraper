import urllib
import json
import re
from typing import Optional, Union, Any, List, Dict, Iterable
from dataclasses import dataclass

import requests
from bs4.element import Tag
from bs4 import BeautifulSoup


@dataclass
class Property:
    _id: str
    price: int
    address: str
    lat: Optional[float]
    lon: Optional[float]
    zipcode: Optional[str]
    url: str
    details: List[str]
    days_on_zillow: int
    json: Optional[Dict]


headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    "accept-encoding": "gzip, deflate, br",
    "accept-language": "en-US,en;q=0.8",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36",
}


chi_url = "https://www.zillow.com/chicago-il/rentals/?searchQueryState"
def make_query_state(page_num: int = 0) -> Dict[str, Any]:
    # The below reflects page 0 of a search for:
    # - Chicago
    # - For rent
    # - Rent: $0-$3000/month
    # - In-unit laundry
    # - 2+ Bedrooms
    query_state = {
        "pagination": {},
        "mapBounds": {
            "west": -88.09607811914063,
            "east": -87.36823388085938,
            "south": 41.217142667058575,
            "north": 42.444992337648856,
        },
        "regionSelection": [{"regionId": 17426, "regionType": 6}],
        "isMapVisible": False,
        "filterState": {
            "fsba": {"value": False},
            "fsbo": {"value": False},
            "nc": {"value": False},
            "fore": {"value": False},
            "cmsn": {"value": False},
            "auc": {"value": False},
            "pmf": {"value": False},
            "pf": {"value": False},
            "fr": {"value": True},
            "ah": {"value": True},
            "mf": {"value": False},
            "manu": {"value": False},
            "land": {"value": False},
            # Here begin the params I understand: beds, price, laundry, days on Zillow.
            "beds": {"min": 2},
            "mp": {"max": 3000},
            "price": {"max": 890941},
            "lau": {"value": True},
            "doz": {"value": "7"},
        },
        "isListVisible": True,
    }
    # If we're on a page other than 0, we need to add that to the query.
    if page_num > 0:
        query_state['pagination'] = {'currentPage': page_num}
    return query_state


def parse_property_card(card: Tag) -> Property:
    prop_id = card.article.attrs['id']
    details_card = card.article.find('ul', class_='list-card-details')
    details = [detail.text for detail in details_card.children]
    if daydiv := card.find('div', text=re.compile(r'days? on Zillow')):
        days_on_zillow_str = daydiv.text
        days_on_zillow = re.match(r'(\d+) day', days_on_zillow_str).group(1)
    else:
        # We might be wrong, but usually if the "days" string isn't found, it's
        # a different string like "1 hour ago" indicating less than a day.
        days_on_zillow = 0
    url = card.find('a', class_='list-card-link').attrs['href']
    address = card.find('address').text
    # Price text is sometimes "$1,500/mo", "$1,300+ 1bd", and "$1,700 1 bd".
    raw_price = card.find('div', class_='list-card-price').text
    price_str = re.match(r'\$(.*?)(\+?)[\s/]', raw_price).group(1)
    price = int(price_str.replace(',', ''))
    j_script = card.find('script', {'type': 'application/ld+json'})
    if j_script is not None:
        j = json.loads(j_script.contents[0])
        lat = j['geo'].get('latitude')
        lon = j['geo'].get('longitude')
        zipcode = j['address']['postalCode']
    else:
        j = lat = lon = zipcode = None

    return Property(
            _id=prop_id,
            price=price,
            address=address,
            lat=lat,
            lon=lon,
            zipcode=zipcode,
            url=url,
            details=details,
            days_on_zillow=days_on_zillow,
            json=j,
    )


def get_properties_from_content(content: Union[str, bytes]) -> Iterable[Property]:
    soup = BeautifulSoup(content, 'html.parser')
    potential_prop_cards = soup.find_all('ul', {'class': {'photo-cards'}})
    if len(potential_prop_cards) > 1:
        raise ValueError('Ambiguous situation in parsing -- too many photo-cards')
    else:
        prop_cards = potential_prop_cards[0]
    return (parse_property_card(card) for card in prop_cards.children
            if card.name == 'li' and card.article is not None)


with requests.Session() as s:
    for page_num in range(10):
        q_state = make_query_state(page_num)
        formatted_q_state = urllib.parse.quote(json.dumps(q_state))
        formatted_url = f"{chi_url}/?searchQueryState{formatted_q_state}"
        response = s.get(formatted_url, headers=headers)
        parsed = get_properties_from_content(response.content)
        break
        time.sleep(2)

