import pandas as pd
from os import path
from Dijkstra1WBA import start


dataPath = path.join('data', 'weekData')
rawServerDf = pd.read_csv(path.join(dataPath, 'Power_HostUtilStat-EPODQLON02-CIMC-20230403-144031.csv'), sep=',', skiprows=1)
# networkDf = pd.read_csv(path.join(dataPath, 'network_ccc123_trimmed.csv'), sep=',')
# datacenterDf = pd.read_csv(path.join(dataPath, 'datacenter_ccc123_trimmed.csv'), sep=';')
# cuserDf = pd.read_csv(path.join(dataPath, 'cuserData.csv'), sep=';')

#prune columns
rawServerDf = rawServerDf[['Time','Platform-Curr', 'CPU-Curr', 'Mem-Curr']]

#conversion from watts to kwh
rawServerDf['Duration'] = -pd.to_datetime(rawServerDf['Time'], errors='coerce').diff(-1).dt.total_seconds()
rawServerDf.drop(rawServerDf.tail(1).index,inplace=True)
rawServerDf['DurationInHours'] = rawServerDf['Duration'] / 3600
rawServerDf['serverEnergy'] = rawServerDf['DurationInHours'] * rawServerDf['Platform-Curr']

#group by hour
serverDataDf = rawServerDf[['Time', 'serverEnergy']]
serverDataDf["Time"] = pd.to_datetime(serverDataDf["Time"])
serverDataDf = serverDataDf.resample('60min', on='Time').sum()
print(serverDataDf)

#first filter the data

# serverDf = serverDf[serverDf['customer_id'] == 604]
# networkDf = networkDf[networkDf['customer_id'] == 604]

# print(serverDf)
# print(networkDf)
# print(datacenterDf)

# start(serverDf, networkDf, datacenterDf, None)
