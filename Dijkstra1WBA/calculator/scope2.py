
from random import randint
import logging
from os import path
import sys

import numpy as np
import pandas as pd
from ..config import Config
from pandas import DataFrame


def wattToEServer(rawServerDf : DataFrame) -> DataFrame:
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
    networkUsageDf = pd.read_csv(path.join(Config.DATAPATH, serverInfo['networkUsageFile']), sep=',', skiprows=1)
    networkUsageDf['time'] = pd.to_datetime(networkUsageDf['time'], unit='s')
    # networkUsageDf = networkUsageDf[(networkUsageDf['time'] >= '2023-03-27') & (networkUsageDf['time'] <= '2023-04-04')]
    networkUsageDf = networkUsageDf.resample('60min', on='time').mean().interpolate('time')
    #divided by two since there are two servers
    networkUsageDf['bytesMoved'] = (networkUsageDf['in'] + networkUsageDf['out']) * 60 * 60 / 2
    networkUsageDf = networkUsageDf[['bytesMoved']]
    return networkUsageDf

def calculateEnergyConsumption(serverInfo : dict) -> DataFrame:

    # result = wattToEServer(rawDataDf)
    result = pd.read_csv(path.join(Config.DATAPATH, serverInfo['powerServerFile']), sep=',', skiprows=1)
    result.loc[:, "time"] = pd.to_datetime(result["time"], format="%d/%m/%Y %H:%M")
    result = result.set_index('time')
    result.sort_index(inplace=True)
    result['eServer'] = result['watts']
    result['eServerStatic'] = Config.SERVERSTATICWATTS
    result['eServerDynamic'] = result['eServer'] - Config.SERVERSTATICWATTS

    networkUsageDf = calculateNetwork(serverInfo)
    result = result.join(networkUsageDf)
    
    
    result['bytesMoved'] = result['bytesMoved'].fillna(0)
    result['eNetwork'] = result['bytesMoved'] * Config.WHPERBYTE
    result['eNetworkStatic'] = Config.MU * result['eNetwork']
    result['eNetworkDynamic'] = (1 - Config.MU) * result['eNetwork']
    # result['eNetworkStatic'] = 12
    # result['eNetworkDynamic'] = (1 - Config.MU) * result['eNetwork']

    result['eCooling'] = (serverInfo['PUE'] - 1) * (result['eServer'] + result['eNetwork'])
    result['nu'] = (result['eServerStatic'] + result['eNetworkStatic']) / (result['eServer'] + result['eNetwork'])
    result['eCoolingStatic'] = result['nu'] * result['eCooling']
    result['eCoolingDynamic'] = (1 - result['nu']) * result['eCooling']

    result['scope2E'] = result['eServer'] + result['eNetwork'] + result['eCooling']
    result['scope2ELower'] = Config.GAMMA_LOWER * (result['eServerStatic'] + result['eNetworkStatic'] + result['eCoolingStatic']) + Config.ZETA_LOWER * (result['eServerDynamic'] + result['eNetworkDynamic'] + result['eCoolingDynamic'])
    result['scope2EUpper'] = Config.GAMA_UPPER * (result['eServerStatic'] + result['eNetworkStatic'] + result['eCoolingStatic']) + Config.ZETA_UPPER * (result['eServerDynamic'] + result['eNetworkDynamic'] + result['eCoolingDynamic'])
    
    return result

def calculate(serverInfo : dict) -> DataFrame:
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
    result['scope2Lower'] = result['scope2ELower'] * result['ci']
    result['scope2Upper'] = result['scope2EUpper'] * result['ci']
    return result