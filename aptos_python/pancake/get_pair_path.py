import os
import time
import csv
from pprint import pprint

import pandas as pd
from tqdm import tqdm
import yaml
from aptos_sdk.client import RestClient

with open('.aptos/config.yaml', 'r') as f:
    config = yaml.safe_load(f)

PRIVATE_KEY = config['profiles']['mainnet']['private_key']
NODE_URL = os.path.join(config['profiles']['mainnet']['rest_url'], 'v1')
PANCAKE_ADDRESS = '0xc7efb4076dbe143cbcd98cfaaa929ecfc8f299203dfff63b95ccb6bfe19850fa'

APT_COIN = '0x1::aptos_coin::AptosCoin'
USDC_COIN = '0xf22bede237a07e121b56d91a491eb7bcdfd1f5907926a9e58338f964a01b17fa::asset::USDC'
EVENT_NAME = f'{PANCAKE_ADDRESS}::swap::SwapInfo'
LIMIT = 100


class wrappedRestClient(RestClient):
    def __init__(self, url) -> None:
        super().__init__(url)

    def get_event(self, address, event_handle, field_name, params=None):
        # https://fullnode.devnet.aptoslabs.com/v1/accounts/{address}/events/{event_handle}/{field_name}
        uri = os.path.join('https://aptos-mainnet-archive.allthatnode.com/v1', 'accounts', str(address), 'events', event_handle, field_name)
        response = self.client.get(uri, params=params)
        return response.json()


client = wrappedRestClient(NODE_URL)


res = client.get_event(PANCAKE_ADDRESS, EVENT_NAME, 'pair_created', {'limit':1})
print(res)