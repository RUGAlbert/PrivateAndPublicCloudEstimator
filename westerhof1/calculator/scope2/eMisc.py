from pandas import DataFrame

def calculate(miscDf : DataFrame, multitenancyShare : float):
    print(miscDf)
    totalDirect = miscDf[miscDf['DeviceName'] == 'Misca']['DevicePower'].sum()
    totalIndirect = miscDf[miscDf['DeviceName'] != 'Misca']['DevicePower'].sum()
    return totalIndirect * multitenancyShare + totalDirect
