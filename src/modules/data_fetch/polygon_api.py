
import sys

sys.path.append('/Users/olivervantil/trading-system/backtester/')

import pandas as pd
from polygon import RESTClient
from src.various import ProgressBar

polygon_client = RESTClient('pImtsbTOelehVbMlVAgAv_QqEVqvBh9E')


class MarketData:

    def check_exists(self, name):
        # check if name.csv exists in data/polygon
        try:
            df = pd.read_csv(f'data/polygon/{name}.csv')
            return df

        except:
            return None

    def save_df(self, name, df):
        df.to_csv(f'data/polygon/{name}.csv', index=False)

    def get_ohlcv_dataframe(self,
                            market_code: str,
                            multiplier: int,
                            timespan: str,
                            from_date: str,
                            to_date: str,
                            save: bool = True):
        """Uses the Polygon.io library to construct a Pandas DataFrame of
        a specified market. Overcomes the data limitations of a single
        request by automatically downloading all datasets required to reach
        the specified timestamp and removes any overlap using the timestamp
        column.

        Args:
            market_code (str): The market code, as per Polygon specification
            multiplier (int): Determines the length of a candle, using timespan
            timespan (str): 1m, 15m, 1h, etc
            from_date (str): The start date of the dataset, as YYYY-mm-dd
            to_date (str): The end date of the dataset, as YYYY-mm-dd

        Returns:
            pd.DataFrame: A DataFrame containing the market data.
        """

        # convert from_date and to_date to strings
        csv_from = str(from_date)
        csv_to = str(to_date)

        csv_market_code = ''.join(filter(str.isalpha, market_code))
        csv_from = ''.join(filter(str.isdigit, from_date))
        csv_to = ''.join(filter(str.isdigit, to_date))

        name = f'{csv_market_code}_{multiplier}_{timespan}_{csv_from}_{csv_to}'

        f = self.check_exists(name)

        if type(f) == pd.DataFrame:
            print('file exists, loading from disk')
            return f

        #construct the initial dataframe
        df = pd.DataFrame(
            polygon_client.get_aggs(market_code,
                                    multiplier,
                                    timespan,
                                    from_date,
                                    to_date,
                                    limit=500000))

        #calculate the number of minutes between the from and to dates
        from_date = pd.to_datetime(from_date)
        to_date = pd.to_datetime(to_date)
        minutes_between = (to_date - from_date).total_seconds() / 60
        minutes_between = int(minutes_between)

        #create progress bar
        progbar = ProgressBar(f'(download) {market_code} OHLCV data', 1)

        #convert the timestamp to a datetime object
        df.timestamp = pd.to_datetime(df.timestamp * 1000000)
        additional_download_counter = 0
        df2_first_timestamp = None

        #calculate the number of minutes between the first and last timestamp of the df
        df_first_timestamp = df.timestamp.iloc[0]
        df_last_timestamp = df.timestamp.iloc[-1]
        df_minutes_between = (df_last_timestamp -
                              df_first_timestamp).total_seconds() / 60
        df_minutes_between = int(df_minutes_between)

        #calculate the percentage of the progress bar to fill based on the number of minutes

        #check that the last timestamp is >= to_date
        while df.timestamp.iloc[-1] <= pd.to_datetime(to_date):

            if additional_download_counter == 0:
                progbar.additional_info = (
                    '[MARKET_DATA] additonal data required to generate '
                    'requested dataframe')

            additional_download_counter += 1

            progbar.additional_info = (f'downloading additional data from'
                                       f' {df.timestamp.iloc[-1]}')

            #get the last timestamp
            last_timestamp = df.timestamp.iloc[-1]

            #get the next batch of data
            df2 = pd.DataFrame(
                polygon_client.get_aggs(market_code,
                                        multiplier,
                                        timespan,
                                        last_timestamp,
                                        to_date,
                                        limit=500000))

            df_first_timestamp = df.timestamp.iloc[0]
            df_last_timestamp = df.timestamp.iloc[-1]
            df_minutes_between = (df_last_timestamp -
                                  df_first_timestamp).total_seconds() / 60
            df_minutes_between = int(df_minutes_between)
            pct = df_minutes_between / minutes_between * 100
            progbar.progress(pct)

            if df2.iloc[0].timestamp == df2_first_timestamp:
                progbar.additional_info = (
                    f'   [->] no new data downloaded, breaking out of loop')
                progbar.exit()

                # convert from_date and to_date to strings

                if save:
                    self.save_df(name, df)

                return df

            else:
                df2_first_timestamp = df2.iloc[0].timestamp

            #convert the timestamp to a datetime object
            df2.timestamp = pd.to_datetime(df2.timestamp * 1000000)
            #concat the dataframes
            df = pd.concat([df, df2])
            #drop duplicates
            df = df.drop_duplicates(subset=['timestamp'])
            #sort by timestamp
            df = df.sort_values(by=['timestamp'])
            #reset the index
            df = df.reset_index(drop=True)

        progbar.exit()
        # remove all non-letter characters from the market code
        market_code = ''.join(filter(str.isalpha, market_code))

        # convert from_date and to_date to strings
        from_date = str(from_date)
        to_date = str(to_date)

        # remove all non-digit characters from the from_date and to_date
        from_date = ''.join(filter(str.isdigit, from_date))
        to_date = ''.join(filter(str.isdigit, to_date))

        csv_name = f'{market_code}_{multiplier}_{timespan}_{from_date}_{to_date}'
        self.save_df(csv_name, df)

        return df


if __name__ == '__main__':
    market_data = MarketData()
    data = market_data.get_ohlcv_dataframe('C:XAUGBP',
                                           4,
                                           'hour',
                                           '2018-09-01',
                                           '2023-10-02',
                                           save=True)
