'''
This is the start place of the calculation
'''

import pandas as pd
from pandas import DataFrame
from os import path

from .calculator import calculate

def start(hourlyDf : DataFrame, coolingDf : DataFrame, miscDf : DataFrame, cuserDf : DataFrame):

    calculate(hourlyDf, coolingDf, miscDf, cuserDf)
