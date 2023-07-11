'''
This is the start place of the calculation
'''

import os
from os import path
from typing import Tuple

import numpy as np
from pandas import DataFrame

from .calculator import calculateEmmisionsOfServer
from .config import Config

from .cuProcessor import preprocessConcurrentUsers
from .scoreCalculator import doLinearRegression


def createOutputFolder(datapath : str):
    """Creates output folder for the csv files

    Args:
        datapath (str) : the path to the data files
    """
    outputFolder = path.join(datapath, 'output')
    if not os.path.exists(outputFolder):
        os.makedirs(outputFolder)

def getStaticAndDynamicPercentage(totalDf : DataFrame) -> Tuple[float, float]:
    """Calculates the average static and dynamic percentage

    Args:
        totalDf (DataFrame): the dataframe with all energy consumption of all servers

    Returns:
        (float, float): percentage of dynamic and static energy usage
    """

    avgEStatic = np.mean(totalDf['eServerStatic'] + totalDf['eNetworkStatic'] + totalDf['eCoolingStatic'])
    avgEDynamic = np.mean(totalDf['eServerDynamic'] + totalDf['eNetworkDynamic'] + totalDf['eCoolingDynamic'])
    staticPercent = (avgEStatic/(avgEStatic + avgEDynamic)).round(2)
    dynamicPercent = (avgEDynamic/(avgEStatic + avgEDynamic)).round(2)

    return staticPercent, dynamicPercent

def getPercentageDifferentComponents(totalDf : DataFrame) -> Tuple[float, float, float]:
    """Calculates the average percentage that different components have

    Args:
        totalDf (DataFrame): the dataframe with all energy consumption of all servers

    Returns:
        (float, float, float): percentage of server, network and cooling
    """

    avgEServer = np.mean(totalDf['eServerStatic'] + totalDf['eServerDynamic'])
    avgENetwork = np.mean(totalDf['eNetworkStatic'] + totalDf['eNetworkDynamic'])
    avgECooling = np.mean(totalDf['eCoolingStatic'] + totalDf['eCoolingDynamic'])
    avgETotal = avgEServer + avgENetwork + avgECooling

    eServerPercent = (avgEServer / avgETotal).round(2)
    eNetworkPercent = (avgENetwork / avgETotal).round(2)
    eCoolingPercent = (avgECooling / avgETotal).round(2)

    return eServerPercent, eNetworkPercent, eCoolingPercent


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

    _,_ = doLinearRegression(totalDf)

    eServerPercent, eNetworkPercent, eCoolingPercent = getPercentageDifferentComponents(totalDf)

    print('percentages of different components: Server:', eServerPercent,
          "Network:", eNetworkPercent,
          "Cooling:", eCoolingPercent)


    print('percentages of static/dynamic', getStaticAndDynamicPercentage(totalDf))

    csvPath = path.join(datapath, 'output', 'total.csv')
    totalDf = totalDf.round(2)
    totalDf.to_csv(csvPath, sep=';')
