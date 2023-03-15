from pandas import DataFrame
from . import scope2

def calculateEnergy(hourlyDf : DataFrame, coolingDf : DataFrame, miscDf : DataFrame, cuserDf : DataFrame) -> DataFrame:
    # scopes energy
    # energyDf.set_index('date')
    scope2E = scope2.calculate(hourlyDf, coolingDf, miscDf)
    # use it as base
    energyDf = scope2E
    energyDf.loc[:,'scope1'] = 0
    print(energyDf)

    #TODO do the real scope 3 here
    energyDf.loc[:,'scope3'] = 0

    energyDf['total'] = energyDf['scope1'] + energyDf['scope2'] + energyDf['scope3']
    print(ener)

    return energyDf

def calculate(hourlyDf : DataFrame, coolingDf : DataFrame, miscDf : DataFrame, cuserDf : DataFrame):

    energyDf = calculateEnergy(hourlyDf, coolingDf, miscDf, cuserDf)
