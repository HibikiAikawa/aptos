import os
import time
import csv

import yaml

from aptos_sdk.account import Account
from aptos_sdk.account_address import AccountAddress
from aptos_sdk.client import RestClient
from aptos_sdk import ed25519


with open('aux/rate_history.csv', 'w') as f:
    writer = csv.writer(f)
    writer.writerow(['rate', 'version', 'sequence_number'])

with open('../.aptos/config.yaml', 'r') as f:
    config = yaml.safe_load(f)

PRIVATE_KEY = config['profiles']['mainnet']['private_key']
NODE_URL = os.path.join(config['profiles']['mainnet']['rest_url'], 'v1')


AUX_ADDRESS = "0xbd35135844473187163ca197ca93b2ab014370587bb0ed3befff9e902d6bb541"
USDC_COIN = "0x5e156f1207d0ebfa19a9eeff00d62a282278fb8719f4fab3a586a0a2c0fffbea::coin::T"
APT_COIN = "0x1::aptos_coin::AptosCoin"
RESOURCE_NAME = f'{AUX_ADDRESS}::amm::Pool<{APT_COIN}, {USDC_COIN}>'


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


def get_pool_info(response):
    version = response['version']
    if response['data']['in_coin_type'] == APT_COIN:
        apt_amount = int(response['data']['in_au'])
        apt_reserve = int(response['data']['in_reserve'])
        usdc_amount = (-1) * int(response['data']['out_au'])
        usdc_reserve = int(response['data']['out_reserve'])
    else:
        usdc_reserve = int(response['data']['in_reserve'])
        usdc_amount = int(response['data']['in_au'])
        apt_amount = (-1) * int(response['data']['out_au'])
        apt_reserve = int(response['data']['out_reserve'])

    return apt_amount, usdc_amount, apt_reserve, usdc_reserve, version


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
aux_account = AccountAddress.from_hex(AUX_ADDRESS)

# 初期流動性の取得
response = client.account_resource(aux_account, RESOURCE_NAME)
apt_reserve = int(response['data']['x_reserve']['value'])
usdc_reserve = int(response['data']['y_reserve']['value'])

#########
response_swap = client.get_event(aux_account, RESOURCE_NAME, 'swap_events')
response_addliq = client.get_event(aux_account, RESOURCE_NAME, 'add_liquidity_events')
response_remliq = client.get_event(aux_account, RESOURCE_NAME, 'remove_liquidity_events')
'''
import json
print(json.dumps(response_swap[-1],indent=2))
print(json.dumps(response_addliq[-1],indent=2))
print(json.dumps(response_remliq[-1],indent=2))
exit()
'''

sn_swap_pre = response_swap[-1]['sequence_number']
sn_addliq_pre = response_addliq[-1]['sequence_number']
sn_remliq_pre = response_remliq[-1]['sequence_number']


while True:
    responses = []

    # swap
    response = client.get_event(aux_account, RESOURCE_NAME, 'swap_events')
    sequence_number = response[-1]['sequence_number']
    if (int(sequence_number) > int(sn_swap_pre)):
        num = int(sequence_number) - int(sn_swap_pre)
        responses.extend(response[-num:])
        sn_swap_pre = sequence_number

    # add liquidity
    response = client.get_event(aux_account, RESOURCE_NAME, 'add_liquidity_events')
    sequence_number = response[-1]['sequence_number']
    if (int(sequence_number) > int(sn_addliq_pre)):
        num = int(sequence_number) - int(sn_addliq_pre)
        responses.extend(response[-num:])
        sn_addliq_pre = sequence_number

    # remove liquidity
    response = client.get_event(aux_account, RESOURCE_NAME, 'remove_liquidity_events')
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
            apt_amount, usdc_amount, apt_reserve, usdc_reserve, version = get_pool_info(res)
        elif 'AddLiquidityEvent' in type:
            apt_amount = int(res['data']["x_added_au"])
            usdc_amount = int(res['data']["y_added_au"])
        elif 'RemoveLiquidityEvent' in type:
            apt_amount = (-1) * int(res['data']["x_removed_au"])
            usdc_amount = (-1) * int(res['data']["y_removed_au"])
        apt_reserve += apt_amount
        usdc_reserve += usdc_amount
        rate = calc_rate(apt_reserve, usdc_reserve, 0.9990)
        print(f'rate: {rate:.04f} USDC apt_reserve: {apt_reserve} usdc_reserve: {usdc_reserve} version: {version}')

    # test用
    response = client.account_resource(aux_account, RESOURCE_NAME)
    apt_reserve_test = int(response['data']['x_reserve']['value'])
    usdc_reserve_test = int(response['data']['y_reserve']['value'])
    if ((apt_reserve_test != apt_reserve) or (usdc_reserve_test != usdc_reserve)):
        raise ValueError()

    time.sleep(5)

#########
response = client.get_event(aux_account, RESOURCE_NAME, 'swap')
sequence_number_pre = response[-1]['sequence_number']
while True:
    response = client.get_event(aux_account, RESOURCE_NAME, FIELD_NAME)
    sequence_number = response[-1]['sequence_number']
    if (int(sequence_number) > int(sequence_number_pre)):
        num = int(sequence_number) - int(sequence_number_pre)

        for i in range(-1 * num, 0, 1):
            apt_amount, usdc_amount, apt_reserve, usdc_reserve, sequence_number, version = get_pool_info(response, i)
            apt_reserve += apt_amount
            usdc_reserve += usdc_amount
            apt_reserve = from_octa(apt_reserve, 8)
            usdc_reserve = from_octa(usdc_reserve, 6)
            rate = usdc_reserve * 0.9990 / apt_reserve
            with open('aux/rate_history.csv', 'a') as f:
                writer = csv.writer(f)
                writer.writerow([rate, version, sequence_number])
            print(f'apt {rate:.04f} USDC version: {version} sequence_number: {sequence_number}')

        sequence_number_pre = sequence_number
    time.sleep(5)
