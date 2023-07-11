import json
from os import path

import pandas as pd

import modelDijkstra
from modelDijkstra.eServerStaticCalculator import calculateParametersOfServer
from modelDijkstra.config import Config
from extra import createPlots

# createPlots.start()
# exit()

with open(path.join('data', 'cisco', 'serverInfo.json'), encoding='utf-8') as f:
    ciscoData = json.load(f)

with open(path.join('data', 'monthData', 'serverInfo.json'), encoding='utf-8') as f:
    monthData = json.load(f)

with open(path.join(Config.DATAPATH, 'serverInfo.json'), encoding='utf-8') as f:
    data = json.load(f)

modelDijkstra.start(data)
