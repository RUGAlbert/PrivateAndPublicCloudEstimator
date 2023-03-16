from pandas import DataFrame

def calculate(hourlyDf : DataFrame):
    wHPerByte = 6e-8
    return wHPerByte * (hourlyDf['bytes sent'] + hourlyDf['bytes received'])
