import time

import requests


aux_address = "0xbd35135844473187163ca197ca93b2ab014370587bb0ed3befff9e902d6bb541"
usdc_module = "0x5e156f1207d0ebfa19a9eeff00d62a282278fb8719f4fab3a586a0a2c0fffbea::coin::T"
apt_module = "0x1::aptos_coin::AptosCoin"
event_handle = f'{aux_address}::amm::Pool<{apt_module},{usdc_module}>'
field_name = 'swap_events'

# https://fullnode.devnet.aptoslabs.com/v1/accounts/{address}/events/{event_handle}/{field_name}
rest_api_url = f'https://fullnode.mainnet.aptoslabs.com/v1/accounts/{aux_address}/events/{event_handle}/{field_name}'


def from_octa(amount, decimals):
    if isinstance(amount, str):
        amount = int(amount)
    amount /= 10**(decimals)
    return amount


response = requests.get(rest_api_url).json()
sequence_number_pre = response[-1]['sequence_number']

while True:
    response = requests.get(rest_api_url).json()
    sequence_number = response[-1]['sequence_number']
    if (int(sequence_number) > int(sequence_number_pre)):
        num = int(sequence_number) - int(sequence_number_pre)

        for i in range(-1 * num, 0, 1):
            sender_addr = response[i]['data']['sender_addr']
            sequence_number = response[i]['sequence_number']
            if response[i]['data']['in_coin_type'] == apt_module:
                in_au = from_octa(response[i]['data']['in_au'], 8)
                out_au = from_octa(response[i]['data']['out_au'], 6)
                print(f' APT: {in_au:8.2f} -> USDC: {out_au:8.2f} sender_addr: {sender_addr}')
            else:
                in_au = from_octa(response[i]['data']['in_au'], 6)
                out_au = from_octa(response[i]['data']['out_au'], 8)
                print(f'USDC: {in_au:8.2f} ->  APT: {out_au:8.2f} sender_addr: {sender_addr}')

        sequence_number_pre = response[-1]['sequence_number']

    time.sleep(5)
