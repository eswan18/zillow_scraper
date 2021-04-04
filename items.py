from dataclasses import dataclass


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
