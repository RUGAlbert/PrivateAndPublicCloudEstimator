'''
This is the start place of the calculation
'''

from os import path

import pandas as pd
import os
from pandas import DataFrame

from .calculator import calculate
from .config import Config

def createOutputFolder():
    outputFolder = path.join(Config.DATAPATH, 'output')
    if not os.path.exists(outputFolder):
        os.makedirs(outputFolder)


def calculateEmmisionsOfServer(serverInfo : dict) -> DataFrame:
    serverEnergyDf = pd.read_csv(path.join(Config.DATAPATH, serverInfo['powerServerFile']), sep=',', skiprows=1)
    return calculate(serverEnergyDf, serverInfo)

def start(serversInfo : dict):
    createOutputFolder()
    for server in serversInfo['servers']:
        emmisionsOfServer = calculateEmmisionsOfServer(server)
        emmisionsOfServer = emmisionsOfServer.round(2)
        print(emmisionsOfServer)
        csvPath = path.join(Config.DATAPATH, 'output', server['name'] + '.csv')
        emmisionsOfServer.to_csv(csvPath, sep=';')
