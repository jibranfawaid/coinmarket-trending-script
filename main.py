import re

import concurrent.futures
import requests
from bs4 import BeautifulSoup
import json

date_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$')
https_pattern = re.compile(r'^https://')

list_of_asset = []


def process_page(page_num, seen_ids):
    print(f"Writing page number: {page_num + 1}")
    url = f'https://coinmarketcap.com/?page={page_num + 1}'
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    script = soup.find('script', id='__NEXT_DATA__')
    array_of_asset = json.loads(str(script.contents[0]))
    array_of_asset = json.loads(str(array_of_asset["props"]["initialState"]))
    array_of_asset["cryptocurrency"]["listingLatest"]["data"].pop(0)
    array_of_asset = array_of_asset["cryptocurrency"]["listingLatest"]["data"]
    results = []
    for asset in array_of_asset:
        flag = 0
        quote_id = asset[6]
        if type(quote_id) == str or quote_id is None:
            quote_id = asset[12]
        if quote_id in seen_ids:
            continue
        seen_ids.add(quote_id)
        asset_name = ""
        asset_symbol = ""
        for index, asset_detail in reversed(list(enumerate(asset))):
            if type(asset_detail) == str:
                if not date_pattern.match(asset_detail) and not https_pattern.match(asset_detail):
                    if flag == 0:
                        asset_symbol = asset_detail
                    elif flag == 3:
                        asset_name = str(asset_detail).replace("'", "''")
                    flag += 1
        results.append({
            "quote_id": quote_id,
            "asset_name": asset_name,
            "asset_symbol": asset_symbol,
        })
    return results


def get_quote_id(asset):
    return asset['quote_id']


if __name__ == '__main__':
    seen_ids = set()
    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = []
        for page_num in range(92):
            future = executor.submit(process_page, page_num, seen_ids)
            results.append(future)
        for result in concurrent.futures.as_completed(results):
            list_of_asset.extend(result.result())

    # create a list of the quote_id values
    quote_ids = [get_quote_id(asset) for asset in list_of_asset]

    # sort the quote_id values
    sorted_ids = sorted(quote_ids)

    # create a new list with the assets in the sorted order
    sorted_assets = [list_of_asset[quote_ids.index(id)] for id in sorted_ids]

    # replace the original list with the sorted list
    list_of_asset = sorted_assets

    for asset in list_of_asset:
        with open('list_of_assets.txt', 'a') as f:
            f.write(
                f"Quote ID: {asset['quote_id']}, Asset Name: {asset['asset_name']}, Asset Symbol: {asset['asset_symbol']}")
            f.write('\n')
    print("FINISH")