# 現在のプールのステーク状況をチェック(devnetだとまともに動いているのがない)
import os

import yaml

from aptos_sdk.account import Account
from aptos_sdk.account_address import AccountAddress
from aptos_sdk.client import RestClient
from aptos_sdk import ed25519


with open('../.aptos/config.yaml', 'r') as f:
    config = yaml.safe_load(f)

PRIVATE_KEY = config['profiles']['devnet']['private_key']
NODE_URL = os.path.join(config['profiles']['devnet']['rest_url'], 'v1')
AUX_ADDRESS = '0xea383dc2819210e6e427e66b2b6aa064435bf672dc4bdc55018049f0c361d01a'


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

aux_account = AccountAddress.from_hex(AUX_ADDRESS)
resources = client.account_resources(aux_account)

for res in resources:
    module = res['type']
    if ('amm' in module) and ('Pool' in module):
        ret = client.account_resource(aux_account, module)
        print(module)
        print('x', ret['data']['x_reserve'])
        print('y', ret['data']['y_reserve'])
