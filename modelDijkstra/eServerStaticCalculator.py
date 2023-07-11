from os import path

import pandas as pd
from pandas import DataFrame
from .config import Config
from .calculator.scope2 import wattToEServer
from sklearn import linear_model
import logging

def readServerStatistics() -> DataFrame:
    """Reads the server statistics needed for the determination

    Returns:
        DataFrame: the preprocessed data
    """
    cpuDf = pd.read_csv(path.join(Config.DATAPATH, 'FDX_week_CPU.csv'), sep=',', skiprows=1)
    diskDf = pd.read_csv(path.join(Config.DATAPATH, 'FDX_week_Disk.csv'), sep=',', skiprows=1)
    memDf = pd.read_csv(path.join(Config.DATAPATH, 'FDX_week_MEM.csv'), sep=',', skiprows=1)

    result = cpuDf[['Time']].copy()
    result['cpu'] = cpuDf['Usage']
    result['disk'] = diskDf['Usage']
    result['mem'] = memDf['Consumed']

    result = result.dropna()
    result['Time'] = pd.to_datetime(result['Time'])
    result['Time'] = result['Time'].dt.tz_localize(None)
    return result

def calculateParametersOfServer(serverInfo : dict) -> None:
    """Calculates the cooefficients and intercipt of the regression

    Args:
        serverInfo (dict): The dictonary with all the serverinfo

    Returns: nothing
    """
    serverEnergyDf = pd.read_csv(path.join(Config.DATAPATH, serverInfo['powerServerFile']), sep=',', skiprows=1)
    serverDf = wattToEServer(serverEnergyDf)
    serverDf['Time'] = serverDf.index
    serverDf = serverDf.resample('120min', on='Time').mean()
    # serverDf['Time'] = serverDf.index
    print(serverDf)
    serverStatisticsDf = readServerStatistics()
    print(serverStatisticsDf)
    statsDf = serverStatisticsDf.merge(serverDf, how='left', on='Time').sort_values(by='Time')
    statsDf = statsDf.dropna()
    statsDf = statsDf.iloc[2:-2]
    print(statsDf)

    regr = linear_model.LinearRegression()
    #mem is  aproblem
    regr.fit(statsDf[['cpu']], statsDf['eServer'])
    print(regr.intercept_)
    print(regr.coef_)
