import logging
from pandas import DataFrame
from . import scope1, scope2, scope3
from ..config import Config

def calculateMultitenancyShare(serverInfo : dict, monthlyPowerConsumption : float, avgCarbonIntensity : float) -> float:
    return (monthlyPowerConsumption * avgCarbonIntensity) / serverInfo['DCEmissions']['scope2']

def calculateEmmisionsOfServer(serverInfo : dict) -> DataFrame:
    # scopes energy
    # calculate scope 2 energy usage
    result = scope2.calculate(serverInfo)
    monthlyPowerConsumption = result['scope2E'].mean() * 24*365/12
    avgCarbonIntensity = result['ci'].mean()

    #calculate scope 2 and scope 3 emissions
    multitenancyShare = calculateMultitenancyShare(serverInfo, monthlyPowerConsumption, avgCarbonIntensity)
    
    result['scope1'] = scope1.calculate(serverInfo, multitenancyShare)
    result['scope3'] = scope3.calculate(serverInfo, multitenancyShare)
    result['TCFPLower'] = result['scope1'] + result['scope2Lower'] + result['scope3']
    result['TCFPUpper'] = result['scope1'] + result['scope2Upper'] + result['scope3']
    
    result = result[['eNetwork', 'eNetworkTotal', 'eServerStatic', 'eServerDynamic', 'eNetworkStatic', 'eNetworkDynamic', 'eCoolingStatic', 'eCoolingDynamic', 'scope1', 'scope2Lower', 'scope2Upper', 'scope3', 'TCFPLower', 'TCFPUpper', 'ci']]
    result.sort_index(inplace=True)
    return result
