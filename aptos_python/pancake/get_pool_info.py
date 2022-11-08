# 現在のプールのステーク状況をチェック
import os
import csv

import yaml

from aptos_sdk.account import Account
from aptos_sdk.account_address import AccountAddress
from aptos_sdk.client import RestClient
from aptos_sdk import ed25519


with open('../.aptos/config.yaml', 'r') as f:
    config = yaml.safe_load(f)

PRIVATE_KEY = config['profiles']['mainnet']['private_key']
NODE_URL = os.path.join(config['profiles']['mainnet']['rest_url'], 'v1')
PANCAKE_ADDRESS = '0xc7efb4076dbe143cbcd98cfaaa929ecfc8f299203dfff63b95ccb6bfe19850fa'


class wrappedRestClient(RestClient):
    def __init__(self, arg) -> None:
        super().__init__(arg)

    def account_resources(self, account_address: AccountAddress):
        response = self.client.get(
            f"{self.base_url}/accounts/{account_address}/resources"
        )
        return response.json()


private_key = ed25519.PrivateKey.from_hex(PRIVATE_KEY)
my_account = Account(
    account_address=AccountAddress.from_key(private_key.public_key()),
    private_key=private_key,
)
client = wrappedRestClient(NODE_URL)

aux_account = AccountAddress.from_hex(PANCAKE_ADDRESS)
resources = client.account_resources(aux_account)

with open('pancake/pancakeswap_pool.csv', 'w') as f:
    writer = csv.writer(f)
    writer.writerow(['pool_name', 'x_reserve', 'y_reserve'])
    for res in resources:
        module = res['type']
        if ('TokenPairReserve' in module):
            ret = client.account_resource(aux_account, module)
            writer.writerow([module, ret['data']['reserve_x'], ret['data']['reserve_y']])
