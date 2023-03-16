from pandas import DataFrame
from . import scope2
from ..config import Config

def calculateMultitenancyShare():
    return 0.1

def calculateEnergy(hourlyDf : DataFrame, coolingDf : DataFrame, miscDf : DataFrame, cuserDf : DataFrame) -> DataFrame:
    # scopes energy
    # energyDf.set_index('date')
    multitenancyShare = calculateMultitenancyShare()
    scope2E = scope2.calculate(hourlyDf, coolingDf, miscDf, multitenancyShare)
    # use it as base
    energyDf = scope2E
    energyDf.loc[:,'scope1'] = 0


    #TODO do the real scope 3 here
    energyDC = 1000
    r = multitenancyShare * Config.LShare
    energyDf.loc[:,'scope3'] = energyDC * r

    energyDf['total'] = energyDf['scope1'] + energyDf['scope2'] + energyDf['scope3']
    print(energyDf)

    return energyDf

def calculate(hourlyDf : DataFrame, coolingDf : DataFrame, miscDf : DataFrame, cuserDf : DataFrame):

    energyDf = calculateEnergy(hourlyDf, coolingDf, miscDf, cuserDf)
