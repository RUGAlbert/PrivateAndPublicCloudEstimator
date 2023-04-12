"""
Calculates scope 3 emissions
"""

from ..config import Config


def calculate(serverInfo : dict, multitenancyShare : float) -> float:
    """Calculates the scope 3 emissions

    Args:
        serverInfo (dict): dictionary with the information of the server
        multitenancyShare (float): the multitenancy share expressed as a percentage. With a number
            between 0 and 1

    Returns:
        float: the amount of emissions for this server
    """
    return serverInfo["DCEmissions"]["scope3"] * multitenancyShare * Config.LSHARE
