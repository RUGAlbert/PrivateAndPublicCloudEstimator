'''
This is the start place of the calculation
'''

import logging
import os
from datetime import timedelta
from os import path
import matplotlib.pyplot as plt

import pandas as pd
from pandas import DataFrame

from .calculator import calculate
from .checkConcurrentUsers import plotConccurentUsers
from .config import Config


def createOutputFolder():
    outputFolder = path.join(Config.DATAPATH, 'output')
    if not os.path.exists(outputFolder):
        os.makedirs(outputFolder)


def calculateEmmisionsOfServer(serverInfo : dict) -> DataFrame:
    serverEnergyDf = pd.read_csv(path.join(Config.DATAPATH, serverInfo['powerServerFile']), sep=',', skiprows=1)
    return calculate(serverEnergyDf, serverInfo)

def calculateConcurrentUsers(serversInfo : dict) -> DataFrame:
    userLoginDataDf = pd.read_csv(path.join(Config.DATAPATH, serversInfo['concurrentUsersFile']), sep=',', skiprows=1)

    userLoginDataDf['start_time'] = pd.to_datetime(userLoginDataDf['LoginDate'] + " " + userLoginDataDf['LoginTime (GMT)'])
    userLoginDataDf['end_time'] = pd.to_datetime(userLoginDataDf['LogoutDate'] + " " + userLoginDataDf['LogoutTime'])
    print(userLoginDataDf)

    minTimeStamp = (userLoginDataDf['start_time'].min()).replace(minute=0, second=0)
    maxTimeStamp = (userLoginDataDf['end_time'].max()).replace(minute=0, second=0)

    print(minTimeStamp, maxTimeStamp)
    dates = pd.date_range(minTimeStamp, maxTimeStamp, freq='H')

    COEDF = pd.DataFrame({'timestamp': dates, 'minutes':0})

    for index, row in userLoginDataDf.iterrows():
        startLogin = row['start_time']
        endLogin = row['end_time']
        startHour = startLogin.replace(minute=0, second=0)
        endHour = endLogin.replace(minute=0, second=0)

        fullHoursRange = pd.date_range(startHour  + timedelta(hours=1), endHour - timedelta(hours=1), freq='H')

        #bug if there is a range smaller than 1 hour
        startHourMinutes = 60 - startLogin.minute
        endHourMinutes = endLogin.minute

        COEDF.loc[COEDF['timestamp'] == startHour, 'minutes'] += startHourMinutes
        COEDF.loc[COEDF['timestamp'] == endHour, 'minutes'] += endHourMinutes
        COEDF.loc[COEDF['timestamp'].isin(fullHoursRange), 'minutes'] += 60

    COEDF['COE'] = COEDF['minutes'] / 60
    print(COEDF)
    #normalize it to hours
    
    return COEDF


def preprocessConcurrentUsers(serversInfo : dict) -> DataFrame:
    concurrentUserDf = pd.read_csv(path.join(Config.DATAPATH, serversInfo['concurrentUsersFile']), sep=',', skiprows=1)
    concurrentUserDf['DateTime'] = pd.to_datetime(concurrentUserDf['Date'] + " " + concurrentUserDf['Time'], format="%d/%m/%Y %H:%M:%S")
    concurrentUserDf['time'] = concurrentUserDf['DateTime']
    concurrentUserDf['maxUsers'] = concurrentUserDf['Peak']
    concurrentUserDf = concurrentUserDf[['time', 'maxUsers']]
    concurrentUserDf = concurrentUserDf.resample('60min', on='time').max()

    return concurrentUserDf

def start(serversInfo : dict):
    createOutputFolder()
    # calculateConcurrentUsers(serversInfo)
    concurrentUserDf = preprocessConcurrentUsers(serversInfo)
    # plotConccurentUsers(concurrentUserDf)

    for server in serversInfo['servers']:
        print(server['name'])
        emmisionsOfServer = calculateEmmisionsOfServer(server)
        resultDf = emmisionsOfServer.merge(concurrentUserDf, how='left', on='time').sort_values(by='time')
        resultDf['maxUsers'] = resultDf['maxUsers'].fillna(1)
        #normalize data
        # resultDf['TCFPLower'] = resultDf['TCFPLower'] / resultDf['maxUsers']
        # resultDf['TCFPUpper'] = resultDf['TCFPUpper'] / resultDf['maxUsers']
        resultDf = resultDf.round(2)
        print(resultDf)
        resultDf.plot(use_index=True, y=['eServerDynamic', 'eServerStatic', 'maxUsers'])
        csvPath = path.join(Config.DATAPATH, 'output', server['name'] + '.csv')
        resultDf.to_csv(csvPath, sep=';')
    # plt.show()
