from pandas import DataFrame
from . import scope1, scope2, scope3
from ..config import Config

def calculateMultitenancyShare(serverInfo : dict, monthlyPowerConsumption : float) -> float:
    return (monthlyPowerConsumption * Config.CARBONINTENSITY) / serverInfo['DCEmissions']['scope2']

def calculate(serverDf : DataFrame, serverInfo : dict) -> DataFrame:
    # scopes energy
    # calculate scope 2 energy usage
    result = scope2.calculate(serverDf, serverInfo)
    monthlyPowerConsumption = result['scope2E'].mean() * 24*365/12

    #calculate scope 2 and scope 3 emissions
    multitenancyShare = calculateMultitenancyShare(serverInfo, monthlyPowerConsumption)
    result['scope1'] = scope1.calculate(serverInfo, multitenancyShare)
    result['scope2'] = result['scope2E'] * Config.CARBONINTENSITY
    result['scope3'] = scope3.calculate(serverInfo, multitenancyShare)
    result['TCFP'] = result['scope1'] + result['scope2'] + result['scope3']

    return result
