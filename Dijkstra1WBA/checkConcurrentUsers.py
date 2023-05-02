import matplotlib.pyplot as plt
from pandas import DataFrame


def plotConccurentUsers(concurrentUserDf : DataFrame):
    print(concurrentUserDf)
    print(concurrentUserDf.columns)
    concurrentUserDf.plot(use_index=True, y='maxUsers')
    plt.show()
