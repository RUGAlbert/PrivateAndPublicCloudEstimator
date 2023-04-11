
from pandas import DataFrame
from . import eServer, eNetwork, eCooling, eMisc


def calculate(serverDf : DataFrame, networkDf : DataFrame, datacenterDf : DataFrame, multitenancyShare : float) -> DataFrame:
    
    result = serverDf[['date']].copy()
    result['eServer'] = eServer.calculate(hourlyDf)
    result['eNetwork'] = eNetwork.calculate(hourlyDf)
    result['eCooling'] = eCooling.calculate(coolingDf, multitenancyShare)
    result['eMisc'] = eMisc.calculate(miscDf, multitenancyShare)

    result['scope2'] = result['eServer'] + result['eNetwork'] + result['eCooling'] + result['eMisc']
    
    return result
