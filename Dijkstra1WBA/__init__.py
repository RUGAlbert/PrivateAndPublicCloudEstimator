'''
This is the start place of the calculation
'''

import pandas as pd
from pandas import DataFrame
from os import path

from .calculator import calculate


def calculateEmmisionsOfServer(serverInfo : dict):
    dataPath = path.join('data', 'weekData')
    serverEnergyDf = pd.read_csv(path.join(dataPath, serverInfo['powerServerFile']), sep=',', skiprows=1)
    calculate(serverEnergyDf, serverInfo)

def start(serversInfo : dict):
    for server in serversInfo['servers']:
        calculateEmmisionsOfServer(server)
