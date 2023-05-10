import json
from os import path

import pandas as pd

import Dijkstra1WBA, Dijkstra2Cisco
from Dijkstra1WBA.eServerStaticCalculator import calculateParametersOfServer

with open(path.join('data', 'cisco', 'serverInfo.json'), encoding='utf-8') as f:
    data = json.load(f)

# print(data)
# Dijkstra1WBA.start(data)
Dijkstra2Cisco.start(data)
# calculateParametersOfServer(data['servers'][0])

# dataPath = path.join('data', 'weekData')
# serverEnergyDf = pd.read_csv(path.join(dataPath, 'Power_HostUtilStat-EPODQLON02-CIMC-20230403-144031.csv'), sep=',', skiprows=1)
# networkDf = pd.read_csv(path.join(dataPath, 'network_ccc123_trimmed.csv'), sep=',')
# datacenterDf = pd.read_csv(path.join(dataPath, 'datacenter_ccc123_trimmed.csv'), sep=';')
# cuserDf = pd.read_csv(path.join(dataPath, 'cuserData.csv'), sep=';')

# print(serverEnergyDf)

# #first filter the data

# serverDf = serverDf[serverDf['customer_id'] == 604]
# networkDf = networkDf[networkDf['customer_id'] == 604]

# print(serverDf)
# print(networkDf)
# print(datacenterDf)

# start(serverDf, networkDf, datacenterDf, None)
# start(serverEnergyDf)
