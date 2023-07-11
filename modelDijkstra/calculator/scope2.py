
from random import randint
import logging
from os import path
import sys
import numpy as np
import matplotlib.pyplot as plt

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

    # plotted = prunnedRawServerDf[(prunnedRawServerDf['Time'] > '03/27/2023 10') & (prunnedRawServerDf['Time'] < '03/27/2023 11')]
    # plotted['minute'] = pd.to_datetime(plotted['Time'], errors='coerce').dt.minute
    # print(plotted)
    # plotted.plot(x='minute', y=['Platform-Curr'], xlabel="Time in minutes", ylabel="Server Watt usage", legend=False)
    # plt.show()
    # sys.exit()

    # prunnedRawServerDf.sort_index(inplace=True)

    #conversion from watts to kwh
    prunnedRawServerDf.loc[:, 'Duration'] = np.abs(pd.to_datetime(prunnedRawServerDf['Time'], errors='coerce').diff(-1).dt.total_seconds())
    prunnedRawServerDf.drop(prunnedRawServerDf.tail(1).index,inplace=True)
    prunnedRawServerDf.loc[:, 'DurationInHours'] = prunnedRawServerDf['Duration'] / 3600

    prunnedRawServerDf.loc[:, 'watts'] = prunnedRawServerDf['DurationInHours'] * prunnedRawServerDf['Platform-Curr']

    #group by hour
    serverDataDf = prunnedRawServerDf[['Time', 'watts']].copy()
    serverDataDf.loc[:, "time"] = pd.to_datetime(serverDataDf["Time"])
    serverDataDf = serverDataDf.resample('60min', on='time').sum(numeric_only=True)

    return serverDataDf


def calculateNetwork(datapath : str, filename : str, amountNetworkIsSharedBy : int) -> DataFrame:
    """Calculates the amount of network usage in bytes

    Args:
        datapath (str) : the path to the data files
        serverInfo (dict): The dictonary with all the serverinfo

    Returns:
        DataFrame: returns hourly data of network usage in bytes
    """
    networkUsageDf = pd.read_csv(path.join(datapath, filename), sep=',', skiprows=1)
    networkUsageDf['time'] = pd.to_datetime(networkUsageDf['time'], unit='s')
    # networkUsageDf = networkUsageDf[(networkUsageDf['time'] >= '2023-03-27') & (networkUsageDf['time'] <= '2023-04-04')]
    networkUsageDf = networkUsageDf.resample('60min', on='time').mean().interpolate('time')
    #divided by two since there are two servers
    networkUsageDf['bytesMoved'] = (networkUsageDf['in'] + networkUsageDf['out']) * 60 * 60 / amountNetworkIsSharedBy
    networkUsageDf = networkUsageDf[['bytesMoved']]
    networkUsageDf = networkUsageDf[networkUsageDf['bytesMoved'] > 0]
    return networkUsageDf

def calculateNetworkEnergyConsumption(datapath : str, filename : str, amountNetworkIsSharedBy : int, backupNetworkEquipmentPowerUsage : int) -> DataFrame:
    """Calculates the network enenery consumption in a dynamic and static part

    Args:
        datapath (str): the path to the data files
        filename (str): The dictonary with all the serverinfo
        amountNetworkIsSharedBy (int): the amount of servers for which the network is shared by
        backupNetworkEquipmentPowerUsage (int): the power consumption of the backup network devices

    Returns:
        Dataframe: the hourly energy consumption of the network
    """
    networkUsageDf = calculateNetwork(datapath, filename, amountNetworkIsSharedBy)

    networkUsageDf['bytesMoved'] = networkUsageDf['bytesMoved'].fillna(0)
    networkUsageDf['eNetwork'] = networkUsageDf['bytesMoved'] * Config.WHPERBYTE
    peaks = networkUsageDf[networkUsageDf['eNetwork'] > 0].resample('D')['eNetwork'].max()
    valleys = networkUsageDf[networkUsageDf['eNetwork'] > 0].resample('D')['eNetwork'].min()
    avgMax = np.nanmedian(peaks)
    avgMin = np.nanmedian(valleys)
    # print(peaks, valleys)
    networkUsageDf['mu'] = 1 - (1 - Config.MU) * (networkUsageDf['eNetwork'] - avgMin ) / avgMax
    networkUsageDf.loc[networkUsageDf['eNetwork'] < avgMin, 'mu'] = 1
    networkUsageDf.loc[networkUsageDf['mu'] < Config.MU, 'mu'] = Config.MU
    networkUsageDf.loc[networkUsageDf['mu'] > 1, 'mu'] = 1
    # print(networkUsageDf.loc[networkUsageDf.index > '2023-03-01','eNetwork'])
    networkUsageDf['eNetworkStatic'] = avgMax * Config.MU + backupNetworkEquipmentPowerUsage / amountNetworkIsSharedBy
    networkUsageDf['eNetworkDynamic'] = (1 - networkUsageDf['mu']) * networkUsageDf['eNetwork']
    networkUsageDf['eNetwork'] =  networkUsageDf['eNetworkStatic'] + networkUsageDf['eNetworkDynamic']

    return networkUsageDf

