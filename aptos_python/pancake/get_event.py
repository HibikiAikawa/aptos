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
EVENT_NAME = f'{PANCAKE_ADDRESS}::swap::PairEventHolder<{APT_COIN}, {USDC_COIN}>'
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


def preprocessing_dict(response):
    ret = {}
    for name in response:
        if isinstance(response[name], dict):
            ret.update(**response[name])
        else:
            ret.update({name: response[name]})

    return ret


def append_dict(responses):
    _list = []
    for response in responses:
        d = preprocessing_dict(response)
        _list.append(d)
    return _list


# response_swap = client.get_event(PANCAKE_ADDRESS, EVENT_NAME, 'swap', params)
# response_addliq = client.get_event(PANCAKE_ADDRESS, EVENT_NAME, 'add_liquidity', params)

def create_event_df(address, event_name, filter):
    start = 1
    _r = client.get_event(address, event_name, filter, {'limit':1})
    max_sequence_number = _r[-1]['sequence_number']
    all_list = []
    df = pd.DataFrame()
    with tqdm() as pbar:
        while True:
            params = {'start': start, 'limit': LIMIT}
            responses = client.get_event(address, event_name, filter, params)
            sequence_number = responses[-1]['sequence_number']
            start = int(sequence_number) + 1
            _list = append_dict(responses)
            all_list.extend(_list)
            if int(max_sequence_number) - int(sequence_number) <= 0:
                break
            pbar.update(1)
            time.sleep(0.1)
    
    df = pd.DataFrame.from_dict(all_list)
    return df


# event_pair_created = f'{PANCAKE_ADDRESS}::swap::SwapInfo'
# print('collecting pair create event')
# pair_df = create_event_df(PANCAKE_ADDRESS, event_pair_created, 'pair_created')
# pair_df.to_csv('data/pancakeswap/pancakeswap_pair_log.csv')

print('collecting burn log')
burn_df = create_event_df(PANCAKE_ADDRESS, EVENT_NAME, 'remove_liquidity')
burn_df.to_csv('data/burn_log.csv')

print('collecting mint log')
burn_df = create_event_df(PANCAKE_ADDRESS, EVENT_NAME, 'add_liquidity')
burn_df.to_csv('data/mint_log.csv')

print('collecting swap log')
burn_df = create_event_df(PANCAKE_ADDRESS, EVENT_NAME, 'swap')
burn_df.to_csv('data/swap_log.csv')