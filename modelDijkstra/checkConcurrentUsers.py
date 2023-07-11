import matplotlib.pyplot as plt
from pandas import DataFrame
import logging


def plotConccurentUsers(concurrentUserDf : DataFrame):
    print(concurrentUserDf)
    print(concurrentUserDf.columns)
    concurrentUserDf.plot(use_index=True, y='maxUsers', ylabel="max concurrent users per hour", legend=False)
    plt.show()
