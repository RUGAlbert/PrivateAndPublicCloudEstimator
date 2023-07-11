"""Everything to do with calcuting the score and the regression line
"""


from typing import Tuple
from sklearn.linear_model import LinearRegression
import numpy as np
from pandas import DataFrame

from .config import Config


def calculateUPESAScore(regressor : LinearRegression, xStart : float, xEnd : float) -> float:
    """Calculates the score of the regression based on the
     relation between total carbon footprint and maxusers

    Args:
        regressor (LinearRegression): the regressor which estimats the line
        for the relationship between the total carbon footprint per user and the maxusers

    Returns:
        float: the score
    """
    predictedY = regressor.predict(np.arange(xStart, xEnd).reshape(-1,1))

    YPred = 1/ (np.power(predictedY, 1/Config.POWERFUNCTIONFORREGRESSION))

    score = np.sum(YPred) / (xEnd-xStart)
    print("Area score", score[0])
    return score


def calculatePercentile(regressor : LinearRegression, X : DataFrame, percentile : float) -> float:
    """Calculates the percentile of the regression

    Args:
        regressor (LinearRegression): The function describing the regression
        X (DataFrame): the values of which the split is determined
        percentile (float): at which point the split has to be done (i.e. 5th percentile)

    Returns:
        float: return the value at that percentile
    """
    xVal = X[int(len(X)/100*percentile)]
    yVal = 1/ (np.power(regressor.predict((xVal,)), 1/Config.POWERFUNCTIONFORREGRESSION))
    return yVal

def doLinearRegression(resultDf : DataFrame) -> Tuple[DataFrame, DataFrame]:
    """Make the linear regression between the totalcarbon footprint per user and the maxusers

    Args:
        resultDf (DataFrame): the df which also has the columns tcf per user and maxusers per hour

    Returns:
        Tuple[DataFrame, DataFrame]: returns the x and y data for the prediction
    """

    XY = np.column_stack((resultDf['maxUsers'], resultDf['scope2EPerUser']))
    XY = XY[np.argsort(XY[:, 0])]

    X = XY[:,0].reshape(-1,1)
    Y = XY[:,1].reshape(-1,1)

    #Get best powerfunction

    bestScore = 0

    for pwr in np.arange(Config.PWRFUNCREGMIN, Config.PWRFUNCREGMAX, 0.05):
        regressor = LinearRegression()
        regressor.fit(X, 1/ (np.power(Y, pwr)))
        curScore = regressor.score(X, 1/ (np.power(Y, pwr)))
        if curScore > bestScore:
            bestScore = curScore
            Config.POWERFUNCTIONFORREGRESSION = pwr

    regressor = LinearRegression()
    regressor.fit(X, 1/ (np.power(Y, Config.POWERFUNCTIONFORREGRESSION)))
    # regressor.fit(X, Y)  # perform linear regression
    print("mSQR of ", bestScore, "for a n-value of ", Config.POWERFUNCTIONFORREGRESSION)
    predictedY = regressor.predict(X)
    # print("Coefficient", regressor.coef_)
    YPred = 1/ (np.power(predictedY, 1/Config.POWERFUNCTIONFORREGRESSION))
    calculateUPESAScore(regressor, min(X), max(X))
    print("95 percent is less than", calculatePercentile(regressor, X, 5)[0][0])
    print("50 percent is less than", calculatePercentile(regressor, X, 50)[0][0])
    print("5 percent is less than", calculatePercentile(regressor, X, 95)[0][0])
    return X, YPred
