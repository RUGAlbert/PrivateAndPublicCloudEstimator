'''
This is the start place of the calculation
'''

import logging
import os
from datetime import timedelta
from os import path
from typing import Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pandas import DataFrame
from sklearn.linear_model import LinearRegression

from .calculator import calculateEmmisionsOfServer
from .config import Config


def createOutputFolder(datapath : str):
    """Creates output folder for the csv files

    Args:
        datapath (str) : the path to the data files
    """
    outputFolder = path.join(datapath, 'output')
    if not os.path.exists(outputFolder):
        os.makedirs(outputFolder)

def calculateConcurrentUsers(datapath : str, serversInfo : dict) -> DataFrame:
    """Calculates the concurrent users

    Args:
        datapath (str) : the path to the data files
        serversInfo (dict): The dictonary with all the serverinfo

    Returns:
        DataFrame: the hourly concurrent users
    """
    userLoginDataDf = pd.read_csv(path.join(datapath, serversInfo['concurrentUsersFile']), sep=',', skiprows=1)

    userLoginDataDf['start_time'] = pd.to_datetime(userLoginDataDf['LoginDate'] + " " + userLoginDataDf['LoginTime (GMT)'])
    userLoginDataDf['end_time'] = pd.to_datetime(userLoginDataDf['LogoutDate'] + " " + userLoginDataDf['LogoutTime'])

    minTimeStamp = (userLoginDataDf['start_time'].min()).replace(minute=0, second=0)
    maxTimeStamp = (userLoginDataDf['end_time'].max()).replace(minute=0, second=0)

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
    #normalize it to hours

    return COEDF


def preprocessConcurrentUsers(datapath : str, serversInfo : dict) -> DataFrame:
    """Make sure the raw max user data is in the right format for the rest of the program

    Args:
        datapath (str) : the path to the data files
        serversInfo (dict): The dictonary with all the serverinfo

    Returns:
        DataFrame: the maxium concurrent users per hour
    """
    concurrentUserDf = pd.read_csv(path.join(datapath, serversInfo['concurrentUsersFile']), sep=',', skiprows=1)
    if Config.useMinuteDataForPower:
        concurrentUserDf['DateTime'] = pd.to_datetime(concurrentUserDf['Date'] + " " + concurrentUserDf['Time'], format="%Y-%m-%d %H:%M:%S")
    else:
        concurrentUserDf['DateTime'] = pd.to_datetime(concurrentUserDf['Date'] + " " + concurrentUserDf['Time'], format="%d/%m/%Y %H:%M:%S")
    concurrentUserDf['time'] = concurrentUserDf['DateTime'] - timedelta(hours=serversInfo['userTZ'])
    concurrentUserDf['maxUsers'] = concurrentUserDf['Loggedin']
    concurrentUserDf = concurrentUserDf[['time', 'maxUsers']]

    concurrentUserDf = concurrentUserDf.resample('60min', on='time').max()
    concurrentUserDf['maxUsers'].replace(0, 1, inplace=True)
    return concurrentUserDf

def calculateUPESAScore(regressor : LinearRegression, xStart : float, xEnd : float) -> float:
    """Calculates the score of the regression based on the
     relation between total carbon footprint and maxusers

    Args:
        regressor (LinearRegression): the regressor which estimats the line
        for the relationship between the total carbon footprint per user and the maxusers

    Returns:
        float: the score
    """
    predictedY = regressor.predict(np.arange(xStart, xEnd).reshape(-1,1))

    YPred = 1/ (np.power(predictedY, 1/Config.POWERFUNCTIONFORREGRESSION))

    score = np.sum(YPred) / (xEnd-xStart)
    print("Area score", score[0])
    return score


def calculatePercentile(regressor : LinearRegression, X : DataFrame, percentile : float) -> float:
    xVal = X[int(len(X)/100*percentile)]
    yVal = 1/ (np.power(regressor.predict((xVal,)), 1/Config.POWERFUNCTIONFORREGRESSION))
    return yVal

