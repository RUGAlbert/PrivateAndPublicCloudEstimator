
from random import randint
from os import path

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


def calculateNetwork(serverInfo : dict) -> DataFrame:    
    networkUsageDf = pd.read_csv(path.join(Config.DATAPATH, serverInfo['networkUsageFile']), sep=',', skiprows=1)
    networkUsageDf['time'] = pd.to_datetime(networkUsageDf['time'], unit='s')
    # networkUsageDf = networkUsageDf[(networkUsageDf['time'] >= '2023-03-27') & (networkUsageDf['time'] <= '2023-04-04')]
    networkUsageDf = networkUsageDf.resample('60min', on='time').mean().interpolate('time')
    networkUsageDf['bytesMoved'] = (networkUsageDf['in'] + networkUsageDf['out']) * 60 * 60
    networkUsageDf = networkUsageDf[['bytesMoved']]
    return networkUsageDf

def calculate(rawDataDf : DataFrame, serverInfo : dict) -> DataFrame:

    result = wattToEServer(rawDataDf)
    result['eServerStatic'] = 0.8 * result['eServer']
    result['eServerDynamic'] = 0.2 * result['eServer']

    networkUsageDf = calculateNetwork(serverInfo)
    result = result.join(networkUsageDf)
    result['eNetwork'] = result['bytesMoved'] * Config.WHPERBYTE
    result['eNetworkStatic'] = Config.MU * result['eNetwork']
    result['eNetworkDynamic'] = (1 - Config.MU) * result['eNetwork']

    result['eCooling'] = (serverInfo['PUE'] - 1) * (result['eServer'] + result['eNetwork'])
    result['nu'] = (result['eServerStatic'] + result['eNetworkStatic']) / (result['eServer'] + result['eNetwork'])
    result['eCoolingStatic'] = result['nu'] * result['eCooling']
    result['eCoolingDynamic'] = (1 - result['nu']) * result['eCooling']

    result['scope2E'] = result['eServer'] + result['eNetwork'] + result['eCooling']
    result['scope2ELower'] = Config.GAMMA_LOWER * (result['eServerStatic'] + result['eNetworkStatic'] + result['eCoolingStatic']) + Config.ZETA_LOWER * (result['eServerDynamic'] + result['eNetworkDynamic'] + result['eCoolingDynamic'])
    result['scope2EUpper'] = Config.GAMA_UPPER * (result['eServerStatic'] + result['eNetworkStatic'] + result['eCoolingStatic']) + Config.ZETA_UPPER * (result['eServerDynamic'] + result['eNetworkDynamic'] + result['eCoolingDynamic'])

    return result
