import time
import json
import re
from typing import Union, Iterable

import requests
from bs4.element import Tag
from bs4 import BeautifulSoup

from items import Property
from zillow import get_search_page


def parse_property_card(card: Tag) -> Property:
    prop_id = card.article.attrs["id"]
    details_card = card.article.find("ul", class_="list-card-details")
    details = [detail.text for detail in details_card.children]
    if daydiv := card.find("div", text=re.compile(r"days? on Zillow")):
        days_on_zillow_str = daydiv.text
        days_on_zillow = re.match(r"(\d+) day", days_on_zillow_str).group(1)
    else:
        # We might be wrong, but usually if the "days" string isn't found, it's
        # a different string like "1 hour ago" indicating less than a day.
        days_on_zillow = 0
    url = card.find("a", class_="list-card-link").attrs["href"]
    address = card.find("address").text
    # Price text is sometimes "$1,500/mo", "$1,300+ 1bd", and "$1,700 1 bd".
    raw_price = card.find("div", class_="list-card-price").text
    price_str = re.match(r"\$(.*?)(\+?)[\s/]", raw_price).group(1)
    price = int(price_str.replace(",", ""))
    j_script = card.find("script", {"type": "application/ld+json"})
    if j_script is not None:
        j = json.loads(j_script.contents[0])
        lat = j["geo"].get("latitude")
        lon = j["geo"].get("longitude")
        zipcode = j["address"]["postalCode"]
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
    soup = BeautifulSoup(content, "html.parser")
    potential_prop_cards = soup.find_all("ul", {"class": {"photo-cards"}})
    if len(potential_prop_cards) > 1:
        raise ValueError("Ambiguous situation in parsing -- too many photo-cards")
    else:
        prop_cards = potential_prop_cards[0]
    return (
        parse_property_card(card)
        for card in prop_cards.children
        if card.name == "li" and card.article is not None
    )


with requests.Session() as s:
    for page_num in range(10):
        page = get_search_page(session=s, page_num=page_num)
        parsed = get_properties_from_content(page)
        break
        time.sleep(2)
