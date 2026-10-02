import numpy as np
import matplotlib.pyplot as plt
import os
from sys import  argv, exit
from iminuit import Minuit
from iminuit.cost import ExtendedBinnedNLL
from scipy.stats import norm


def usage():
    print("Usage: python time_plot.py <input_path> [output_path] [p_start] [p_end]")
    print("  <input_path>: Directory containing energy subdirectories")
    print("  [output_path]: Output image file (default: time_res.jpeg)")
    print("  [p_start]: Start percentage (default: 10)")
    print("  [p_end]: End percentage (default: 90)")
    exit(1)

input_path = argv[1] if len(argv) > 1 else "data_analysis/time_resolution/slanted_e"
output_path = argv[2] if len(argv) > 2 else input_path
p_start = float(argv[3]) if len(argv) > 3 else 10
p_end = float(argv[4]) if len(argv) > 4 else 90
n_bins = 40

def model_cdf(x, mu, sigma, N):
    """
    Cumulative distribution function (CDF) for a normal distribution.

    Parameters
    ----------
    x : array-like
        Input values.
    mu : float
        Mean of the normal distribution.
    sigma : float
        Standard deviation of the normal distribution.
    N : float
        Normalization factor.

    Returns
    -------
    array-like
        CDF values scaled by N.
    """
    return N * norm.cdf(x, mu, sigma)


def remove_tail(en):
    
    count, edges = np.histogram(en, bins=n_bins)
    m_count = list(count).index( max(count))
    en = np.where(np.abs(en - (edges[m_count] + edges[m_count +1])/2) / np.std(en) < 2, en, 0)
    en = en[en.nonzero()]
    return en


def gauss_fit(data, percentage_index, bins=n_bins, iteration=0, failed=False, removetail=False, initial_data=None, energy_label=""):
    """
    Fit a Gaussian to the histogram of energy values.

    Parameters
    ----------
    data : np.array
        Array of energy values to fit.
    percentage_index : int
        Index of the percentage selection.
    bins : int
        Number of histogram bins.
    iteration : int
        Iteration count for recursive fitting.
    failed : bool
        Flag for failed fit attempts.
    removetail : bool
        Flag to remove histogram tail.
    initial_data : np.array
        Original data for fallback.
    energy_label : str
        Label for saving plots.

    Returns
    -------
    fit_mean : float
        Fitted mean value.
    fit_std : float
        Fitted standard deviation.
    fit_N : float
        Fitted normalization factor.
    fit_cov : dict
        Covariance matrix of the fit parameters.
    """
    iteration += 1
    mean = np.mean(data)
    std = np.std(data)
    count, edges = np.histogram(data, bins=bins)
    cost = ExtendedBinnedNLL(count, edges, model_cdf)
    n = Minuit(cost, mu=mean, sigma=std, N=len(data))
    n.migrad(ncall=1000)

    # Plot fit (commented out by default)
    plt.hist(data, bins=bins, histtype="step")
    plt.plot(
        np.linspace(min(data), max(data), len(edges) - 1),
        (n.values[2] * norm.pdf(
            np.linspace(min(data), max(data), len(edges) - 1),
            loc=n.values[0], scale=n.values[1]
        )) * np.diff(edges)
    )
    plt.savefig("data_analysis/time_resolution/hist_fit/" + energy_label)
    # plt.show()
    plt.clf()
    plt.close()
    if n.valid:
        if n.fval / n.ndof > 4:
            if not removetail:
                return gauss_fit(remove_tail(data), percentage_index, bins, iteration, removetail=True, initial_data=initial_data, energy_label=energy_label)
            else:
                if not failed:
                    if bins < 8:
                        return gauss_fit(initial_data, percentage_index, failed=True, initial_data=initial_data, energy_label=energy_label)
                    return gauss_fit(data, percentage_index, bins - 2, initial_data=initial_data, energy_label=energy_label)
        plt.clf()
        plt.close()
        return n.values[0], n.values[1], n.values[2], n.covariance
    else:
        plt.clf()
        plt.close()
        if not failed:
            if bins < 8:
                return gauss_fit(initial_data, percentage_index, failed=True, initial_data=initial_data, energy_label=energy_label)
            return gauss_fit(data, percentage_index, bins - 2, initial_data=initial_data, energy_label=energy_label)



if __name__ == "__main__":
    # Get list of energy directories
    energy_dirs = os.listdir(input_path)
    energy_dirs = [e for e in energy_dirs if os.path.isdir(os.path.join(input_path, e))]
    energy_values = np.array([int(file.split(".")[0].removeprefix("resolution_")) for file in energy_dirs])

    mean_risetimes = []
    std_risetimes = []

    for energy_dir in energy_dirs:
        dir_path = os.path.join(input_path, energy_dir)
        files = os.listdir(dir_path)
        # Remove PNG files from list
        files = [f for f in files if not f.endswith(".png")]
        all_risetimes = []

        for file_name in files:
            file_path = os.path.join(dir_path, file_name)
            data = np.genfromtxt(file_path, delimiter=',', dtype=float)
            start_indices = int(p_start / 10) - 1
            end_indices = int(p_end / 10) - 1
            peak_index = 9

            l_start = [event[start_indices] for event in data]
            l_end = [event[end_indices] for event in data]
            l_peak = [event[peak_index] for event in data]

            risetime = np.array(l_start)
            all_risetimes.extend(risetime)

        plt.title(energy_dir)
        counts, bins = np.histogram(all_risetimes, bins=100)
        mean, std, filtered_risetimes = calc_momenta(all_risetimes, counts, bins)
        fit_mean, fit_std, fit_N, fit_cov = gauss_fit(mean, std, filtered_risetimes, energy_dir)
        mean_risetimes.append(fit_mean)
        std_risetimes.append(fit_std)

    plt.errorbar(energy_values, std_risetimes, fit_cov[1][1], fmt="o")
    plt.savefig(os.path.join(output_path, "time_res.jpeg"))
    # plt.show()