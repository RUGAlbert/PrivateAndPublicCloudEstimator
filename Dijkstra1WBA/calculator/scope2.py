
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
    # print(rawServerDf)
    prunnedRawServerDf = rawServerDf[['Time','Platform-Curr', 'CPU-Curr', 'Mem-Curr']].copy()

    # prunnedRawServerDf.sort_index(inplace=True)

    #conversion from watts to kwh
    prunnedRawServerDf.loc[:, 'Duration'] = np.abs(pd.to_datetime(prunnedRawServerDf['Time'], errors='coerce').diff(-1).dt.total_seconds())
    prunnedRawServerDf.drop(prunnedRawServerDf.tail(1).index,inplace=True)
    prunnedRawServerDf.loc[:, 'DurationInHours'] = prunnedRawServerDf['Duration'] / 3600

    prunnedRawServerDf.loc[:, 'watts'] = prunnedRawServerDf['DurationInHours'] * prunnedRawServerDf['Platform-Curr']

    #group by hour
    serverDataDf = prunnedRawServerDf[['Time', 'watts']].copy()
    serverDataDf.loc[:, "time"] = pd.to_datetime(serverDataDf["Time"])
    serverDataDf = serverDataDf.resample('60min', on='time').sum()

    return serverDataDf


def calculateNetwork(filename : str, amountNetworkIsSharedBy : int) -> DataFrame:
    """Calculates the amount of network usage in bytes

    Args:
        serverInfo (dict): The dictonary with all the serverinfo

    Returns:
        DataFrame: returns hourly data of network usage in bytes
    """
    networkUsageDf = pd.read_csv(path.join(Config.DATAPATH, filename), sep=',', skiprows=1)
    networkUsageDf['time'] = pd.to_datetime(networkUsageDf['time'], unit='s')
    # networkUsageDf = networkUsageDf[(networkUsageDf['time'] >= '2023-03-27') & (networkUsageDf['time'] <= '2023-04-04')]
    networkUsageDf = networkUsageDf.resample('60min', on='time').mean().interpolate('time')
    #divided by two since there are two servers
    networkUsageDf['bytesMoved'] = (networkUsageDf['in'] + networkUsageDf['out']) * 60 * 60 / amountNetworkIsSharedBy
    networkUsageDf = networkUsageDf[['bytesMoved']]
    # networkUsageDf = networkUsageDf[networkUsageDf['bytesMoved'] > 1000]
    return networkUsageDf

def calculateNetworkEnergyConsumption(filename : str, amountNetworkIsSharedBy : int, backupNetworkEquipmentPowerUsage : int):
    networkUsageDf = calculateNetwork(filename, amountNetworkIsSharedBy)

    networkUsageDf['bytesMoved'] = networkUsageDf['bytesMoved'].fillna(0)
    networkUsageDf['eNetwork'] = networkUsageDf['bytesMoved'] * Config.WHPERBYTE
    print(networkUsageDf)
    peaks = networkUsageDf[networkUsageDf['eNetwork'] > 0].resample('D')['eNetwork'].max()
    valleys = networkUsageDf[networkUsageDf['eNetwork'] > 0].resample('D')['eNetwork'].min()
    avgMax = np.median(peaks)
    avgMin = np.median(valleys)
    print(avgMin, avgMax)
    networkUsageDf['mu'] = 1 - (1 - Config.MU) * (networkUsageDf['eNetwork'] - avgMin ) / avgMax
    networkUsageDf.loc[networkUsageDf['eNetwork'] < avgMin, 'mu'] = Config.MU
    networkUsageDf.loc[networkUsageDf['mu'] < Config.MU, 'mu'] = Config.MU
    networkUsageDf.loc[networkUsageDf['mu'] > 1, 'mu'] = 1
    networkUsageDf['eNetworkStatic'] = avgMax * Config.MU + backupNetworkEquipmentPowerUsage / amountNetworkIsSharedBy
    networkUsageDf['eNetworkDynamic'] = (1 - networkUsageDf['mu']) * networkUsageDf['eNetwork']
    networkUsageDf['eNetworkCalculatedWithConstant'] = networkUsageDf['eNetwork']
    networkUsageDf['eNetwork'] =  networkUsageDf['eNetworkStatic'] + networkUsageDf['eNetworkDynamic']

    print(networkUsageDf)
    return networkUsageDf

def calculateEnergyConsumption(serverInfo : dict) -> DataFrame:
    """Calculates the energy consumption used by the server and other sources

    Args:
        serverInfo (dict): The dictonary with all the serverinfo

    Returns:
        DataFrame: a dataframe with the hourly energy consumption
    """
    result = pd.read_csv(path.join(Config.DATAPATH, serverInfo['powerServerFile']), sep=',', skiprows=1)
    if Config.useMinuteDataForPower:
        result = wattToEServer(result)
    else:
        result.loc[:, "time"] = pd.to_datetime(result["time"], format="%d/%m/%Y %H:%M")
        result = result.set_index('time')
    result.sort_index(inplace=True)
    result['eServer'] = result['watts']
    result['eServerStatic'] = serverInfo['energyServerStatic']
    result['eServerDynamic'] = result['eServer'] - serverInfo['energyServerStatic']

    totalNetworkUsageDf = None
    if(isinstance(serverInfo['networkUsageFile'], str)) :
        totalNetworkUsageDf = calculateNetworkEnergyConsumption(serverInfo['networkUsageFile'], serverInfo['amountNetworkIsSharedBy'], serverInfo['backupNetworkEquipmentPowerUsage'])
    else:
        for networkFile in serverInfo['networkUsageFile']:
            networkUsageDf = calculateNetworkEnergyConsumption(networkFile, serverInfo['amountNetworkIsSharedBy'], serverInfo['backupNetworkEquipmentPowerUsage'])
            if totalNetworkUsageDf is None:
                totalNetworkUsageDf = networkUsageDf
            else:
                totalNetworkUsageDf['eNetwork'] += networkUsageDf['eNetwork']
                totalNetworkUsageDf['eNetworkStatic'] += networkUsageDf['eNetworkStatic']
                totalNetworkUsageDf['eNetworkDynamic'] += networkUsageDf['eNetworkDynamic']
                totalNetworkUsageDf['bytesMoved'] += networkUsageDf['bytesMoved']

    result = result.join(totalNetworkUsageDf)
    print(result)

    result['eCooling'] = (serverInfo['PUE'] - 1) * (result['eServer'] + result['eNetwork'])
    result['nu'] = (result['eServerStatic'] + result['eNetworkStatic']) / (result['eServer'] + result['eNetwork'])
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
