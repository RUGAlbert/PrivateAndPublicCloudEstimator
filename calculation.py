import pandas as pd
from os import path
from westerhof1 import start


dataPath = path.join('data', 'testData')
hourlyDf = pd.read_csv(path.join(dataPath, 'hourlyData.csv'), sep=';')
coolingDf = pd.read_csv(path.join(dataPath, 'coolingData.csv'), sep=';')
miscDf = pd.read_csv(path.join(dataPath, 'miscData.csv'), sep=';')
cuserDf = pd.read_csv(path.join(dataPath, 'cuserData.csv'), sep=';')

start(hourlyDf, coolingDf, miscDf, cuserDf)
