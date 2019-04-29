""" Ichimoku Indicator
"""

import math

import numpy
import pandas
from talib import abstract

from analyzers.utils import IndicatorUtils


class Ichimoku(IndicatorUtils):
    def analyze(self, historical_data, signal=['leading_span_a', 'leading_span_b'], hot_thresh=None, cold_thresh=None, chart=None):
        """Performs an ichimoku cloud analysis on the historical data

        Args:
            historical_data (list): A matrix of historical OHCLV data.
            signal (list, optional): Defaults to leading_span_a and leading_span_b. The indicator
                line to check hot/cold against.
            hot_thresh (float, optional): Defaults to None. The threshold at which this might be
                good to purchase.
            cold_thresh (float, optional): Defaults to None. The threshold at which this might be
                good to sell.

        Returns:
            pandas.DataFrame: A dataframe containing the indicators and hot/cold values.
        """

        dataframe = self.convert_to_dataframe(historical_data)

        ichimoku_columns = {
            'tenkansen': [numpy.nan] * dataframe.index.shape[0],
            'kijunsen': [numpy.nan] * dataframe.index.shape[0],
            'leading_span_a': [numpy.nan] * dataframe.index.shape[0],
            'leading_span_b': [numpy.nan] * dataframe.index.shape[0]
        }

        ichimoku_values = pandas.DataFrame(ichimoku_columns,
                                           index=dataframe.index
                                           )
        # value calculations
        low_9 = dataframe['low'].rolling(window=9).min()
        low_26 = dataframe['low'].rolling(window=26).min()
        low_52 = dataframe['low'].rolling(window=52).min()
        high_9 = dataframe['high'].rolling(window=9).max()
        high_26 = dataframe['high'].rolling(window=26).max()
        high_52 = dataframe['high'].rolling(window=52).max()

        ichimoku_values['tenkansen'] = (low_9 + high_9) / 2
        ichimoku_values['kijunsen'] = (low_26 + high_26) / 2
        ichimoku_values['leading_span_a'] = ((ichimoku_values['tenkansen'] + ichimoku_values['kijunsen']) / 2)
        ichimoku_values['leading_span_b'] = (high_52 + low_52) / 2

        # add time period for cloud offset
        ## if cloud discplacement changed the ichimuko plot will be off ##
        cloud_displacement = 26
        last_time = dataframe.index[-1]
        timedelta = dataframe.index[1] - dataframe.index[0]
        newindex = pandas.DatetimeIndex(start=last_time + timedelta,
                                        freq=timedelta,
                                        periods=cloud_displacement)
        ichimoku_values = ichimoku_values.append(pandas.DataFrame(index=newindex))
        # cloud offset
        ichimoku_values['leading_span_a'] = ichimoku_values['leading_span_a'].shift(cloud_displacement)
        ichimoku_values['leading_span_b'] = ichimoku_values['leading_span_b'].shift(cloud_displacement)

        ichimoku_values['is_hot'] = False
        ichimoku_values['is_cold'] = False

        try:
            for index in range(0, ichimoku_values.index.shape[0]):
                date = ichimoku_values.index[index]

                if date <= dataframe.index[-1]:
                    span_hot = ichimoku_values['leading_span_a'][date] > ichimoku_values['leading_span_b'][date]
                    close_hot = dataframe['close'][date] > ichimoku_values['leading_span_a'][date]
                    if hot_thresh:
                        ichimoku_values.at[date, 'is_hot'] = span_hot and close_hot
                    span_cold = ichimoku_values['leading_span_a'][date] < ichimoku_values['leading_span_b'][date]
                    close_cold = dataframe['close'][date] < ichimoku_values['leading_span_a'][date]
                    if cold_thresh:
                        ichimoku_values.at[date, 'is_cold'] = span_cold and close_cold
                else:
                    pass

        except KeyError as e:
            print('keyerror: {}'.format(e))

        if chart == None:
            ichimoku_values.dropna(how='any', inplace=True)

        return ichimoku_values