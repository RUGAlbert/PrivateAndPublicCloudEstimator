from os import path

import pandas as pd

from .config import Config


def start(serversInfo : dict):
    print(serversInfo)
    serverInfo = serversInfo['servers'][1]
    dataDumpDf = pd.read_csv(path.join(Config.DATAPATH, serverInfo['powerServerFile']), sep=',', skiprows=1)
    dataDumpDf['isServer'] = dataDumpDf['Name'].str.contains("hxn")

    dataDumpDf['totalEnergy'] = dataDumpDf['Power|Total Energy (Wh)']
    # dataDumpDf['tenantEnergy'] = dataDumpDf['Power|Tenant Energy (Wh)']
    dataDumpDf['time'] = pd.to_datetime(dataDumpDf['Interval Breakdown'])
    dataDumpDf = dataDumpDf[['time', 'totalEnergy', 'isServer']]
    dataDumpDf['tenantEnergy'] = dataDumpDf['totalEnergy'] / 5
    dataDumpDf['serverTenantEnergy'] = dataDumpDf['tenantEnergy']
    dataDumpDf['storageTenantEnergy'] = dataDumpDf['tenantEnergy']
    dataDumpDf.loc[dataDumpDf['isServer'] == False, 'serverTenantEnergy'] = 0
    dataDumpDf.loc[dataDumpDf['isServer'] == True, 'storageTenantEnergy'] = 0
    print(dataDumpDf)

    result = dataDumpDf.groupby(['time']).aggregate({'serverTenantEnergy':'sum','storageTenantEnergy':'sum'})
    result = result.round(2)
    print(result)

    csvPath = path.join(Config.DATAPATH, 'output', serverInfo['name'] + '.csv')
    result.to_csv(csvPath, sep=';')
