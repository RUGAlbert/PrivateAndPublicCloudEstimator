import json
import sys
from os import path

import modelDijkstra

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Please include the datapath")
    datapath = sys.argv[1]
    with open(path.join(datapath, 'serverInfo.json'), encoding='utf-8') as f:
        data = json.load(f)

    modelDijkstra.start(datapath, data)
