"""
This calculates the server energy
"""


from numpy import NaN
from pandas import DataFrame


def calculate(hourlyDf : DataFrame):
    
    # https://stackoverflow.com/questions/54754880/linear-regression-over-two-variables-in-a-pandas-dataframe
    # Do this later

    # Coefficients
    idlePower = 1.650e5
    cpuUtil = 1.187e4
    cacheDataMoved = 0
    dramAccessed = 1.828e-4
    diskDataMoved = 1.365e-6

    eServer = (idlePower + cpuUtil * hourlyDf['amount_CPU_CLK_UNHALTED'] + 
        cacheDataMoved * (hourlyDf['amount_INSTRUCTION_CACHE_FETCHES'] +hourlyDf['amount_DATA_CACHE_FETCHES']) +
        dramAccessed * hourlyDf['amount_DRAM_ACCESSES'] +
        diskDataMoved * (hourlyDf['disk_bytes_read'] + hourlyDf['disk_bytes_written'])
    )

    return eServer
