from os import path

import pandas as pd

from .config import Config

def calculateForServer(serverInfo : dict) :
    print(serverInfo['name'])
    dataDumpDf = pd.read_csv(path.join(Config.DATAPATH, serverInfo['powerServerFile']), sep=',', skiprows=1)
    # dataDumpDf['isServer'] = dataDumpDf['Name'].str.contains("hxn")

    dataDumpDf['totalEnergy'] = dataDumpDf['Power|Total Energy (Wh)']
    # dataDumpDf['tenantEnergy'] = dataDumpDf['Power|Tenant Energy (Wh)']
    dataDumpDf['time'] = pd.to_datetime(dataDumpDf['Interval Breakdown'])
    dataDumpDf = dataDumpDf[['time', 'totalEnergy']]
    dataDumpDf['tenantEnergy'] = dataDumpDf['totalEnergy'] / 5
    # dataDumpDf['serverTenantEnergy'] = dataDumpDf['tenantEnergy']
    # dataDumpDf['storageTenantEnergy'] = dataDumpDf['tenantEnergy']
    # dataDumpDf.loc[dataDumpDf['isServer'] == False, 'serverTenantEnergy'] = 0
    # dataDumpDf.loc[dataDumpDf['isServer'] == True, 'storageTenantEnergy'] = 0
    print(dataDumpDf)

    result = dataDumpDf.groupby(['time']).aggregate({'tenantEnergy':'sum'})
    result['eServer'] = result['tenantEnergy']
    mu = 1 - (1 - Config.MU) * serverInfo['networkUsageAvg'] / serverInfo['networkUsageMax']
    print(mu)
    dynamicENetwork = (1- mu) * Config.WHPERBYTE * serverInfo['networkUsageAvg'] * 60 * 60
    staticENetwork = serverInfo['networkUsageMax'] * Config.WHPERBYTE * Config.MU * 60 * 60
    result['eNetwork'] = staticENetwork + dynamicENetwork
    # result['eNetwork'] = Config.WHPERBYTE * serverInfo['networkUsageAvg'] * 60 * 60
    result['eCooling'] = (serverInfo['PUE'] - 1) * (result['eServer'] + result['eNetwork'])

    result['scope2E'] = result['eServer'] + result['eNetwork'] + result['eCooling']
    result = result.round(2)
    print(result)

    csvPath = path.join(Config.DATAPATH, 'output', serverInfo['name'] + '.csv')
    result.to_csv(csvPath, sep=';')

def start(serversInfo : dict):
    for server in serversInfo['servers']:
        calculateForServer(server)
