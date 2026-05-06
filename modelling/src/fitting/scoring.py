from fitting.utils import D


def mse(observed, simulated):
    """
    Calculate the mean squared error (MSE) between observed and simulated data

    MSE = (1 / N) * Σ (observed - simulated)²

    :param observed: Dictionary of observed data points
    :param simulated: Dictionary of simulated data points
    :return: MSE
    """
    # Get a list of months that appear in both the observed and simulated data
    months = sorted(set(observed) & set(simulated))
    if not months:
        raise ValueError("No overlapping months between observed and simulated data")

    # For each month, the error is calculated as the squared difference between observed
    # and simulated data. This is summed to give the mismatch across the year and then
    # divided by the number of months to give a monthly average mismatch
    return sum((observed[m] - simulated[m]) ** 2 for m in months) / D(len(months))
