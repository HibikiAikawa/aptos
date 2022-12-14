import os

import yaml

from aptos_sdk.account import Account
from aptos_sdk.account_address import AccountAddress
from aptos_sdk.client import RestClient
from aptos_sdk import ed25519
from aptos_sdk.transactions import (
    EntryFunction,
    TransactionArgument,
    TransactionPayload,
)

from aptos_sdk.bcs import Serializer
from aptos_sdk.type_tag import StructTag, TypeTag


with open('../.aptos/config.yaml', 'r') as f:
    config = yaml.safe_load(f)

PRIVATE_KEY = config['profiles']['devnet']['private_key']
NODE_URL = os.path.join(config['profiles']['devnet']['rest_url'], 'v1')
AUX_ADDRESS = '0xea383dc2819210e6e427e66b2b6aa064435bf672dc4bdc55018049f0c361d01a'

APT_COIN = '0x1::aptos_coin::AptosCoin'
BTC_COIN = f'{AUX_ADDRESS}::fake_coin::BTC'
USDC_COIN = f'{AUX_ADDRESS}::fake_coin::USDC'
APT_RESOURCE_NAME = f'0x1::coin::CoinStore<{APT_COIN}>'
USDC_RESOURCE_NAME = f'0x1::coin::CoinStore<{AUX_ADDRESS}::fake_coin::FakeCoin<{USDC_COIN}>>'
BTC_RESOURCE_NAME = f'0x1::coin::CoinStore<{AUX_ADDRESS}::fake_coin::FakeCoin<{BTC_COIN}>>'

private_key = ed25519.PrivateKey.from_hex(PRIVATE_KEY)
my_account = Account(
    account_address=AccountAddress.from_key(private_key.public_key()),
    private_key=private_key,
)
client = RestClient(NODE_URL)

aux_account = AccountAddress.from_hex(AUX_ADDRESS)


print('='*10, 'before swap', '='*10)
usdc_value = client.account_resource(my_account.address(), USDC_RESOURCE_NAME)['data']['coin']['value']
apt_value = client.account_resource(my_account.address(), APT_RESOURCE_NAME)['data']['coin']['value']
print(f'usdc value: {usdc_value}')
print(f'apt  value: {apt_value}')

print('swap')
in_type_tag = StructTag.from_str(f'{AUX_ADDRESS}::fake_coin::FakeCoin')
in_type_tag_child = StructTag.from_str(USDC_COIN)
in_type_tag.type_args = [TypeTag(in_type_tag_child)]

out_type_tag = StructTag.from_str(APT_COIN)

payload = EntryFunction.natural(
    f"{AUX_ADDRESS}::amm",
    "swap_exact_coin_for_coin_with_signer",
    [TypeTag(in_type_tag), TypeTag(out_type_tag)],
    [TransactionArgument(1_000, Serializer.u64), TransactionArgument(0, Serializer.u64)],
)
signed_transaction = client.create_single_signer_bcs_transaction(
    my_account, TransactionPayload(payload)
)
txn_hash = client.submit_bcs_transaction(signed_transaction)
client.wait_for_transaction(txn_hash)
print('done')

print('='*10, 'after swap', '='*10)
usdc_value = client.account_resource(my_account.address(), USDC_RESOURCE_NAME)['data']['coin']['value']
apt_value = client.account_resource(my_account.address(), APT_RESOURCE_NAME)['data']['coin']['value']
print(f'usdc value: {usdc_value}')
print(f'apt  value: {apt_value}')
