# AUXとPANCAKEでAPT/USDCの裁定機会があるかどうかをチェックする。(USDCはそれぞれwarmholeとlayerzeroで違うので注意)
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


def get_amount(in_reserve, out_reserve, in_amount, fee):
    return out_reserve * (1-fee) * in_amount / (in_reserve + (1-fee) * in_amount)


def get_rate(in_reserve_x, out_reserve_x, in_reserve_y, out_reserve_y, in_amount, fee_x, fee_y):
    forward_swap = get_amount(in_reserve_x, out_reserve_x, in_amount, fee_x)
    backward_swap = get_amount(in_reserve_y, out_reserve_y, forward_swap, fee_y)
    return backward_swap


# トレード量
INIT_AMOUNT = 10_000_000_000

# aux
aux_df = pd.read_csv('aux/rate_history.csv')
aux_version = aux_df['version'].values
aux_rate = aux_df['rate'].values

# pancake
pancake_df = pd.read_csv('pancake/rate_history.csv')
pancake_version = pancake_df['version'].values
pancake_rate = pancake_df['rate'].values

# auxとpancakeのrate差分
df = pd.merge(aux_df, pancake_df, on='version', how='outer')
df = df.sort_values('version').reset_index(drop=True).interpolate('ffill')
diff_version = df['version'].values
return_amount_1 = get_rate(
    df['usdc_reserve_x'],
    df['apt_reserve_x'],
    df['apt_reserve_y'],
    df['usdc_reserve_y'],
    INIT_AMOUNT,
    0.0010,
    0.0025
    )
return_amount_2 = get_rate(
    df['usdc_reserve_y'],
    df['apt_reserve_y'],
    df['apt_reserve_x'],
    df['usdc_reserve_x'],
    INIT_AMOUNT,
    0.0025,
    0.0010)

diff_rate_1 = ((return_amount_1 - INIT_AMOUNT) / (10 ** 6)).values
diff_rate_2 = ((return_amount_2 - INIT_AMOUNT) / (10 ** 6)).values

# plot
fig, ax1 = plt.subplots(figsize=(18, 9))
ax1.plot(aux_version, aux_rate, label='aux')
ax1.plot(pancake_version, pancake_rate, label='pancake')
ax1.set_ylabel('apt/usdc rate')

ax2 = ax1.twinx()
ax2.hlines(y=0, xmin=df['version'].values[0], xmax=df['version'].values[-1], colors='r', alpha=0.3)
ax2.plot(diff_version, diff_rate_1, 'm--', alpha=0.5, label='aux->pancake')
ax2.plot(diff_version, diff_rate_2, 'c--', alpha=0.5, label='pancake->aux')
ax2.set_ylabel('profit(USDC)')

ax1.set_xlabel('version')

h1, l1 = ax1.get_legend_handles_labels()
h2, l2 = ax2.get_legend_handles_labels()
ax1.legend(h1+h2, l1+l2, loc='upper right')
plt.title(f'Trade Amount {int(INIT_AMOUNT/(10**6))}USDC')
plt.savefig('arbitrage/rate_diff_between_aux_and_pancake.png')
