"""
Calculates scope 1 emissions
"""


def calculate(serverInfo : dict, multitenancyShare : float) -> float:
    """Calculates the scope 1 emissions

    Args:
        serverInfo (dict): dictionary with the information of the server
        multitenancyShare (float): the multitenancy share expressed as a percentage. With a number
            between 0 and 1

    Returns:
        float: the amount of emissions for this server
    """
    return serverInfo["DCEmissions"]["scope1"] * multitenancyShare
