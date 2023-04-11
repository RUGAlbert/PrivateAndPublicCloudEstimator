"""
This calculates the server energy
"""


from numpy import NaN
from pandas import DataFrame
from sklearn import linear_model

def calculateCoefficients(hourlyDf: DataFrame):
    regr = linear_model.LinearRegression()
    regr.fit(hourlyDf[['amount_CPU_CLK_UNHALTED', 'cache_data_moved', 'amount_DRAM_ACCESSES', 'disk_data_moved']], hourlyDf['power_consumed'])
    print(regr.intercept_)
    print(regr.coef_)


def calculate(hourlyDf : DataFrame):


    #prepare dataframe
    hourlyDf['cache_data_moved'] = hourlyDf['amount_INSTRUCTION_CACHE_FETCHES'] +hourlyDf['amount_DATA_CACHE_FETCHES']
    hourlyDf['disk_data_moved'] = hourlyDf['disk_bytes_read'] + hourlyDf['disk_bytes_written']

    calculateCoefficients(hourlyDf)
    
    # https://stackoverflow.com/questions/54754880/linear-regression-over-two-variables-in-a-pandas-dataframe
    # Do this later

    # Coefficients
    idlePower = 1.650e5
    cpuUtil = 1.187e4
    cacheDataMoved = 0
    dramAccessed = 1.828e-4
    diskDataMoved = 1.365e-6
    

    eServer = (idlePower + cpuUtil * hourlyDf['amount_CPU_CLK_UNHALTED'] + 
        cacheDataMoved * hourlyDf['cache_data_moved'] +
        dramAccessed * hourlyDf['amount_DRAM_ACCESSES'] +
        diskDataMoved * hourlyDf['disk_data_moved']
    )

    return eServer
