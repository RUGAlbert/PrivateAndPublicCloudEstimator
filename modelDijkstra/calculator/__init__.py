"""
All the calculations to estimate the emissions
"""

from pandas import DataFrame
from . import scope1, scope2, scope3

def calculateMultitenancyShare(serverInfo : dict, monthlyPowerConsumption : float, avgCarbonIntensity : float) -> float:
    """Calculates the multitenancy share for the tenant

    Args:
        serverInfo (dict): The dictonary with all the serverinfo
        monthlyPowerConsumption (float): the monthly consumption in wh of the server
        avgCarbonIntensity (float): the average carbon intensity of the month

    Returns:
        float: the multenancy share, a value between 0 and 1
    """
    return (monthlyPowerConsumption * avgCarbonIntensity) / serverInfo['DCEmissions']['scope2']

def calculateEmmisionsOfServer(datapath: str, serverInfo : dict) -> DataFrame:
    """Calculates the emissions of the server.

    Args:
        datapath (str) : the path to the data files
        serverInfo (dict): The dictonary with all the serverinfo

    Returns:
        DataFrame: returns the hourly emissions in a dataframe
    """
    # scopes energy
    # calculate scope 2 energy usage
    result = scope2.calculate(datapath, serverInfo)
    monthlyPowerConsumption = result['scope2E'].mean() * 24*365/12
    avgCarbonIntensity = result['ci'].mean()

    #calculate scope 2 and scope 3 emissions
    multitenancyShare = calculateMultitenancyShare(serverInfo, monthlyPowerConsumption, avgCarbonIntensity)

    result['scope1'] = scope1.calculate(serverInfo, multitenancyShare)
    result['scope3'] = scope3.calculate(serverInfo, multitenancyShare)
    #the following line can be used if no scope 3 emissions are known
    # result['scope3'] = Config.LSHARE * avgCarbonIntensity * result['scope2E'].mean() / 0.19 * 0.81
    result['TCFPLower'] = result['scope1'] + result['scope2Lower'] + result['scope3']
    result['TCFPUpper'] = result['scope1'] + result['scope2Upper'] + result['scope3']

    result = result[['scope2E','eServerStatic', 'eServerDynamic', 'eNetworkStatic',
                     'eNetworkDynamic', 'eCoolingStatic', 'eCoolingDynamic', 'scope1',
                     'scope2Lower', 'scope2Upper', 'scope3', 'TCFPLower', 'TCFPUpper', 'ci']]
    result.sort_index(inplace=True)
    #remove first and last since it could be that these are not full hours
    result.drop(result.tail(1).index,inplace=True)
    result.drop(result.head(1).index,inplace=True)

    return result
