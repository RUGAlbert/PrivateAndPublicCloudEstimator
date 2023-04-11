'''
This is the start place of the calculation
'''

import pandas as pd
from pandas import DataFrame
from os import path

from .calculator import calculate

def rawDataToWattHour(rawServerDf : DataFrame):
    rawServerDf = rawServerDf[['Time','Platform-Curr', 'CPU-Curr', 'Mem-Curr']]

    #conversion from watts to kwh
    rawServerDf['Duration'] = -pd.to_datetime(rawServerDf['Time'], errors='coerce').diff(-1).dt.total_seconds()
    rawServerDf.drop(rawServerDf.tail(1).index,inplace=True)
    rawServerDf['DurationInHours'] = rawServerDf['Duration'] / 3600
    rawServerDf['serverEnergy'] = rawServerDf['DurationInHours'] * rawServerDf['Platform-Curr']

    #group by hour
    serverDataDf = rawServerDf[['Time', 'serverEnergy']]
    serverDataDf["Time"] = pd.to_datetime(serverDataDf["Time"])
    serverDataDf = serverDataDf.resample('60min', on='Time').sum()
    return serverDataDf

# def start(serverDf : DataFrame, networkDf : DataFrame, datacenterDf : DataFrame, cuserDf : DataFrame):
def start(serverDf : DataFrame):
    print(rawDataToWattHour(serverDf))
    # calculate(serverDf, networkDf, datacenterDf, cuserDf)
