import os
import time

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
AUX_ADDRESS = "0xbd35135844473187163ca197ca93b2ab014370587bb0ed3befff9e902d6bb541"

WARMHOLE_USDC_COIN = "0x5e156f1207d0ebfa19a9eeff00d62a282278fb8719f4fab3a586a0a2c0fffbea::coin::T"
APT_COIN = "0x1::aptos_coin::AptosCoin"
LAYERZERO_USDC_COIN = '0xf22bede237a07e121b56d91a491eb7bcdfd1f5907926a9e58338f964a01b17fa::asset::USDC'
PANCAKE_RESOURCE_NAME = f'{PANCAKE_ADDRESS}::swap::TokenPairReserve<{APT_COIN}, {LAYERZERO_USDC_COIN}>'
AUX_RESOURCE_NAME = f'{AUX_ADDRESS}::amm::Pool<{APT_COIN}, {WARMHOLE_USDC_COIN}>'


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


def get_rate_aux(client, account, resource_name, x_decimals, y_decimals, fee):
    response = client.account_resource(account, resource_name)
    timestamp = response['data']['block_timestamp_last']
    x_reserve = from_octa(response['data']['reserve_x'], x_decimals)
    y_reserve = from_octa(response['data']['reserve_y'], y_decimals)
    rate = y_reserve*fee/x_reserve
    return rate, timestamp


def get_rate_pancake(client, account, resource_name, x_decimals, y_decimals, fee):
    response = client.account_resource(account, resource_name)
    timestamp = response['data']['timestamp']
    x_reserve = from_octa(response['data']['x_reserve']['value'], x_decimals)
    y_reserve = from_octa(response['data']['y_reserve']['value'], y_decimals)
    rate = y_reserve*fee/x_reserve
    return rate, timestamp


private_key = ed25519.PrivateKey.from_hex(PRIVATE_KEY)
my_account = Account(
    account_address=AccountAddress.from_key(private_key.public_key()),
    private_key=private_key,
)
client = wrappedRestClient(NODE_URL)
pancake_account = AccountAddress.from_hex(PANCAKE_ADDRESS)
aux_account = AccountAddress.from_hex(AUX_ADDRESS)

pancake_rate, pre_timestamp_pancake = get_rate_aux(
    client,
    pancake_account,
    PANCAKE_RESOURCE_NAME,
    x_decimals=8,
    y_decimals=6,
    fee=0.9975
)

aux_rate, pre_timestamp_aux = get_rate_pancake(
    client,
    aux_account,
    AUX_RESOURCE_NAME,
    x_decimals=8,
    y_decimals=6,
    fee=0.9990
)
print(f'(DIFF) {abs(pancake_rate-aux_rate):.04f} (AUX) APT: {pancake_rate:.04f} USDC (PANCAKE) APT {aux_rate:.04f} USDC')
while True:
    time.sleep(1)
    pancake_rate, timestamp_pancake = get_rate_aux(
        client,
        pancake_account,
        PANCAKE_RESOURCE_NAME,
        x_decimals=8,
        y_decimals=6,
        fee=0.9975
    )

    aux_rate, timestamp_aux = get_rate_pancake(
        client,
        aux_account,
        AUX_RESOURCE_NAME,
        x_decimals=8,
        y_decimals=6,
        fee=0.9990
    )
    if ((pre_timestamp_pancake != timestamp_pancake) or (pre_timestamp_aux != timestamp_aux)):
        print(f'(DIFF) {abs(pancake_rate-aux_rate):.04f} (AUX) APT: {pancake_rate:.04f} USDC (PANCAKE) APT {aux_rate:.04f} USDC')
        pre_timestamp_pancake = timestamp_pancake
        pre_timestamp_aux = timestamp_aux
