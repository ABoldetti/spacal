import uproot  # For reading ROOT files
import ROOT    # For writing ROOT files
import numpy as np  # For numerical operations
import matplotlib.pyplot as plt  # For plotting
from iminuit import Minuit  # For minimization/fitting
from iminuit.cost import ExtendedBinnedNLL, LeastSquares  # Cost functions for fitting
from scipy.stats import norm, chi2  # Statistical distributions
import os  # For file and directory operations
from sys import argv  # For command-line arguments

from error_propagation import propagazione_errore  # Custom error propagation function
import array  # For array operations (used in ROOT trees)

# Set input and output paths for data
input_path = argv[1] if len(argv) > 1 else "data_analysis/readout/slanted_e"
output_path = input_path.replace("readout", "energy_res")
root_path = input_path.replace("readout", "root_resolution")
n_bins = 80  # Number of bins for histograms
coeff = 1

# Cumulative distribution function for a normal distribution
def cdf(x, mu, sigma, N):
    """
    Returns the cumulative distribution function for a normal distribution.
    Parameters:
        x: Value(s) at which to evaluate the CDF
        mu: Mean of the distribution
        sigma: Standard deviation of the distribution
        N: Normalization factor
    Returns:
        CDF value(s)
    """
    return N * norm.cdf(x, mu, sigma)

# Linear function for fitting
def line(x, q, m):
    """
    Linear function for fitting.
    Parameters:
        x: Independent variable
        q: Intercept
        m: Slope
    Returns:
        Linear function value(s)
    """
    return m * x + q

# Reads ROOT file and extracts reconstructed energy array
def Readout_convertion(path: str):
    """
    Reads ROOT file and extracts 'mod_reco_energy' for each cell from the tree.
    Parameters:
        path: Path to the ROOT file
    Returns:
        mod0_reco_energy: Array of reconstructed energies for module 0
        reco: Array of reconstructed energies for all cells (from index 17 onward)
    """
    file = uproot.open(path)
    tree = file["tree"]
    keys = tree.keys()
    reco = []
    # Collect all arrays with 'reco_energy' in their key
    for key in keys:
        if "reco_energy" in key:
            reco.append(tree[key].array(library="np"))
    reco = np.array(reco[17::])  # Select from index 17 onward
    file.close()
    return tree["mod0_reco_energy"].array(library="np"), reco

# Calculate mean and std of energy, cleaning outliers
def calc_momenta(en: np.array, count, edges):
    """
    Calculates mean and standard deviation of energy, removing outliers.
    Parameters:
        en: Energy array
        count: Histogram counts
        edges: Histogram bin edges
    Returns:
        mean: Mean energy
        std: Standard deviation
        en: Cleaned energy array
    """
    mean = np.mean(en)
    # Remove low energy entries
    en = (np.where(en < mean / 2, 0, en))
    en = en[en.nonzero()]
    mean = np.mean(en)
    std = np.std(en)

    # Create histogram to identify outliers
    count, edges = np.histogram(en, bins=100)
    c_max = max(count)
    c_mean = np.mean(count)

    # Remove bins with low counts
    if c_max > 100:
        for i in range(len(count)):
            if count[i] < c_mean:
                en = np.where((en > edges[i]) & (en < edges[i + 1]), 0, en)
        en = en[en.nonzero()]
    
    # Remove entries more than 2 std from mean
    en = np.where(np.abs(en - np.mean(en)) / np.std(en) < 1, en, 0)
    en = en[en.nonzero()]
    return np.mean(en), np.std(en), en

# Sturges' formula for optimal bin number
def sturges(n):
    """
    Calculates optimal number of bins using Sturges' formula.
    Parameters:
        n: Number of data points
    Returns:
        Number of bins
    """
    return int(np.ceil(1 + np.log2(n)))

# Fit a Gaussian to the histogram using ExtendedBinnedNLL
def gauss_fit(cdf, mean, std, en, fixed=False):
    """
    Fits a Gaussian to the histogram using ExtendedBinnedNLL.
    Parameters:
        cdf: Cumulative distribution function
        mean: Initial mean guess
        std: Initial std guess
        en: Energy array
        fixed: If True, fixes mean during fit
    Returns:
        Fitted mean, std, normalization, covariance matrix
    """
    count, edges = np.histogram(en, bins=n_bins)
    cost = ExtendedBinnedNLL(count, edges, cdf)
    p_index = list(count).index(max(count))  # Index of peak bin
    cost = ExtendedBinnedNLL(count, edges, cdf)
    n = Minuit(cost, mu=(edges[p_index] + edges[p_index + 1]) / 2, sigma=std, N=len(en))
    if fixed:
        n.fixed["mu"] = True
    n.migrad(ncall=1000)
    # Plot fit (commented out by default)
    plt.hist(en, bins=n_bins, histtype="step")
    plt.plot(
        np.linspace(min(en), max(en), len(edges) - 1),
        (n.values[2] * norm.pdf(
            np.linspace(min(en), max(en), len(edges) - 1),
            loc=n.values[0], scale=n.values[1]
        )) * np.diff(edges)
    )
    # plt.show()
    plt.clf()
    if n.valid:
        return n.values[0], n.values[1], n.values[2], n.covariance
    else:
        # Retry with mean fixed if fit fails
        return gauss_fit(cdf, mean, std, en, fixed=True)

