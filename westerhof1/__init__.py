'''
This is the start place of the calculation
'''

import pandas as pd
from pandas import DataFrame
from os import path

from .calculator import calculate

def start(serverDf : DataFrame, networkDf : DataFrame, datacenterDf : DataFrame, cuserDf : DataFrame):

    calculate(serverDf, networkDf, datacenterDf, cuserDf)
