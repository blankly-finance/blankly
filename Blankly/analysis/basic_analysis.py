from statistics import mean


def average(data) -> float:
    """
    Find average of dataset
    Args:
        data: (list) A list containing the values to determine the mean
    Returns:
        float: This is the mean of the dataset
    """
    return mean(data)


def back_average(prices, distance):
    if distance > len(prices):
        distance = len(prices)
    return mean(prices[-distance:])