def calculateEnergyConsumption(datapath: str, serverInfo : dict) -> DataFrame:
    """Calculates the energy consumption used by the server and other sources

    Args:
        datapath (str) : the path to the data files
        serverInfo (dict): The dictonary with all the serverinfo

    Returns:
        DataFrame: a dataframe with the hourly energy consumption
    """
    result = pd.read_csv(path.join(datapath, serverInfo['powerServerFile']), sep=',', skiprows=1)
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
    #if there are more than one network device loop over all network devices
    if(isinstance(serverInfo['networkUsageFile'], str)) :
        totalNetworkUsageDf = calculateNetworkEnergyConsumption(datapath, serverInfo['networkUsageFile'], serverInfo['amountNetworkIsSharedBy'], serverInfo['backupNetworkEquipmentPowerUsage'])
    else:
        for networkFile in serverInfo['networkUsageFile']:
            networkUsageDf = calculateNetworkEnergyConsumption(datapath, networkFile, serverInfo['amountNetworkIsSharedBy'], serverInfo['backupNetworkEquipmentPowerUsage'])
            if totalNetworkUsageDf is None:
                totalNetworkUsageDf = networkUsageDf
            else:
                totalNetworkUsageDf['eNetwork'] += networkUsageDf['eNetwork']
                totalNetworkUsageDf['eNetworkStatic'] += networkUsageDf['eNetworkStatic']
                totalNetworkUsageDf['eNetworkDynamic'] += networkUsageDf['eNetworkDynamic']
                totalNetworkUsageDf['bytesMoved'] += networkUsageDf['bytesMoved']

    result = result.join(totalNetworkUsageDf)

    result['eCooling'] = (serverInfo['PUE'] - 1) * (result['eServer'] + result['eNetwork'])
    result['nu'] = (result['eServerStatic'] + result['eNetworkStatic']) / (result['eServer'] + result['eNetwork'])
    result['eCoolingStatic'] = result['nu'] * result['eCooling']
    result['eCoolingDynamic'] = (1 - result['nu']) * result['eCooling']

    result['scope2E'] = result['eServer'] + result['eNetwork'] + result['eCooling']
    result['scope2ELower'] = Config.GAMMA_LOWER * (result['eServerStatic'] + result['eNetworkStatic'] + result['eCoolingStatic']) + Config.ZETA_LOWER * (result['eServerDynamic'] + result['eNetworkDynamic'] + result['eCoolingDynamic'])
    result['scope2EUpper'] = Config.GAMA_UPPER * (result['eServerStatic'] + result['eNetworkStatic'] + result['eCoolingStatic']) + Config.ZETA_UPPER * (result['eServerDynamic'] + result['eNetworkDynamic'] + result['eCoolingDynamic'])

    return result

def calculate(datapath : str, serverInfo : dict) -> DataFrame:
    """Calculates the scope 2 emissions

    Args:
        datapath (str) : the path to the data files
        serverInfo (dict): The dictonary with all the serverinfo

    Returns:
        DataFrame: returns the hourly scope 2 emissions data
    """
    result = calculateEnergyConsumption(datapath, serverInfo)

    carbonIntensityDf =  pd.read_csv(path.join(datapath, serverInfo['carbonIntensityFile']), sep=',', skiprows=1)
    carbonIntensityDf['time'] = pd.to_datetime(carbonIntensityDf['Datetime (UTC)']).dt.tz_localize(None)
    # print(carbonIntensityDf.columns)
    #divide it by 1000 to translate from kwh to wh
    carbonIntensityDf['ci'] = carbonIntensityDf['London'] / 1000
    # carbonIntensityDf = carbonIntensityDf.set_index('time')
    carbonIntensityDf = carbonIntensityDf.resample('60min', on='time').mean(numeric_only=True)
    carbonIntensityDf = carbonIntensityDf[['ci']]
    result = result.join(carbonIntensityDf)

    if Config.USEHOURLYCARBON:
        result['scope2Lower'] = result['scope2ELower'] * result['ci']
        result['scope2Upper'] = result['scope2EUpper'] * result['ci']
    else:
        result['scope2Lower'] = result['scope2ELower'] * Config.CARBONINTENSITY
        result['scope2Upper'] = result['scope2EUpper'] * Config.CARBONINTENSITY

    return result
