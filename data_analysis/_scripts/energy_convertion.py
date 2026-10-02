from matplotlib.transforms import offset_copy

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
root_path = argv[2] if len(argv) > 2 else None
n_bins = 20  # Number of bins for histograms
coeff = 1

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


def corrected(en: float, q: float , m: float):
    """
    Applies linear correction to energy values.
    Parameters:
        en: Energy value(s)
        n: Minuit fit object
    Returns:
        Corrected energy value(s)
    """
    return (en - q) / m

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
    
    # Create histogram to identify outliers
    count, edges = np.histogram(en, bins=100)
    c_max = max(count)
    c_mean = np.mean(count[count.nonzero()])
    # Remove bins with low counts
    if c_max > 100:
        for i in range(len(count)):
            if count[i] < c_mean:
                en = np.where((en > edges[i]) & (en < edges[i + 1]), 0, en)
        en = en[en.nonzero()]
    
    return np.mean(en), np.std(en), en


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
    plt.close()
    if n.valid:
        return n.values[0], n.values[1], n.values[2], n.covariance
    else:
        # Retry with mean fixed if fit fails
        return gauss_fit(cdf, mean, std, en, fixed=True)

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


if __name__ =="__main__":


    # Create output directories if they don't exist
    os.makedirs(output_path, exist_ok=True)
    

    # List all files in input directory
    files = os.listdir(input_path)
    print(files)

    linear_regression_coefficients = []
    with open("data_analysis/energy_res/linear_regression_coefficients.csv", "r") as myfile:
        string = myfile.read()
    print(string)
    linear_regression_coefficients = [float(i) for i in string.split(",") ]
    starting_energy = np.array([float(file.split("GeV")[0]) for file in files])*coeff

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
    for idx, energy in enumerate(reconstructed_energies_list):
        m, s, e = calc_momenta(energy, *np.histogram(energy, bins=n_bins))
        m, s, n, cov = gauss_fit(cdf, m, s, e)
        mean.append(m)
        standard_deviation.append(s)
        N.append(n)
        covariance.append(cov)
        # Plot histogram and Gaussian fit with statistics box
        fig, ax = plt.subplots(figsize=(7, 5))
        hist_data, hist_bins, _ = ax.hist(e, bins=n_bins, histtype="step", color="navy", linewidth=1.5, label="Data")
        # Use a dense set of points for the fit curve
        fit_x = np.linspace(hist_bins[0], hist_bins[-1], 500)
        fit_curve = (n * norm.pdf(fit_x, loc=m, scale=s)) * np.diff(hist_bins)[0]
        ax.plot(fit_x, fit_curve, color="crimson", linewidth=1.5, label="Gaussian Fit")

        # Calculate expected counts for each bin center
        bin_centers = (hist_bins[:-1] + hist_bins[1:]) / 2
        expected_counts = (n * norm.pdf(bin_centers, loc=m, scale=s)) * np.diff(hist_bins)
        # Calculate chi-square
        chi_sq = np.sum((hist_data - expected_counts) ** 2 / (expected_counts + 1e-8))
        ndof = len(hist_data) - 3
        chi_sq_prob = 1 - chi2.cdf(chi_sq, ndof)

        # Stats box text
        stats_text = (
            f"Mean = {m:.3f}\n"
            f"Std = {s:.3f}\n"
            f"χ²/ndof = {chi_sq:.2f}/{ndof} = {chi_sq/ndof:.2f}\n"
            f"p = {chi_sq_prob:.3f}"
        )
        props = dict(boxstyle='round', facecolor='white', alpha=0.85, edgecolor='gray')
        ax.text(0.98, 0.98, stats_text, transform=ax.transAxes, fontsize=11,
                verticalalignment='top', horizontalalignment='right', bbox=props)

        ax.set_xlabel("Energy Vt", fontsize=13)
        ax.set_ylabel("Counts", fontsize=13)
        ax.set_title(f"Energy Distribution and Gaussian Fit ({starting_energy[idx]} GeV)", fontsize=15)
        ax.legend(fontsize=12)
        plt.tight_layout()
        plt.savefig(f"{output_path}/{files[idx].replace('.root', '_unconverted_energy_fit.pdf')}")
        plt.close()


    
    # Plot and save corrected histograms and fits
    for i in range(len(reconstructed_energies_list)):
        fig, axs = plt.subplots(1, 1)
        reconstructed_energies_list[i] = corrected(reconstructed_energies_list[i], *linear_regression_coefficients)
        s_cell = 0
        for cell in range(16):
            reconstructed_cell_list[i][cell] = np.float64(corrected(np.float64(reconstructed_cell_list[i][cell]), *linear_regression_coefficients))
            s_cell+= reconstructed_cell_list[i][cell]
        hist_edges = np.histogram(reconstructed_energies_list[i], bins=n_bins)[1]
        hist_range = np.linspace(min(reconstructed_energies_list[i]), max(reconstructed_energies_list[i]), 1000)
        # Plot total reconstructed energy histogram and fit
        axs.hist(reconstructed_energies_list[i], bins=n_bins, histtype="step", label="Total Energy")
        axs.plot(
            hist_range,
            (N[i] * norm.pdf(
            hist_range,
            loc=corrected(mean[i], *linear_regression_coefficients),
            scale=corrected(standard_deviation[i], *linear_regression_coefficients)
            )) * np.diff(hist_edges)[0],
            color="red", label="Gaussian Fit"
        )
        # Calculate chi-square for the fit
        observed_counts, _ = np.histogram(reconstructed_energies_list[i], bins=hist_edges)
        expected_counts = (N[i] * norm.pdf(
            (hist_edges[:-1] + hist_edges[1:]) / 2,
            loc=corrected(mean[i], *linear_regression_coefficients),
            scale=corrected(standard_deviation[i], *linear_regression_coefficients)
        )) * np.diff(hist_edges)
        chi_square = np.sum((observed_counts - expected_counts) ** 2 / (expected_counts + 1e-8))
        ndof = len(observed_counts) - 3  # mean, std, norm fitted
        chi_square_prob = 1 - chi2.cdf(chi_square, ndof)
        chi_square_text = f"χ²/ndof = {chi_square:.2f}/{ndof} = {chi_square/ndof:.2f}, p = {chi_square_prob:.3f}"

        axs.set_title(f"{files[i]}: Total Energy")
        axs.set_xlabel("Energy (GeV)")
        axs.set_ylabel("Counts")
        axs.legend()
        mean_val = corrected(mean[i], *linear_regression_coefficients)
        std_val = corrected(standard_deviation[i], *linear_regression_coefficients)
        axs.text(0.05, 0.95, f"Mean = {mean_val:.3f}\nStd = {std_val:.3f}\n{chi_square_text}",
                transform=axs.transAxes, fontsize=10, verticalalignment='top', bbox=dict(facecolor='white', alpha=0.7))
        total_energy_image = f"{output_path}/{files[i].replace('root', 'total_energy.pdf')}"

        plt.tight_layout()
        plt.savefig(total_energy_image)
        # plt.show()
        plt.close()

    # Calculate corrected resolution and error
    corrected_std = corrected(np.array(standard_deviation), *linear_regression_coefficients)
    corrected_mean = corrected(np.array(mean), *linear_regression_coefficients)
    corrected_resolution = corrected_std / corrected_mean
    corrected_resolution_error = err_prop(np.array(standard_deviation), np.array(mean), np.array(covariance))

    # Fit energy resolution function to data
    energy_resolution_fit = LeastSquares(starting_energy, corrected_resolution, corrected_resolution_error, e_res)
    resolution_minuit = Minuit(energy_resolution_fit, a=1, b=0, c=1)
    resolution_minuit.fixed["b"] = True
    resolution_minuit.limits["a","c"] = (0.0001 , None)
    resolution_minuit.migrad()
    chi_square_prob = 1 - chi2.cdf(resolution_minuit.fval, df=resolution_minuit.ndof)
    print("chi square prob", chi_square_prob, resolution_minuit.fval / resolution_minuit.ndof)
    print(resolution_minuit.values)

    # Plot and save energy resolution curve
    # Plot energy resolution curve with fit and save as image
    energy_range = np.linspace(0.5, 102, 500)
    print( corrected_resolution_error , corrected_resolution)
    plt.errorbar(starting_energy, corrected_resolution, corrected_resolution_error, fmt="o", markersize=3.5, label="Data")
    a_percent = resolution_minuit.values[0] * 100
    c_percent = resolution_minuit.values[2] * 100
    # Get errors from covariance matrix
    a_err = resolution_minuit.errors["a"] * 100
    c_err = resolution_minuit.errors["c"] * 100
    # Chi square and probability
    chi2_val = resolution_minuit.fval
    ndof = resolution_minuit.ndof
    chi2_prob = 1 - chi2.cdf(chi2_val, ndof)
    # Only show "Fit" in label
    plt.plot(energy_range, e_res(energy_range, *resolution_minuit.values), label="Fit", color="red")
    plt.plot(energy_range, e_res( energy_range , 0.1 , 0 , 0.01) , label="goal( s=10%, c=1%)" , color = "grey" , linestyle = "--")
    plt.xlabel("Energy (GeV)")
    plt.ylabel("Energy Resolution (σ/E)")
    plt.title("Energy Resolution vs Energy")
    plt.legend()
    # Add textbox for coefficients and chi-square
    textbox_text = (
        f"s = ({a_percent:.2f} ± {a_err:.2f})%\n"
        f"c = ({c_percent:.2f} ± {c_err:.2f})%\n"
    )
    ax = plt.gca()
    txt = ax.text(
        0.5, 0.95, textbox_text,
        transform=ax.transAxes,
        fontsize=10, verticalalignment='top', horizontalalignment='center',
        bbox=dict(facecolor='white', alpha=0.7)
    )
    txt.set_transform(offset_copy(ax.transAxes, fig=plt.gcf(), x=-20, y=0, units='dots'))
    plt.tight_layout()
    plt.savefig(f"{output_path}/energy_resolution.pdf")
    plt.show()
    plt.clf()

    # Create a new ROOT file and tree for each energy
    if root_path is not None:
        os.makedirs(root_path, exist_ok=True)
        for energy_idx in range(len(starting_energy)):
            root_file_name = f"{root_path}/resolution_{starting_energy[energy_idx]/coeff}GeV.root"
            f = uproot.open(root_file_name)
            output_root_file = ROOT.TFile(root_file_name, "UPDATE")
            f = uproot.open(root_file_name)

            # Delete existing energy_resolution tree if present
            for key in f.keys():
                if "energy_resolution" in key:
                    output_root_file.Delete(key)
            f.close()

            # Create new tree
            tree = ROOT.TTree("energy_resolution", "Energy resolution results")
            n_events = len(reconstructed_energies_list[energy_idx])
            n_cells = len(reconstructed_cell_list[energy_idx])

            energy_hist = array.array("f", [0])
            cell_arrays = [array.array("f", [0]) for _ in range(n_cells)]

            tree.Branch("full_reconstructed_energy", energy_hist, "full_reconstructed_energy/F")
            for cell_idx in range(n_cells):
                tree.Branch(f"cell{cell_idx}_reconstructed_energy", cell_arrays[cell_idx], f"cell{cell_idx}_reconstructed_energy/F")

            # Fill tree with data
            for event_idx in range(n_events):
                energy_hist[0] = reconstructed_energies_list[energy_idx][event_idx]
                for cell_idx in range(n_cells):
                    cell_arrays[cell_idx][0] = reconstructed_cell_list[energy_idx][cell_idx][event_idx]
                tree.Fill()

            print("printing file in:", root_file_name)

            # Write and close the file
            output_root_file.Write()
            output_root_file.Close()