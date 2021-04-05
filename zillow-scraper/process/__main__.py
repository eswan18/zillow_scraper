import sys

import pandas as pd

date = sys.argv[1]

df = pd.read_json(f'raw_data/{date}.json')

# Get latitude and longitude for rows where it isn't already populated.
def extract_ll_from_id(_id):
    '''
    It seems like many properties that don't have lat/lon have an ID that
    contains their lat/lon.
    '''
    try:
        s = _id.lstrip('zpid_')
        lat, lon = s.split('-', 1)
        lat = float(lat)
        lon = float(lon)
        return lat, lon
    except:
        return None, None
no_lat = df.lat.isna()
new_lats = df.loc[no_lat, '_id'].apply(lambda _id: pd.Series(extract_ll_from_id(_id)))
df.loc[no_lat, 'lat'] = new_lats[0]
df.loc[no_lat, 'lon'] = new_lats[1]

df.to_json('clean_data/20210404.json')
