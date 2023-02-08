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

    entry_atr: float


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
        print()

        # ATR TPSL variables
        atr_timeperiod = 50
        atr_sl_multiplier = 3
        atr_tp_multiplier = 6

        self.spot_df['bullish_candle'] = self.spot_df['open'] < self.spot_df['close']
        self.spot_df['bearish_candle'] = self.spot_df['open'] > self.spot_df['close']
        
        # configure SL/TP data
        self.spot_df['atr_tpsl'] = ta.ATR(self.spot_df['high'],
                                          self.spot_df['low'],
                                          self.spot_df['close'],
                                          timeperiod=atr_timeperiod)
        
        self.spot_df['atr_14'] = ta.ATR(self.spot_df['high'],
                                            self.spot_df['low'],
                                            self.spot_df['close'],
                                            timeperiod=14)

        # prevent forward looking of ATR
        self.spot_df['atr_tpsl'] = self.spot_df['atr_tpsl'].shift(1)
        self.spot_df['atr_14'] = self.spot_df['atr_14'].shift(1)
        
        self.spot_df['stoploss'] = self.spot_df['open'] - \
            (self.spot_df['atr_tpsl'] * atr_sl_multiplier)

        self.spot_df['takeprofit'] = self.spot_df['open'] + \
            (self.spot_df['atr_tpsl'] * atr_tp_multiplier)

    def simulate(self):
        entry_points = self.algo_df[self.algo_df['entry'] == True]

        for index, row in enumerate(entry_points.itertuples()):

            if index < 2:
                continue
            
            # get number of bullish candles in last 15 candles
            bullish_candles = self.spot_df.iloc[row.Index - 8:row.Index]['bullish_candle'].sum()
            if bullish_candles > 4:
                print('bullish candles: ', bullish_candles)
                continue 
                
            swap_row = self.swap_df.iloc[row.Index]
            # find the row where timestamps match

            spot_row = self.spot_df.iloc[row.Index]
            entry_price = swap_row['open']
            stoploss = spot_row['stoploss']
            takeprofit = spot_row['takeprofit']

            stoploss_pct = (stoploss - entry_price) / entry_price
            takeprofit_pct = (takeprofit - entry_price) / entry_price

            trade = Trade(entry_price=entry_price,
                          tp_price=takeprofit,
                          sl_price=stoploss,
                          entry_timestamp=swap_row['timestamp'],
                          exit_timestamp=None,
                          exit_price=None,
                          win=None,
                          entry_atr=spot_row['atr_14'])

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

        wins = 0
        losses = 0
        portfolio_size = 10000
        fee_amount_per_side = 0.0005
        first_price = None

        total_profit = 0
        total_loss = 0

        pnl = 0
        fees = 0

        pct_risk = 0.05
        pnl_list = []
        rolling_pnl_list = []

        buy_hold_pnl = 0
        rolling_buy_hold_pnl_list = []

        for trade in self.trades:
            if trade.exit_timestamp != None:

                if first_price == None:
                    first_price = trade.entry_price

                buy_hold_pnl = ((trade.exit_price - first_price) /
                                first_price) * portfolio_size
                rolling_buy_hold_pnl_list.append(buy_hold_pnl)

                dollar_change = trade.exit_price - trade.entry_price
                pct_change = dollar_change / trade.entry_price

                wins += 1 if trade.win else 0
                losses += 1 if not trade.win else 0

                stoploss_pct = (trade.sl_price -
                                trade.entry_price) / trade.entry_price
                takeprofit_pct = (trade.tp_price -
                                  trade.entry_price) / trade.entry_price

                atr_based_pos_multiplier = (trade.entry_atr/trade.entry_price)*100

                pos_size = (portfolio_size * pct_risk / stoploss_pct) * atr_based_pos_multiplier
                profit = abs(pos_size * pct_change)
                fee = abs(pos_size * (2 * fee_amount_per_side))

                color_green = '\033[92m'
                color_red = '\033[91m'
                color_end = '\033[0m'

                print(f'[{trade.entry_timestamp}]')
                if trade.win:
                    print(
                        f'{color_green}win: ${profit:.2f}{color_end}, fee: ${fee:.2f}'
                    )
                    total_profit += profit

                if not trade.win:
                    profit = -profit
                    print(
                        f'{color_red}loss: ${profit:.2f}{color_end}, fee: ${fee:.2f}'
                    )
                    total_loss += profit

                pnl += profit
                pnl_list.append(pnl)
                rolling_pnl_list.append(pnl)
                fees += fee
                
                print(f'stoploss: %{stoploss_pct:.2f},' +
                      f' ${trade.entry_price - trade.sl_price:.2f}')
                print(f'takeprofit: %{takeprofit_pct:.2f},' +
                      f' ${trade.tp_price - trade.entry_price:.2f}')
                print(f'pos_size: ${abs(pos_size):.2f}')

        summary_header_colour = color_green if pnl > 0 else color_red
        print(f'{summary_header_colour}summary{color_end}')
        print(f'  wins: {wins}')
        print(f'  losses: {losses}')
        print(f'  losses ($): ${total_loss:.2f}')
        print(f'  profits ($): ${total_profit:.2f}')
        print(f'  fees ($): ${fees:.2f}')
        print(f'  net change: ${(total_profit+total_loss)-fees:.2f}')

        # plot the rolling_pnl
        plt.plot(rolling_pnl_list, label='algorithm')
        plt.plot(rolling_buy_hold_pnl_list, label='buy and hold')
        plt.legend()
        plt.show()