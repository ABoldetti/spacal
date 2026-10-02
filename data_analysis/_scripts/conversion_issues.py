import uproot  # For reading ROOT files
import ROOT    # For writing ROOT files
import numpy as np  # For numerical operations
import matplotlib.pyplot as plt  # For plotting
from iminuit import Minuit  # For minimization/fitting
from iminuit.cost import ExtendedBinnedNLL, LeastSquares  # Cost functions for fitting
from scipy.stats import norm, chi2  # Statistical distributions
import os  # For file and directory operations
from sys import argv  # For command-line arguments
import decimal as d

from error_propagation import propagazione_errore  # Custom error propagation function
import array  # For array operations (used in ROOT trees)


# Set input and output paths for data
input_path = argv[1] if len(argv) > 1 else "data_analysis/readout/slanted_e"
output_path = input_path.replace("readout", "energy_res")
root_path = argv[2] if len(argv) > 2 else input_path.replace("readout", "root_resolution")
n_bins = 50  # Number of bins for histograms
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
    empty = []
    # Collect all arrays with 'reco_energy' in their key
    val = False
    for key in keys:
        if "reco_energy" in key:
            if "16" in key:
                val = True
            
            if val:
                reco.append(tree[key].array(library="np").tolist())
            if not val:
                empty.append( tree[key].array(library="np").tolist())


    file.close()
    full_energy = tree["mod0_reco_energy"].array(library="np").tolist()
    for i in range(len(full_energy)):
        full_energy[i] = d.Decimal(full_energy[i])
        for cell in range(len(reco)):
            reco[cell][i] = d.Decimal(reco[cell][i])
            empty[cell][i] = d.Decimal(empty[cell][i])
    full_energy = np.array( full_energy )
    reco = np.array( reco )
    empty = np.array(empty)



    return full_energy, reco , empty


def corrected(en: d.Decimal, q: d.Decimal , m: d.Decimal):
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
    count, edges = np.histogram( en, bins=100)
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
    



if __name__ =="__main__":


    # Create output directories if they don't exist
    os.makedirs(output_path, exist_ok=True)
    os.makedirs(root_path, exist_ok=True)

    d.getcontext().prec = 80

    # List all files in input directory
    files = os.listdir(input_path)
    print(files)

    linear_regression_coefficients = []
    with open("data_analysis/energy_res/linear_regression_coefficients.csv", "r") as myfile:
        string = myfile.read()
    print(string)
    linear_regression_coefficients = [d.Decimal(i) for i in string.split(",") ]
    starting_energy = np.array([float(file.split("GeV")[0]) for file in files])*coeff

    # Read reconstructed energy arrays from files
    reconstructed_energies_list = [
        Readout_convertion(f"{input_path}/{file}")[0] for file in files
    ]
    reconstructed_cell_list = np.array([
        Readout_convertion(f"{input_path}/{file}")[1] for file in files
    ])
    empty = np.array([
        Readout_convertion(f"{input_path}/{file}")[2] for file in files
    ])



    mean = []  # List to store means
    standard_deviation = []  # List to store standard deviations
    N = []  # List to store normalization factors
    covariance = []  # List to store covariance matrices

    # Loop over each energy sample
    for energy in reconstructed_energies_list:
        ausy = np.copy(energy)
        ausy = np.array( ausy , dtype = np.float32)
        m, s, e = calc_momenta(ausy, *np.histogram( ausy , bins=n_bins) )
        m, s, n, cov = gauss_fit(cdf, m, s, e)
        mean.append(m)
        standard_deviation.append(s)
        N.append(n)
        covariance.append(cov)
    plt.clf()
    plt.close()

    non_corrected_cell = np.copy(reconstructed_cell_list)
    non_corrected_energy = np.copy(reconstructed_energies_list)

    for i in range(len(reconstructed_energies_list)):
        print( starting_energy[i])
        
        reconstructed_energies_list[i] = corrected(reconstructed_energies_list[i], *linear_regression_coefficients)
        s_cell = []
        for cell in range(16):

            # empty[i][cell] = corrected( empty[i][cell] , *linear_regression_coefficients)
            # Store the non-corrected version for plotting
            
            # Apply correction
            reconstructed_cell_list[i][cell] = corrected(reconstructed_cell_list[i][cell], *linear_regression_coefficients)
            corrected_cell = np.array(reconstructed_cell_list[i][cell], dtype=np.float32)
            

            s_cell.append( reconstructed_cell_list[i][cell])
        s_cell = sum(s_cell)
        print( np.mean(s_cell) , np.mean(reconstructed_energies_list[i]))
        print( np.std(s_cell) , np.std(reconstructed_energies_list[i]))
        plt.hist( np.array(s_cell , dtype=np.float32), bins = n_bins , histtype="step" , label="s_cell" )
        plt.hist( np.array(reconstructed_energies_list[i] , dtype=np.float32) , bins = n_bins , histtype="step" , label="tot en" )
        plt.title(f"energy: {starting_energy[i]}")
        plt.legend()
        plt.show()
    


    for event in range(len( reconstructed_energies_list[i])):
        for i in range( len( starting_energy)):
            
            perc = 0
            nc_perc = 0
            for cell in range(16):
                print( "cell : " , cell)
                print( "====================converted===============================")
                print( reconstructed_cell_list[i][cell][event]/reconstructed_energies_list[i][event])
                perc += reconstructed_cell_list[i][cell][event]/reconstructed_energies_list[i][event]
                print( "cell=" , reconstructed_cell_list[i][cell][event])
                print( "total=" , reconstructed_energies_list[i][event])
                print( "====================not converted===============================")
                print( non_corrected_cell[i][cell][event]/non_corrected_energy[i][event])
                nc_perc += non_corrected_cell[i][cell][event]/non_corrected_energy[i][event]
                print( "cell=" , non_corrected_cell[i][cell][event])
                print( "total=" , non_corrected_energy[i][event])
                print("\n\n")
            print( "--------------------------------------------------------------------------------")
            print( "--------------------------------------------------------------------------------")
            print( sum([reconstructed_cell_list[i][cell][event] for cell in range(16)]) , reconstructed_energies_list[i][event])
            print( starting_energy[i])
            print( perc , nc_perc)
            input()

    
