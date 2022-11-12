# AUXとPANCAKEでAPT/USDCの裁定機会があるかどうかをチェックする。(USDCはそれぞれwarmholeとlayerzeroで違うので注意)
import pandas as pd
import numpy as np
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

idx = np.where(diff_rate_1 > 0)[0]

pre_i = idx[0]
start_idx = [pre_i]
end_idx = []
for i in idx[1:]:
    if (i - pre_i > 1):
        start_idx.append(i)
        end_idx.append(pre_i+1)
    pre_i = i
print(diff_version[end_idx] - diff_version[start_idx[:-1]])
print(diff_version[start_idx[:-1]])
