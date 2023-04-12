
from random import randint

import numpy as np
import pandas as pd
from ..config import Config
from pandas import DataFrame


def wattToEServer(rawServerDf : DataFrame) -> DataFrame:
    prunnedRawServerDf = rawServerDf[['Time','Platform-Curr', 'CPU-Curr', 'Mem-Curr']].copy()

    #conversion from watts to kwh
    prunnedRawServerDf.loc[:, 'Duration'] = -pd.to_datetime(prunnedRawServerDf['Time'], errors='coerce').diff(-1).dt.total_seconds()
    prunnedRawServerDf.drop(prunnedRawServerDf.tail(1).index,inplace=True)
    prunnedRawServerDf.loc[:, 'DurationInHours'] = prunnedRawServerDf['Duration'] / 3600
    prunnedRawServerDf.loc[:, 'eServer'] = prunnedRawServerDf['DurationInHours'] * prunnedRawServerDf['Platform-Curr']

    #group by hour
    serverDataDf = prunnedRawServerDf[['Time', 'eServer']].copy()
    serverDataDf.loc[:, "Time"] = pd.to_datetime(serverDataDf["Time"])
    serverDataDf = serverDataDf.resample('60min', on='Time').sum()
    return serverDataDf


def calculate(rawDataDf : DataFrame, serverInfo : dict) -> DataFrame:

    result = wattToEServer(rawDataDf)
    #include real calculation
    result['eNetwork'] = np.random.randint(5000,30000,size=result.shape[0]) * Config.WHPERBYTE
    result['eCooling'] = (serverInfo['PUE'] - 1) * (result['eServer'] + result['eNetwork'])

    result['scope2E'] = result['eServer'] + result['eNetwork'] + result['eCooling']

    return result
