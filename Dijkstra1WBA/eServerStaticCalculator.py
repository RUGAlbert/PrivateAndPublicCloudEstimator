from os import path

import pandas as pd
from pandas import DataFrame
from .config import Config
from .calculator.scope2 import wattToEServer
from sklearn import linear_model

def readServerStatistics() -> DataFrame:
    cpuDf = pd.read_csv(path.join(Config.DATAPATH, 'CPU_sample.csv'), sep=',', skiprows=1)
    diskDf = pd.read_csv(path.join(Config.DATAPATH, 'DISKIO_sample.csv'), sep=',', skiprows=1)
    memDf = pd.read_csv(path.join(Config.DATAPATH, 'MEM_sample.csv'), sep=',', skiprows=1)
    
    result = cpuDf[['Time']].copy()
    result['cpu'] = cpuDf['Usage for 195.213.64.174']
    result['disk'] = diskDf['Usage for 195.213.64.174']
    result['mem'] = memDf['Consumed for 195.213.64.174']

    result = result.dropna()
    result['Time'] = pd.to_datetime(result['Time'])
    result['Time'] = result['Time'].dt.tz_localize(None)
    return result

def calculateParametersOfServer(serverInfo : dict) -> DataFrame:
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
    statsDf = statsDf.iloc[10:-10]
    print(statsDf)

    regr = linear_model.LinearRegression()
    #mem is  aproblem
    regr.fit(statsDf[['cpu', 'disk', 'mem']], statsDf['eServer'])
    print(regr.intercept_)
    print(regr.coef_)
