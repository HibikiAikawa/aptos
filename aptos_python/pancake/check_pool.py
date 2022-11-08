# get_pool_info.pyで取得したプール情報を元にデータを可視化
import csv
import pandas as pd


df = pd.read_csv('pancake/pancakeswap_pool.csv', header=0)


for _, (pool_name, x, y) in df.iterrows():
    start_index = pool_name.find('<')
    pools = pool_name[start_index + 1:-1].split(', ')
    if ('0x1::aptos_coin::AptosCoin' in pools):
        idx = pools.index('0x1::aptos_coin::AptosCoin')
        if idx == 0:
            print(f'{x:15d}, {pools[1]}')
        else:
            print(f'{y:15d}, {pools[0]}')

    else:
        x_name = pools[0].split('::')[2]
        y_name = pools[1].split('::')[2]
        print(f'{x_name:10s} {x:15d}  {y_name:10s} {y:15d}')
