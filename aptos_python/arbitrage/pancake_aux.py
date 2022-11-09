# AUXとPANCAKEでAPT/USDCの裁定機会があるかどうかをチェックする。(USDCはそれぞれwarmholeとlayerzeroで違うので注意)
import pandas as pd
import matplotlib.pyplot as plt

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
diff_rate_1 = ((df['apt_reserve_x']/df['usdc_reserve_x']) * (df['usdc_reserve_y']/df['apt_reserve_y']) * (0.9990 * 0.9975) - 1).values
diff_rate_2 = ((df['apt_reserve_y']/df['usdc_reserve_y']) * (df['usdc_reserve_x']/df['apt_reserve_x']) * (0.9990 * 0.9975) - 1).values

# plot
fig, ax1 = plt.subplots(figsize=(18, 9))
ax1.plot(aux_version, aux_rate, label='aux')
ax1.plot(pancake_version, pancake_rate, label='pancake')
ax1.set_ylabel('apt/usdc rate')

ax2 = ax1.twinx()
ax2.hlines(y=0, xmin=df['version'].values[0], xmax=df['version'].values[-1], colors='r', alpha=0.3)
ax2.plot(diff_version, diff_rate_1, 'm--', alpha=0.5, label='aux->pancake')
ax2.plot(diff_version, diff_rate_2, 'c--', alpha=0.5, label='pancake->aux')
ax2.set_ylabel('rate diff(%)')

plt.xlabel('version')

h1, l1 = ax1.get_legend_handles_labels()
h2, l2 = ax2.get_legend_handles_labels()
ax1.legend(h1+h2, l1+l2, loc='upper right')

plt.savefig('arbitrage/rate_diff_between_aux_and_pancake.png')
