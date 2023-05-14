"""
This script should be created as a Lambda function to proxy data from the
Etsy API v3. It pulls listings for a specified shop name.
"""
import json
import math
import os
import urllib.error
import urllib.request

import boto3


ETSY_CLIENT_ID = os.environ.get("ETSY_CLIENT_ID", "")
ETSY_SHOP_NAME = os.environ.get("ETSY_SHOP_NAME", "")
ETSY_ACCESS_TOKEN = os.environ.get("ETSY_ACCESS_TOKEN", "")
ETSY_REFRESH_TOKEN = os.environ.get("ETSY_REFRESH_TOKEN", "")

ETSY_HEADERS = {
    "content-type": "application/x-www-form-urlencoded",
    "authorization": f'Bearer {ETSY_ACCESS_TOKEN}',
    "x-api-key": ETSY_CLIENT_ID,
}


def _request(endpoint, query, payload=None):
    if query:
        params = urllib.parse.urlencode(query)
        endpoint = f'{endpoint}?{params}'

    data = None
    if payload:
        data = urllib.parse.urlencode(payload).encode("ascii")

    print("endpoint: " + endpoint)
    request = urllib.request.Request(endpoint, headers=ETSY_HEADERS, data=data)
    response = urllib.request.urlopen(request)
    result = response.read()
    print("result: " + result.decode("utf-8"))
    return result


def _get(endpoint, query):
    return _request(endpoint, query)


def _post(endpoint, query, payload):
    return _request(endpoint, query, payload)


def refresh_oauth_token():
    payload = {
        "grant_type": "refresh_token",
        "client_id": ETSY_CLIENT_ID,
        "refresh_token": ETSY_REFRESH_TOKEN,
    }
    response = _post("https://api.etsy.com/v3/public/oauth/token", None, payload)
    result = json.loads(response)

    client = boto3.client('lambda')
    response = client.update_function_configuration(
        FunctionName='MissMeiKeiEtsyProxy',
        Environment={
            'Variables': {
                "ETSY_CLIENT_ID": ETSY_CLIENT_ID,
                "ETSY_SHOP_NAME": ETSY_SHOP_NAME,
                'ETSY_ACCESS_TOKEN': result["access_token"],
                'ETSY_REFRESH_TOKEN': result["refresh_token"],
            }
        }
    )
    print(response)
    return response


def get_shop_id(shop_name):
    response = _get(
        f'https://openapi.etsy.com/v3/application/shops?shop_name={shop_name}',
        None)
    result = json.loads(response)
    return result["results"][0]["shop_id"]


def get_shop_listing(shop_id, limit, page):
    data = {"results": [], "next_page": 0}

    response = _get(
        f'https://openapi.etsy.com/v3/application/shops/{shop_id}/listings/active',
        {"limit": limit, "offset": limit * page})
    result = json.loads(response)

    count = result["count"]
    pages = math.ceil(count / limit)
    next_page = page + 1
    if next_page >= pages:
        next_page = 0
    data["next_page"] = next_page

    listings = result["results"]
    listing_ids = ",".join(map(lambda listing: str(listing["listing_id"]), listings))
    response = _get(f'https://openapi.etsy.com/v3/application/listings/batch', {
        "listing_ids": listing_ids,
        "includes": "Images",
    })
    result = json.loads(response)

    listings = result["results"]
    for listing in listings:
        price = listing["price"]["amount"] / listing["price"]["divisor"]
        data["results"].append({
            "title": listing["title"],
            "price": "${:0,.2f}".format(price),
            "url": listing["url"],
            "image": listing["images"][0],
        })

    return data


def main(event, _context):
    print("event: " + str(event))
    data = json.loads(event.get("body", "{}"))
    listings = {}

    try:
        shop_name = data.get("shop_name", ETSY_SHOP_NAME)
        limit = data.get("limit", 12)
        page = data.get("page", 0)
        shop_id = get_shop_id(shop_name)
        listings = get_shop_listing(shop_id, limit, page)

    except Exception as error:
        print(error)

    finally:
        refresh_oauth_token()
        return listings
