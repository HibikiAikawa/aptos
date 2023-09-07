import requests
from aptos_sdk.account_address import AccountAddress

PANCAKE_ADDRESS = '0xc7efb4076dbe143cbcd98cfaaa929ecfc8f299203dfff63b95ccb6bfe19850fa'
APT_COIN = '0x1::aptos_coin::AptosCoin'
USDC_COIN = '0xf22bede237a07e121b56d91a491eb7bcdfd1f5907926a9e58338f964a01b17fa::asset::USDC'
RESOURCE_NAME = f'{PANCAKE_ADDRESS}::swap::TokenPairReserve<{APT_COIN}, {USDC_COIN}>'
EVENT_NAME = f'{PANCAKE_ADDRESS}::swap::PairEventHolder<{APT_COIN}, {USDC_COIN}>'

pancake_account = AccountAddress.from_hex(PANCAKE_ADDRESS)
pancake_account = str(pancake_account)

url = f"https://fullnode.mainnet.aptoslabs.com/v1/accounts/{PANCAKE_ADDRESS}/events/{EVENT_NAME}/swap"
# headers = {"Accept": "application/json, application/x-bcs"}

# response = requests.get(url, headers=headers)

# print(response.json())


# import http.client

# conn = http.client.HTTPSConnection("fullnode.mainnet.aptoslabs.com")

# headers = { 'Accept': "application/json, application/x-bcs" }

# conn.request("GET", f"/v1/accounts/{pancake_account}/events/{EVENT_NAME}/swap", headers=headers)

# res = conn.getresponse()
# data = res.read()

# print(data.decode("utf-8"))





import importlib.metadata as metadata
import httpx
import asyncio

# constants
PACKAGE_NAME = "aptos-sdk"


class Metadata:
    APTOS_HEADER = "x-aptos-client"

    @staticmethod
    def get_aptos_header_val():
        version = metadata.version(PACKAGE_NAME)
        return f"aptos-python-sdk/{version}"

print(Metadata.get_aptos_header_val())

client = httpx.AsyncClient(
    http2=False,
    limits=httpx.Limits(),
    timeout=httpx.Timeout(60.0, pool=None),
    headers={Metadata.APTOS_HEADER: Metadata.get_aptos_header_val()}
)

#client.get(os.path.join(self.base_url, 'accounts', str(address), 'events', event_handle, field_name))
async def main():
    ret = await client.get(url, params={'start':866360, 'limit':5})
    for l in ret.json():
        print(l['sequence_number'])

asyncio.run(main())