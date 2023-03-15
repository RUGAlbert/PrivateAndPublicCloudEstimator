
from pandas import DataFrame
from . import eServer


def calculate(hourlyDf : DataFrame, coolingDf : DataFrame, miscData : DataFrame) -> DataFrame:
    
    result = hourlyDf[['date']].copy()
    result['eServer'] = eServer.calculate(hourlyDf)
    result['eNetwork'] = 0
    result['eCooling'] = 0
    result['eMisc'] = 0

    result['scope2'] = result['eServer'] + result['eNetwork'] + result['eCooling'] + result['eMisc']
    
    return result
