from os import path


class Config():
    LSHARE = 1
    CARBONINTENSITY = 1.4
    WHPERBYTE = 6e-8

    DATAPATH = path.join('data', 'monthData')

    ZETA_LOWER = 1
    GAMMA_LOWER = 0

    ZETA_UPPER = 1
    GAMA_UPPER = 0.5

    MU = 0.81

    SERVERSTATICWATTS = 217
