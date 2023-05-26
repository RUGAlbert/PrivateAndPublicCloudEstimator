
from random import randint
import logging
from os import path
import sys
import numpy as np

import numpy as np
import pandas as pd
from ..config import Config
from pandas import DataFrame


def wattToEServer(rawServerDf : DataFrame) -> DataFrame:
    """Translates the watt usage per minute to wh

    Args:
        rawServerDf (DataFrame): the raw watt data per minute

    Returns:
        DataFrame: returns a dataframe with hourly wh data
    """    
    prunnedRawServerDf = rawServerDf[['time','Platform-Curr', 'CPU-Curr', 'Mem-Curr']].copy()

    #conversion from watts to kwh
    prunnedRawServerDf.loc[:, 'Duration'] = -pd.to_datetime(prunnedRawServerDf['time'], errors='coerce').diff(-1).dt.total_seconds()
    prunnedRawServerDf.drop(prunnedRawServerDf.tail(1).index,inplace=True)
    prunnedRawServerDf.loc[:, 'DurationInHours'] = prunnedRawServerDf['Duration'] / 3600
    prunnedRawServerDf.loc[:, 'eServer'] = prunnedRawServerDf['DurationInHours'] * prunnedRawServerDf['Platform-Curr']

    #group by hour
    serverDataDf = prunnedRawServerDf[['time', 'eServer']].copy()
    serverDataDf.loc[:, "time"] = pd.to_datetime(serverDataDf["time"])
    serverDataDf = serverDataDf.resample('60min', on='time').sum()
    return serverDataDf


def calculateNetwork(serverInfo : dict) -> DataFrame:
    """Calculates the amount of network usage in bytes

    Args:
        serverInfo (dict): The dictonary with all the serverinfo

    Returns:
        DataFrame: returns hourly data of network usage in bytes
    """    
    networkUsageDf = pd.read_csv(path.join(Config.DATAPATH, serverInfo['networkUsageFile']), sep=',', skiprows=1)
    networkUsageDf['time'] = pd.to_datetime(networkUsageDf['time'], unit='s')
    # networkUsageDf = networkUsageDf[(networkUsageDf['time'] >= '2023-03-27') & (networkUsageDf['time'] <= '2023-04-04')]
    networkUsageDf = networkUsageDf.resample('60min', on='time').mean().interpolate('time')
    #divided by two since there are two servers
    networkUsageDf['bytesMoved'] = (networkUsageDf['in'] + networkUsageDf['out']) * 60 * 60 / 2
    networkUsageDf = networkUsageDf[['bytesMoved']]
    networkUsageDf = networkUsageDf[networkUsageDf['bytesMoved'] > 1000]
    return networkUsageDf

def calculateEnergyConsumption(serverInfo : dict) -> DataFrame:
    """Calculates the energy consumption used by the server and other sources

    Args:
        serverInfo (dict): The dictonary with all the serverinfo

    Returns:
        DataFrame: a dataframe with the hourly energy consumption
    """
    # result = wattToEServer(rawDataDf)
    result = pd.read_csv(path.join(Config.DATAPATH, serverInfo['powerServerFile']), sep=',', skiprows=1)
    result.loc[:, "time"] = pd.to_datetime(result["time"], format="%d/%m/%Y %H:%M")
    result = result.set_index('time')
    result.sort_index(inplace=True)
    result['eServer'] = result['watts']
    result['eServerStatic'] = serverInfo['energyServerStatic']
    result['eServerDynamic'] = result['eServer'] - serverInfo['energyServerStatic']

    networkUsageDf = calculateNetwork(serverInfo)
    result = result.join(networkUsageDf)


    result['bytesMoved'] = result['bytesMoved'].fillna(0)
    result['eNetwork'] = result['bytesMoved'] * Config.WHPERBYTE
    result['mu'] = 1 - (1 - Config.MU) * (result['eNetwork'] - 10 ) / (250)
    peaks = result[result['eNetwork'] > 0].resample('D')['eNetwork'].max()
    avgMax = np.mean(peaks)
    # result['mu'] = result['mu'].rolling(window=30).mean().shift(1)
    # result['eNetworkStatic'] = result['mu'] * result['eNetwork']
    result['eNetworkStatic'] = avgMax * Config.MU
    result['eNetworkDynamic'] = (1 - result['mu']) * result['eNetwork']
    result['eNetworkCalculatedWithConstant'] = result['eNetwork']
    result['eNetworkWithNewAlgorithm'] =  result['eNetworkStatic'] + result['eNetworkDynamic']

    result['eCooling'] = (serverInfo['PUE'] - 1) * (result['eServer'] + result['eNetwork'])
    result['nu'] = (result['eServerStatic'] + result['eNetworkStatic']) / (result['eServer'] + result['eNetworkWithNewAlgorithm'])
    result['eCoolingStatic'] = result['nu'] * result['eCooling']
    result['eCoolingDynamic'] = (1 - result['nu']) * result['eCooling']

    result['scope2E'] = result['eServer'] + result['eNetwork'] + result['eCooling']
    result['scope2ELower'] = Config.GAMMA_LOWER * (result['eServerStatic'] + result['eNetworkStatic'] + result['eCoolingStatic']) + Config.ZETA_LOWER * (result['eServerDynamic'] + result['eNetworkDynamic'] + result['eCoolingDynamic'])
    result['scope2EUpper'] = Config.GAMA_UPPER * (result['eServerStatic'] + result['eNetworkStatic'] + result['eCoolingStatic']) + Config.ZETA_UPPER * (result['eServerDynamic'] + result['eNetworkDynamic'] + result['eCoolingDynamic'])

    return result

def calculate(serverInfo : dict) -> DataFrame:
    """Calculates the scope 2 emissions

    Args:
        serverInfo (dict): The dictonary with all the serverinfo

    Returns:
        DataFrame: returns the hourly scope 2 emissions data
    """    
    result = calculateEnergyConsumption(serverInfo)

    carbonIntensityDf =  pd.read_csv(path.join(Config.DATAPATH, serverInfo['carbonIntensityFile']), sep=',', skiprows=1)
    carbonIntensityDf['time'] = pd.to_datetime(carbonIntensityDf['Datetime (UTC)']).dt.tz_localize(None)
    # print(carbonIntensityDf.columns)
    #divide it by 1000 to translate from kwh to wh
    carbonIntensityDf['ci'] = carbonIntensityDf['London'] / 1000
    # carbonIntensityDf = carbonIntensityDf.set_index('time')
    carbonIntensityDf = carbonIntensityDf.resample('60min', on='time').mean()
    carbonIntensityDf = carbonIntensityDf[['ci']]
    result = result.join(carbonIntensityDf)

    if Config.USEHOURLYCARBON:
        result['scope2Lower'] = result['scope2ELower'] * result['ci']
        result['scope2Upper'] = result['scope2EUpper'] * result['ci']
    else:
        result['scope2Lower'] = result['scope2ELower'] * Config.CARBONINTENSITY
        result['scope2Upper'] = result['scope2EUpper'] * Config.CARBONINTENSITY

    return result