"""
If necessary these scripts can be used to help determine the static power consumption
of the server
"""

from os import path

import pandas as pd
from pandas import DataFrame
from sklearn import linear_model

from .calculator.scope2 import wattToEServer


def readServerStatistics(datapath : str) -> DataFrame:
    """Reads the server statistics needed for the determination

    Args:
        datapath (str) : the path to the data files

    Returns:
        DataFrame: the preprocessed data
    """
    cpuDf = pd.read_csv(path.join(datapath, 'FDX_week_CPU.csv'), sep=',', skiprows=1)
    diskDf = pd.read_csv(path.join(datapath, 'FDX_week_Disk.csv'), sep=',', skiprows=1)
    memDf = pd.read_csv(path.join(datapath, 'FDX_week_MEM.csv'), sep=',', skiprows=1)

    result = cpuDf[['Time']].copy()
    result['cpu'] = cpuDf['Usage']
    result['disk'] = diskDf['Usage']
    result['mem'] = memDf['Consumed']

    result = result.dropna()
    result['Time'] = pd.to_datetime(result['Time'])
    result['Time'] = result['Time'].dt.tz_localize(None)
    return result

def calculateParametersOfServer(datapath: str, serverInfo : dict) -> None:
    """Calculates the cooefficients and intercipt of the regression

    Args:
        datapath (str) : the path to the data files
        serverInfo (dict): The dictonary with all the serverinfo

    Returns: nothing
    """
    serverEnergyDf = pd.read_csv(path.join(datapath, serverInfo['powerServerFile']), sep=',', skiprows=1)
    serverDf = wattToEServer(serverEnergyDf)
    serverDf['Time'] = serverDf.index
    serverDf = serverDf.resample('120min', on='Time').mean()
    # serverDf['Time'] = serverDf.index
    print(serverDf)
    serverStatisticsDf = readServerStatistics(datapath)
    print(serverStatisticsDf)
    statsDf = serverStatisticsDf.merge(serverDf, how='left', on='Time').sort_values(by='Time')
    statsDf = statsDf.dropna()
    statsDf = statsDf.iloc[2:-2]
    print(statsDf)

    regr = linear_model.LinearRegression()
    
    regr.fit(statsDf[['cpu']], statsDf['eServer'])
    print(regr.intercept_)
    print(regr.coef_)
