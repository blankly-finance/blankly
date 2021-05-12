from statistics import mean


def moving_average(data, depth) -> float:
    """
    Find the unweighted average n (distance) points back in the dataset:
    Args:
        data: (list) A list containing the values to find the mean from
        depth: (int) A number containing the distance the algorithm should go back to find the average.
         If this is larger than the size of the dataset, it will default to the dataset length.
    """
    if depth > len(data):
        depth = len(data)
    return mean(data[-depth:])


def exponential_average():
    pass


def moving_average_set(data, depth) -> list:
    """
    Finding the moving average of a dataset. Note that this removes the depth-1 points from the beginning of the set.
    Args:
        data: (list) A list containing the data you want to find the moving average of
        depth: (int) How far each average set should be
    """
    set_length = len(data)
    # Simply return the mean immediately if the user requests a large depth or has a small set
    if depth >= set_length:
        return [mean(data)]

    needed_lists = set_length - depth
    # Final list of moving average
    ma_list = []
    while needed_lists >= 0:
        # Use needed lists as index
        ma_list.insert(0, mean(data[needed_lists: needed_lists + depth]))
        needed_lists -= 1

    difference = len(data) - len(ma_list)
    while difference > 0:
        ma_list.insert(0, data[difference-1])
        difference = len(data) - len(ma_list)
    return ma_list


