import os
import sys
import talib as ta
import numpy as np
import pandas as pd
import time
import matplotlib.pyplot as plt

from dataclasses import dataclass

sys.path.append('src/')

from modules.other.logger import TraderLogger


@dataclass
class Trade:
    entry_price: float
    tp_price: float
    sl_price: float
    entry_timestamp: str

    exit_timestamp: str
    exit_price: float
    win: bool


class Trader:

    def __init__(self,
                 market_spot_df,
                 market_swap_df,
                 algorithm_df,
                 max_leverage=5,
                 capital=1000) -> None:

        self.spot_df = market_spot_df
        self.swap_df = market_swap_df
        self.algo_df = algorithm_df
        self.max_leverage = max_leverage
        self.capital = capital
        self.trades = []

        self.tl = TraderLogger()

        # ATR TPSL variables
        atr_timeperiod = 100
        atr_sl_multiplier = 1.4
        atr_tp_multiplier = 3

        # configure SL/TP data
        self.spot_df['atr_tpsl'] = ta.ATR(self.spot_df['high'],
                                          self.spot_df['low'],
                                          self.spot_df['close'],
                                          timeperiod=atr_timeperiod)

        # prevent forward looking of ATR
        self.spot_df['atr_tpsl'] = self.spot_df['atr_tpsl'].shift(1)
        self.spot_df['stoploss'] = self.spot_df['open'] - \
            (self.spot_df['atr_tpsl'] * atr_sl_multiplier)
        self.spot_df['takeprofit'] = self.spot_df['open'] + \
            (self.spot_df['atr_tpsl'] * atr_tp_multiplier)

    def simulate(self):
        entry_points = self.algo_df[self.algo_df['entry'] == True]

        for index, row in enumerate(entry_points.itertuples()):

            if index < 50:
                continue

            swap_row = self.swap_df.iloc[row.Index]
            # find the row where timestamps match

            spot_row = self.spot_df.iloc[row.Index]

            entry_price = swap_row['open']
            stoploss = spot_row['stoploss']
            takeprofit = spot_row['takeprofit']

            stoploss_pct = (stoploss - entry_price) / entry_price
            takeprofit_pct = (takeprofit - entry_price) / entry_price

            # self.tl.log(f'entry price: {entry_price:.2f}')
            # self.tl.log(f'stoploss: {stoploss:.2f}')
            # self.tl.log(f'takeprofit: {takeprofit:.2f}')
            # self.tl.log(f'stoploss_pct: {stoploss_pct*100:.2f}%')
            # self.tl.log(f'takeprofit_pct: {takeprofit_pct*100:.2f}%\n')

            trade = Trade(entry_price=entry_price,
                          tp_price=takeprofit,
                          sl_price=stoploss,
                          entry_timestamp=swap_row['timestamp'],
                          exit_timestamp=None,
                          exit_price=None,
                          win=None)

            # print('trade entered on timestamp: ', trade.entry_timestamp)

            for index_fwd, row_fwd in enumerate(
                    self.spot_df.iloc[row.Index + 1:].itertuples()):

                open = row_fwd.open
                high = row_fwd.high
                low = row_fwd.low
                pnl = entry_price - open

                if low < stoploss:
                    trade.exit_timestamp = row_fwd.timestamp
                    trade.exit_price = stoploss
                    trade.win = False
                    # print('loss')
                    break

                if high > takeprofit:
                    trade.exit_timestamp = row_fwd.timestamp
                    trade.exit_price = takeprofit
                    trade.win = True
                    # print('win')
                    break

            self.trades.append(trade)
            # print(trade.win, trade.entry_timestamp, trade.exit_timestamp)

        wins = [trade.win for trade in self.trades if trade.win != False]
        losses = [trade.win for trade in self.trades if trade.win == False]

        print(f'wins: {len(wins)}')
        print(f'losses: {len(losses)}')

        pnl = 0
        pos_size = 2500
        fees = 0
        drawdown = 0
        pnl_rolling = []
        open_rolling = []

        for trade in self.trades[:-5]:
            pct_change = (trade.exit_price -
                          trade.entry_price) / trade.entry_price

            pnl += pos_size * pct_change
            # fee is 0.04% per side
            fee = 0.0008 * pos_size

            fees += fee
            pnl -= fee

            if pnl < drawdown:
                drawdown = pnl

            print(f'{pnl:.2f} {trade.entry_timestamp}')
            pnl_rolling.append(pnl)
            open_rolling.append(trade.entry_price)

        print()
        print(f'fees: {fees:.2f}')
        print(f'pnl: {pnl:.2f}')
        print(f'pnl (fee adjusted): {pnl-fees:.2f}')
        print('drawdown: ', drawdown)

        # convert pnl_rolling to a pct based on the first val
        # pnl_rolling = [((pnl - pnl_rolling[0]) / pnl_rolling[0]) * 100
        #                for pnl in pnl_rolling]
        
        # open_rolling = [((pnl - open_rolling[0]) / open_rolling[0]) * 100
        #                   for pnl in open_rolling]

        plt.plot(pnl_rolling)
        plt.plot(open_rolling)
        # print(open_rolling)
        
        

        print('buy and gold gain: ',
              (open_rolling[-1] - open_rolling[0]) / open_rolling[0] * 100)

        plt.show()