def doLinearRegression(resultDf : DataFrame) -> Tuple[DataFrame, DataFrame]:
    """Make the linear regression between the totalcarbon footprint per user and the maxusers

    Args:
        resultDf (DataFrame): the df which also has the columns tcf per user and maxusers per hour

    Returns:
        Tuple[DataFrame, DataFrame]: returns the x and y data for the prediction
    """
    
    XY = np.column_stack((resultDf['maxUsers'], resultDf['scope2EPerUser']))
    XY = XY[np.argsort(XY[:, 0])]

    X = XY[:,0].reshape(-1,1)
    Y = XY[:,1].reshape(-1,1)

    #Get best powerfunction

    bestScore = 0

    for pwr in np.arange(Config.PWRFUNCREGMIN, Config.PWRFUNCREGMAX, 0.05):
        regressor = LinearRegression()
        regressor.fit(X, 1/ (np.power(Y, pwr)))
        curScore = regressor.score(X, 1/ (np.power(Y, pwr)))
        if curScore > bestScore:
            bestScore = curScore
            Config.POWERFUNCTIONFORREGRESSION = pwr

    regressor = LinearRegression()
    regressor.fit(X, 1/ (np.power(Y, Config.POWERFUNCTIONFORREGRESSION)))
    # regressor.fit(X, Y)  # perform linear regression
    print("mSQR of ", bestScore, "for a n-value of ", Config.POWERFUNCTIONFORREGRESSION)
    predictedY = regressor.predict(X)
    # print("Coefficient", regressor.coef_)
    YPred = 1/ (np.power(predictedY, 1/Config.POWERFUNCTIONFORREGRESSION))
    calculateUPESAScore(regressor, min(X), max(X))
    print("95 percent is less than", calculatePercentile(regressor, X, 5)[0][0])
    print("50 percent is less than", calculatePercentile(regressor, X, 50)[0][0])
    print("5 percent is less than", calculatePercentile(regressor, X, 95)[0][0])
    return X, YPred

def start(datapath : str, serversInfo : dict):
    """Calculate the emissions and save it to the csv files

    Args:
        datapath (str) : the path to the data files
        serversInfo (dict): the info for all the servers
    """
    createOutputFolder(datapath)
    concurrentUserDf = preprocessConcurrentUsers(datapath, serversInfo)


    totalDf = DataFrame()

    for server in serversInfo['servers']:
        
        print(server['name'])
        emmisionsOfServer = calculateEmmisionsOfServer(datapath, server)
        resultDf = emmisionsOfServer.merge(concurrentUserDf, how='left', on='time').sort_values(by='time')
        resultDf = resultDf[(~resultDf['maxUsers'].isna())]

        #normalize data
        resultDf['TCFPLowerPerUser'] = resultDf['TCFPLower'] / resultDf['maxUsers']
        resultDf['TCFPUpperPerUser'] = resultDf['TCFPUpper'] / resultDf['maxUsers']
        resultDf['scope2EPerUser'] = resultDf['scope2E'] / resultDf['maxUsers']

        resultDf = resultDf.round(2)
        if(len(totalDf) > 0):
            totalDf = totalDf.add(resultDf[resultDf.index.isin(totalDf.index)], fill_value=0)
        else:
            totalDf = totalDf.add(resultDf, fill_value=0)
        
        totalDf[['maxUsers', 'ci']] = resultDf[['maxUsers', 'ci']]
        totalDf = totalDf[totalDf.index.isin(resultDf.index)]
        csvPath = path.join(datapath, 'output', server['name'] + '.csv')
        resultDf.to_csv(csvPath, sep=';')

    totalDf['maxUsers'].dropna(inplace=True)
    if not Config.useMinuteDataForPower:
        totalDf = totalDf[(totalDf.index <= '2023-04-21')]

    _, _ = doLinearRegression(totalDf)

    avgEServer = np.mean(totalDf['eServerStatic'] + totalDf['eServerDynamic'])
    avgENetwork = np.mean(totalDf['eNetworkStatic'] + totalDf['eNetworkDynamic'])
    avgECooling = np.mean(totalDf['eCoolingStatic'] + totalDf['eCoolingDynamic'])
    avgETotal = avgEServer + avgENetwork + avgECooling

    avgEStatic = np.mean(totalDf['eServerStatic'] + totalDf['eNetworkStatic'] + totalDf['eCoolingStatic'])
    avgEDynamic = np.mean(totalDf['eServerDynamic'] + totalDf['eNetworkDynamic'] + totalDf['eCoolingDynamic'])

    print('percentages of different components: Server:', (avgEServer / avgETotal).round(2),
          "Network:", (avgENetwork / avgETotal).round(2),
          "Cooling:", (avgECooling / avgETotal).round(2))


    print('percentages of static/dynamic', (avgEStatic/(avgEStatic + avgEDynamic)).round(2), (avgEDynamic/(avgEStatic + avgEDynamic)).round(2))

    csvPath = path.join(datapath, 'output', 'total.csv')
    totalDf = totalDf.round(2)
    totalDf.to_csv(csvPath, sep=';')
