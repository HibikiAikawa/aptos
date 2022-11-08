import os
import time
import csv

import yaml

from aptos_sdk.account import Account
from aptos_sdk.account_address import AccountAddress
from aptos_sdk.client import RestClient
from aptos_sdk import ed25519


with open('pancake/rate_history.csv', 'w') as f:
    writer = csv.writer(f)
    writer.writerow(['rate', 'version'])

with open('../.aptos/config.yaml', 'r') as f:
    config = yaml.safe_load(f)

PRIVATE_KEY = config['profiles']['mainnet']['private_key']
NODE_URL = os.path.join(config['profiles']['mainnet']['rest_url'], 'v1')
PANCAKE_ADDRESS = '0xc7efb4076dbe143cbcd98cfaaa929ecfc8f299203dfff63b95ccb6bfe19850fa'

APT_COIN = '0x1::aptos_coin::AptosCoin'
USDC_COIN = '0xf22bede237a07e121b56d91a491eb7bcdfd1f5907926a9e58338f964a01b17fa::asset::USDC'
RESOURCE_NAME = f'{PANCAKE_ADDRESS}::swap::TokenPairReserve<{APT_COIN}, {USDC_COIN}>'
EVENT_NAME = f'{PANCAKE_ADDRESS}::swap::PairEventHolder<{APT_COIN}, {USDC_COIN}>'
FIELD_NAME = 'swap'


class wrappedRestClient(RestClient):
    def __init__(self, url) -> None:
        super().__init__(url)

    def get_event(self, address: AccountAddress, event_handle, field_name):
        # https://fullnode.devnet.aptoslabs.com/v1/accounts/{address}/events/{event_handle}/{field_name}
        response = self.client.get(os.path.join(self.base_url, 'accounts', str(address), 'events', event_handle, field_name))
        return response.json()


def from_octa(amount, decimals):
    if isinstance(amount, str):
        amount = int(amount)
    return amount / 10**decimals


def calc_rate(apt_reserve, usdc_reserve, fee):
    apt_reserve = from_octa(apt_reserve, 8)
    usdc_reserve = from_octa(usdc_reserve, 6)
    return usdc_reserve*fee/apt_reserve


# client作成
private_key = ed25519.PrivateKey.from_hex(PRIVATE_KEY)
my_account = Account(
    account_address=AccountAddress.from_key(private_key.public_key()),
    private_key=private_key,
)
client = wrappedRestClient(NODE_URL)
pancake_account = AccountAddress.from_hex(PANCAKE_ADDRESS)

# 初期流動性のチェック
response = client.account_resource(pancake_account, RESOURCE_NAME)
apt_reserve = int(response['data']['reserve_x'])
usdc_reserve = int(response['data']['reserve_y'])


response_swap = client.get_event(pancake_account, EVENT_NAME, 'swap')
response_addliq = client.get_event(pancake_account, EVENT_NAME, 'add_liquidity')
response_remliq = client.get_event(pancake_account, EVENT_NAME, 'remove_liquidity')

sn_swap_pre = response_swap[-1]['sequence_number']
sn_addliq_pre = response_addliq[-1]['sequence_number']
sn_remliq_pre = response_remliq[-1]['sequence_number']


while True:
    responses = []

    # swap
    response = client.get_event(pancake_account, EVENT_NAME, 'swap')
    sequence_number = response[-1]['sequence_number']
    if (int(sequence_number) > int(sn_swap_pre)):
        num = int(sequence_number) - int(sn_swap_pre)
        responses.extend(response[-num:])
        sn_swap_pre = sequence_number

    # add liquidity
    response = client.get_event(pancake_account, EVENT_NAME, 'add_liquidity')
    sequence_number = response[-1]['sequence_number']
    if (int(sequence_number) > int(sn_addliq_pre)):
        num = int(sequence_number) - int(sn_addliq_pre)
        responses.extend(response[-num:])
        sn_addliq_pre = sequence_number

    # remove liquidity
    response = client.get_event(pancake_account, EVENT_NAME, 'remove_liquidity')
    sequence_number = response[-1]['sequence_number']
    if (int(sequence_number) > int(sn_remliq_pre)):
        num = int(sequence_number) - int(sn_remliq_pre)
        responses.extend(response[-num:])
        sn_remliq_pre = sequence_number

    # 全イベントを合わせてversion順にソート
    responses = sorted(responses, key=lambda x: x['version'])

    for res in responses:
        type = res['type']
        version = res['version']
        if 'SwapEvent' in type:
            amount_x_in = res['data']["amount_x_in"]
            amount_x_out = res['data']["amount_x_out"]
            amount_y_in = res['data']["amount_y_in"]
            amount_y_out = res['data']["amount_y_out"]
            if amount_x_in == '0':
                apt_amount = (-1) * int(amount_x_out)
                usdc_amount = int(amount_y_in)
            else:
                apt_amount = int(amount_x_in)
                usdc_amount = (-1) * int(amount_y_out)
        elif 'AddLiquidityEvent' in type:
            apt_amount = int(res['data']["amount_x"])
            usdc_amount = int(res['data']["amount_y"])
        elif 'RemoveLiquidityEvent' in type:
            apt_amount = (-1) * int(res['data']["amount_x"])
            usdc_amount = (-1) * int(res['data']["amount_y"])
        apt_reserve += apt_amount
        usdc_reserve += usdc_amount
        rate = calc_rate(apt_reserve, usdc_reserve, 0.9975)
        print(f'rate: {rate:.04f} USDC apt_reserve: {apt_reserve} usdc_reserve: {usdc_reserve} version: {version}')

    # test用
    response = client.account_resource(pancake_account, RESOURCE_NAME)
    apt_reserve_test = int(response['data']['reserve_x'])
    usdc_reserve_test = int(response['data']['reserve_y'])
    if ((apt_reserve_test != apt_reserve) or (usdc_reserve_test != usdc_reserve)):
        raise ValueError()

    time.sleep(5)
