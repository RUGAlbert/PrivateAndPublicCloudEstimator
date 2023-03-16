
from pandas import DataFrame
from . import eServer, eNetwork, eCooling, eMisc


def calculate(hourlyDf : DataFrame, coolingDf : DataFrame, miscDf : DataFrame, multitenancyShare : float) -> DataFrame:
    
    result = hourlyDf[['date']].copy()
    result['eServer'] = eServer.calculate(hourlyDf)
    result['eNetwork'] = eNetwork.calculate(hourlyDf)
    result['eCooling'] = eCooling.calculate(coolingDf, multitenancyShare)
    result['eMisc'] = eMisc.calculate(miscDf, multitenancyShare)

    result['scope2'] = result['eServer'] + result['eNetwork'] + result['eCooling'] + result['eMisc']
    
    return result
