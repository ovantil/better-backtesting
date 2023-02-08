import os
import sys
import ccxt
import numpy as np
import pandas as pd

from datetime import datetime

config = {
    'apiKey': "601b10a0-e21c-4bcc-ad4f-3babdc7fb9b8",
    'secret': "2691880D4AB6F2C17F11243DCB941D6F",
    'password': 'A5*q6pzEb)ezh)t',
}


class OkxDataFetch:
    '''
    ~~ some info about OKx market data API ~~
    perpeptual swap markets are (base)-(settle_ccy)-SWAP,
    and spot markets are (base)-(settle_ccy)-SPOT
    '''

    timeframe_minutes = {
        '1m': 1,
        '3m': 3,
        '5m': 5,
        '15m': 15,
        '30m': 30,
        '1h': 60,
        '2h': 120,
        '4h': 240,
        '6h': 360,
        '8h': 480,
        '12h': 720,
        '1d': 1440
    }

    def __init__(self, cache: bool = False) -> None:
        self.exchange = ccxt.okex(config)

    def get_ohlcv(self,
                  market: str,
                  timeframe: str,
                  type: str,
                  since: str,
                  until=None,
                  cache=False):

        # the market code does not need 'spot', only 'swap'
        type = '' if type == 'spot' else '-' + type
        market_id = f'{market.upper()}-USDT{type.upper()}'
        write_name = f'{market_id}_{timeframe}_{since}_{until}'

        # check if the file is already cached, and return it if it is
        if cache:
            if os.path.isfile(f'./data/okx/{write_name}.pkl'):
                print(f'loading {write_name} from cache')
                return pd.read_pickle(f'./data/okx/{write_name}.pkl')

        # convert since from dd-mm-yyyy to unix timestamp
        since = int(datetime.strptime(since, '%d-%m-%Y').timestamp()) * 1000
        until = int(
            datetime.now().timestamp()) * 1000 if until is None else int(
                datetime.strptime(until, '%d-%m-%Y').timestamp())

        print(f'fetching market data, ' \
            f'configuration is {market_id}_{timeframe}_{since}_{until}')

        # pre-calculate number of candles
        req_mins = (until - since) / 1000 / 60
        num_candles = int(req_mins / self.timeframe_minutes[timeframe])
        num_requests = np.ceil(num_candles / 100)

        # iterate over requests until we have enough candles
        datasets = []
        for req in range(int(num_requests)):
            since = since if req == 0 else datasets[-1][-1][0]

            response = self.exchange.fetch_ohlcv(
                symbol=market_id,
                timeframe=timeframe,
                since=since if req == 0 else datasets[-1][-1][0],
                limit=100)

            datasets.append(response)

            req_pct = (req + 1) / num_requests
            sys.stdout.write(f'\r{req_pct:.2%}')
            sys.stdout.flush()
            sys.stdout.write('\b')

        sys.stdout.write(f'\rdownload complete.' + ' ' * 12 + '\n')

        # convert to dataframe
        df = pd.DataFrame(
            [item for sublist in datasets for item in sublist],
            columns=['timestamp', 'open', 'high', 'low', 'close', 'vol'])

        # dedupe rows by timestamp, keep the original timestamp
        df = df.drop_duplicates(subset=['timestamp'], keep='first')

        # pickles are smaller than csvs
        if cache:
            pd.to_pickle(df, f'./data/okx/{write_name}.pkl', protocol=4)
            print(f'wrote {write_name} to cache')

        return df


if __name__ == '__main__':
    okx = OkxDataFetch()
    df_swap = okx.get_ohlcv('BTC', '4h', 'spot', '01-01-2021', cache=True)
    # df_spot = okx.get_ohlcv('BTC', '1d', 'spot', '01-01-2020', cache=True)