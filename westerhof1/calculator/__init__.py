from pandas import DataFrame
from . import scope2
from ..config import Config

def calculateMultitenancyShare():
    return 0.1

def calculateEnergy(serverDf : DataFrame, networkDf : DataFrame, datacenterDf : DataFrame) -> DataFrame:
    # scopes energy
    # energyDf.set_index('date')
    multitenancyShare = calculateMultitenancyShare()
    scope2E = scope2.calculate(serverDf, networkDf, datacenterDf, multitenancyShare)
    # use it as base
    energyDf = scope2E
    energyDf.loc[:,'scope1'] = 0


    #TODO do the real scope 3 here
    energyDC = 1000
    r = multitenancyShare * Config.LSHARE
    energyDf.loc[:,'scope3'] = energyDC * r

    energyDf['total'] = energyDf['scope1'] + energyDf['scope2'] + energyDf['scope3']

    return energyDf

def calculateCarbonIntensity(energyDf : DataFrame):
    carbonDf = energyDf[['date']].copy()
    carbonDf['emmisions'] = energyDf['total'] * Config.CARBONINTENSITY
    return carbonDf

def calculate(serverDf : DataFrame, networkDf : DataFrame, datacenterDf : DataFrame, cuserDf : DataFrame):

    energyDf = calculateEnergy(serverDf, networkDf, datacenterDf)
    carbonDf = calculateCarbonIntensity(energyDf)
    print(energyDf)
    print(carbonDf)
    return carbonDf