# Apply linear correction to energy values
def corrected(en: float, n: Minuit):
    """
    Applies linear correction to energy values.
    Parameters:
        en: Energy value(s)
        n: Minuit fit object
    Returns:
        Corrected energy value(s)
    """
    return (en - n.values[0]) / n.values[1]

# Error propagation for ratio a/b
def err_prop(a, b, cov):
    """
    Error propagation for ratio a/b.
    Parameters:
        a: Numerator
        b: Denominator
        cov: Covariance matrix
    Returns:
        Propagated error
    """
    if isinstance(a, type(np.array([0, 0]))) and isinstance(b, type(np.array([0, 0]))):
        err_list = []
        for i in range(len(a)):
            cov_i = np.delete(cov[i], 2, 0)  # Delete third row
            cov_i = np.delete(cov_i, 2, 1)   # Delete third column
            err_list.append(propagazione_errore(['a', 'b'], 'a/b', [a[i], b[i]], cov_i, Display=False))
        return np.float32(err_list)
    else:
        return propagazione_errore(['a', 'b'], 'a/b', [a, b], cov)

# Energy resolution function
def e_res(E, a, b, c):
    """
    Energy resolution function.
    Parameters:
        E: Energy
        a, b, c: Fit parameters
    Returns:
        Energy resolution
    """
    return np.sqrt(np.power(a / np.sqrt(E), 2) + np.power(b / E, 2) + np.power(c, 2))

def e_res2(E, a, c):
    """
    Alternative energy resolution function (without b term).
    Parameters:
        E: Energy
        a, c: Fit parameters
    Returns:
        Energy resolution
    """
    return np.sqrt(np.power(a / np.sqrt(E), 2) + np.power(c, 2))

# Main script execution
if __name__ == "__main__":

    # Create output directories if they don't exist
    os.makedirs(output_path, exist_ok=True)
    os.makedirs(root_path, exist_ok=True)

    # List all files in input directory
    files = os.listdir(input_path)
    print(files)

    # Extract starting energies from filenames
    starting_energy = np.array([int(file.split(".")[0].removeprefix("resolution_")) for file in files])*coeff

    # Read reconstructed energy arrays from files
    reconstructed_energies_list = [
        Readout_convertion(f"{input_path}/{file}")[0] for file in files
    ]
    reconstructed_cell_list = np.array([
        Readout_convertion(f"{input_path}/{file}")[1] for file in files
    ])

    mean = []  # List to store means
    standard_deviation = []  # List to store standard deviations
    N = []  # List to store normalization factors
    covariance = []  # List to store covariance matrices

    # Loop over each energy sample
    for energy in reconstructed_energies_list:
        m, s, e = calc_momenta(energy, *np.histogram(energy, bins=n_bins))
        m, s, n, cov = gauss_fit(cdf, m, s, e)
        mean.append(m)
        standard_deviation.append(s)
        N.append(n)
        covariance.append(cov)

    # Normalize mean and std by starting energy
    normalized_mean = np.array(mean) / starting_energy
    normalized_standard_deviation = np.array(standard_deviation) / starting_energy

    # Fit a line to mean vs starting energy
    least_squares_fit = LeastSquares(starting_energy, mean, standard_deviation, line)
    linear_fit = Minuit(least_squares_fit, m=0, q=0)
    linear_fit.fixed["q"] = True
    linear_fit.migrad()

    # Calculate chi-square and p-value
    chi2_value = least_squares_fit(linear_fit.values["q"], linear_fit.values["m"])
    ndof = len(starting_energy) - linear_fit.nfit
    p_value = 1 - chi2.cdf(chi2_value, ndof)
    print(f"Chi-square: {chi2_value:.2f}, ndof: {ndof}, p-value: {p_value:.4f}")

    # Plot the data and the fitted line
    # Generate fit line and plot data with error bars
    x_fit = np.linspace(min(starting_energy), max(starting_energy), 100)
    plt.errorbar(starting_energy, mean, yerr=standard_deviation, fmt="o", markersize=3, label="Measured Means")
    plt.text(
        0.05, 0.95,
        f"$\\chi^2$ = {chi2_value:.2f}\n$p$ = {p_value:.4f}",
        transform=plt.gca().transAxes,
        verticalalignment='top',
        fontsize=10,
        bbox=dict(facecolor='white', alpha=0.7, edgecolor='none')
    )
    plt.plot(x_fit, line(x_fit, linear_fit.values["q"], linear_fit.values["m"]), label=f"y = {linear_fit.values['m']:.3f} x", color="red")
    plt.xlabel("Starting Energy [GeV]\n ")
    plt.ylabel("pulse amplitude value [Vt]")
    plt.title("Energy Calibration: Mean vs Starting Energy")
    plt.legend()
    # Add line coefficients to the plot
    plt.text(
        0.05, 0.85,
        f"Slope (m): {linear_fit.values['m']:.3f}\n",
        transform=plt.gca().transAxes,
        verticalalignment='top',
        fontsize=10,
        bbox=dict(facecolor='white', alpha=0.7, edgecolor='none')
    )
    plt.tight_layout()
    plt.savefig("data_analysis/energy_res/energy_calibration.pdf")
    plt.clf()
    print( type(linear_fit.values[0]))
    print( linear_fit.values)
    # save linear regression coefficients into a file
    with open("data_analysis/energy_res/linear_regression_coefficients.csv", "w") as myfile:
            myfile.write( f"{linear_fit.values[0]} , {linear_fit.values[1]}")