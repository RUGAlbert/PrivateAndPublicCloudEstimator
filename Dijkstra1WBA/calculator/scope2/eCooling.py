from pandas import DataFrame

def calculate(coolingDf : DataFrame, multitenancyShare : float):
    total = coolingDf['DevicePower'].sum()
    return total * multitenancyShare
