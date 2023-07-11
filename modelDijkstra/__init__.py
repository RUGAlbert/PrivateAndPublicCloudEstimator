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
from sklearn.metrics import mean_squared_error

from .calculator import calculateEmmisionsOfServer
from .checkConcurrentUsers import plotConccurentUsers
from .config import Config


def createOutputFolder():
    """Creates output folder for the csv files
    """    
    outputFolder = path.join(Config.DATAPATH, 'output')
    if not os.path.exists(outputFolder):
        os.makedirs(outputFolder)

def calculateConcurrentUsers(serversInfo : dict) -> DataFrame:
    """Calculates the concurrent users

    Args:
        serversInfo (dict): The dictonary with all the serverinfo

    Returns:
        DataFrame: the hourly concurrent users
    """    
    userLoginDataDf = pd.read_csv(path.join(Config.DATAPATH, serversInfo['concurrentUsersFile']), sep=',', skiprows=1)

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


def preprocessConcurrentUsers(serversInfo : dict) -> DataFrame:
    """Make sure the raw max user data is in the right format for the rest of the program

    Args:
        serversInfo (dict): The dictonary with all the serverinfo

    Returns:
        DataFrame: the maxium concurrent users per hour
    """    
    concurrentUserDf = pd.read_csv(path.join(Config.DATAPATH, serversInfo['concurrentUsersFile']), sep=',', skiprows=1)
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

def calculateScore(regressor : LinearRegression, xStart : float, xEnd : float) -> float:
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

    # X = (resultDf['maxUsers'].iloc[:].values.reshape(-1, 1))  # values converts it into a numpy array
    # Y = (resultDf['TCFPLowerPerUser'].iloc[:].values.reshape(-1, 1))
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
    calculateScore(regressor, min(X), max(X))
    print("95 percent is less than", calculatePercentile(regressor, X, 5)[0][0])
    print("50 percent is less than", calculatePercentile(regressor, X, 50)[0][0])
    print("5 percent is less than", calculatePercentile(regressor, X, 95)[0][0])
    return X, YPred

def start(serversInfo : dict):
    """Calculate the emissions and save it to the csv files

    Args:
        serversInfo (dict): the info for all the servers
    """    
    createOutputFolder()
    print(serversInfo)
    # calculateConcurrentUsers(serversInfo)
    concurrentUserDf = preprocessConcurrentUsers(serversInfo)
    # print(concurrentUserDf)
    plotConccurentUsers(concurrentUserDf)


    totalDf = DataFrame()

    for server in serversInfo['servers']:
        #Works with QT on linux
        print(server['name'])
        emmisionsOfServer = calculateEmmisionsOfServer(server)
        resultDf = emmisionsOfServer.merge(concurrentUserDf, how='left', on='time').sort_values(by='time')
        # resultDf['maxUsers'] = resultDf['maxUsers'].fillna(1)
        # resultDf = resultDf[(~resultDf['maxUsers'].isna()) & (resultDf['eNetworkDynamic'] > 0)]
        resultDf = resultDf[(~resultDf['maxUsers'].isna())]
        #normalize data
        resultDf['TCFPLowerPerUser'] = resultDf['TCFPLower'] / resultDf['maxUsers']
        resultDf['TCFPUpperPerUser'] = resultDf['TCFPUpper'] / resultDf['maxUsers']
        resultDf['scope2EPerUser'] = resultDf['scope2E'] / resultDf['maxUsers']

        # XPred, YPred = doLinearRegression(resultDf)

        # print(min(regressor.predict(X)))

        resultDf = resultDf.round(2)

        # totalDf = pd.concat([totalDf, resultDf]).groupby(['time']).sum().reset_index()
        if(len(totalDf) > 0):
            totalDf = totalDf.add(resultDf[resultDf.index.isin(totalDf.index)], fill_value=0)
        else:
            totalDf = totalDf.add(resultDf, fill_value=0)
        # print(resultDf['mu'])
        totalDf[['mu', 'maxUsers', 'ci']] = resultDf[['mu', 'maxUsers', 'ci']]
        totalDf = totalDf[totalDf.index.isin(resultDf.index)]

        if False:
            #make it cummalative
            cumDf = resultDf.groupby(resultDf.index.to_period('m')).cumsum()
            # cumDf[(cumDf['maxUsers'] > 1) & cumDf['eNetworkDynamic'] > 0].plot(use_index=True, y=['TCFPLower', 'TCFPUpper'])

            # usefullData = resultDf[(resultDf['maxUsers'] > 1) & (resultDf['eNetworkDynamic'] > 0)]
            # plt.get_current_fig_manager().window.wm_geometry("+0+0")
            # resultDf.plot(use_index=True, y=['ci'])
            # plt.get_current_fig_manager().window.wm_geometry("+800+0")
            # resultDf.plot.scatter(x='maxUsers', y='TCFPUpperPerUser', c='DarkBlue', title='New algorithm'))
            # plt.plot(XPred, YPred, color='red')

            # resultDf['ci'] *= 1000
            # resultDf.plot(use_index=True, y=['TCFPLowerPerUser', 'TCFPUpperPerUser'])
            # usefullData.plot(use_index=True, y=['TCFPLower', 'TCFPUpper'])

            # plt.get_current_fig_manager().window.wm_geometry("+0+500")
            _, ax = plt.subplots()
            resultDf.plot(use_index=True, y=['eNetworkCalculatedWithConstant'], ax = ax, ylabel="total power usage in wH", legend=False)
            resultDf.plot(use_index=True, y=['mu'], ax = ax, secondary_y = True, ylabel="max users per hour", legend=False)
            plt.get_current_fig_manager().window.wm_geometry("+800+500")
        csvPath = path.join(Config.DATAPATH, 'output', server['name'] + '.csv')
        resultDf.to_csv(csvPath, sep=';')
        # break

    totalDf['maxUsers'].dropna(inplace=True)
    if not Config.useMinuteDataForPower:
        totalDf = totalDf[(totalDf.index <= '2023-04-21')]
    # print('average', np.mean(totalDf['TCFPUpper']), np.mean(totalDf['maxUsers']))
    XPred, YPred = doLinearRegression(totalDf)
    # totalDf.plot(use_index=True, y=['scope2E'], ax = ax, ylabel="total power usage in wH", legend=False)
    # totalDf.plot(use_index=True, y=['maxUsers'], ax = ax, secondary_y = True, ylabel="max users per hour", legend=False)

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

    # plt.show()
    # plt.hist(resultDf['TCFPUpper'])
    _, ax = plt.subplots()
    # totalDf['Concurrent users'] = resultDf['maxUsers']
    # totalDf['Total energy consumption'] = totalDf['scope2E']
    # totalDf.plot(use_index=True, y=['Concurrent users'],  ylabel="max concurrent users per hour", legend=False)
    # totalDf.plot(use_index=True, ax = ax, y=['Total energy consumption'], ylabel="total power usage in wH", legend=True)
    # totalDf.plot(use_index=True, ax = ax, y=['Concurrent users'], secondary_y = True, ylabel="max concurrent users per hour", legend=True)
    # plt.show()
    totalDf.plot.scatter(x='maxUsers', y='scope2EPerUser', c='DarkBlue', ax = ax, xlabel="amount of max users per hour", ylabel="TCFP per user in grams")
    plt.plot(XPred, YPred, color='red')
    plt.show()
    # ax.axvline(x=XPred[int(len(XPred)/100*5)], color='y')
    csvPath = path.join(Config.DATAPATH, 'output', 'total.csv')
    totalDf = totalDf.round(2)
    totalDf.to_csv(csvPath, sep=';')
    # plt.show()
