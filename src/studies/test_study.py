'''
Author: Oliver van Til
Date: Monday, 06th January 2023
Desc: Study used for developing the backtesting framework.
'''

import sys

import pandas as pd
import numpy as np

sys.path.append('src/')

from modules.simulator.market import Market
from modules.simulator.trader import Trader

from algorithm.algorithm import AlgoEngine

algo_engine = AlgoEngine()

# unpickle the data
df_spot = pd.read_pickle('data/okx/LTC-USDT_30m_01-01-2022_None.pkl')
df_swap = pd.read_pickle('data/okx/LTC-USDT-SWAP_30m_01-01-2022_None')
# convert the timestamp to datetime
df_spot.timestamp = pd.to_datetime(df_spot.timestamp, unit='ms')
df_swap.timestamp = pd.to_datetime(df_swap.timestamp, unit='ms')

print(df_spot)

# reset index
df_spot.reset_index(inplace=True)
df_swap.reset_index(inplace=True)

df_algo = algo_engine.process(df_spot)
# df_alg = (df_algo.loc[df_algo['entry'] == True])

# for index, row in enumerate(df_alg.itertuples()):
#     print(row.Index)

trader = Trader(df_spot, df_swap, df_algo)
trader.simulate()
