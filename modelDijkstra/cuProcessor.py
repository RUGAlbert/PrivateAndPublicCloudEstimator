"""
All the scripts to preprocess the concurrent user files
"""


from datetime import timedelta
from os import path
from pandas import DataFrame
import pandas as pd

from .config import Config


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
