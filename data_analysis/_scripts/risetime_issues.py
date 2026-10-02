import numpy as np
import uproot
import matplotlib.pyplot as plt
import os
from iminuit import Minuit
from iminuit.cost import ExtendedBinnedNLL , LeastSquares
from scipy.stats import norm , chi2
from error_propagation import propagazione_errore




input_path = "root_resolution"
output_path = "data_analysis/time_resolution"

n_bins = 60
en = 0
perc = "40"

# 20 , 20 , 20 , 20 , 20 , 20 , 20 , 35 , 80
# 18 , 22 , 22 , 25 , 25 , 23 , 24 , 33 , 60


def Resolution_convertion(path: str , string = "30"):
    """
    Reads ROOT file and extracts 'mod0_ph' and 'mod0_pulse' arrays from the tree.

    Parameters
    ----------
    path : str
        Path to the ROOT file.

    Returns
    -------
    mod_ph : np.ndarrayx == cell[0]
        Array of photon counts.
    mod_pulse : np.ndarray
        Array of pulse shapes.
    """
    file = uproot.open(path)
    t_res = file["time_resolution"]

    t_keys=t_res.keys()

    risetime = []
    risetime_err = []
    for key in t_keys:
        if string in key:
            if key.endswith("error"):
                risetime_err.append(t_res[key].array(library="np"))
            else:
                risetime.append( t_res[key].array(library="np") )
    risetime = np.array(risetime)
    result = risetime
    result = np.array(result) 
    risetime_err = np.array(risetime_err)
    err = [ risetime_err[i] for i in range(1 , len(risetime))]

    return [result,err]

def f(count):
    return max(1, int(np.log2(count+1)))



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

def model_parabola(x, a, b, c):
    return a * x**2 + b * x + c

      

def remove_tail(en):
    
    count, edges = np.histogram(en, bins=n_bins)
    m_count = list(count).index( max(count))
    en = np.where(np.abs(en - (edges[m_count] + edges[m_count +1])/2) / np.std(en) < 2, en, 0)
    en = en[en.nonzero()]
    return en

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

def quadrature_sum(a, b):
    """
    Returns the square root of the sum of squares of two values or arrays.

    Parameters
    ----------
    a : float or np.ndarray
        First value or array.
    b : float or np.ndarray
        Second value or array.

    Returns
    -------
    float or np.ndarray
        sqrt(a**2 + b**2)
    """
    return np.sqrt(np.square(a) + np.square(b))


percentage = 4



#______________________________________________________________________________________________________________________________________
#
#--------------------------------------------------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------------------------------------------
#______________________________________________________________________________________________________________________________________
#

if __name__ == "__main__":
    files = os.listdir( input_path + "/slanted_e")
    files = sorted(files, key=lambda x: int(x.split(".")[0].removeprefix("resolution_")))
    files = files[en::]

    starting_energy = np.array([int(file.split(".")[0].removeprefix("resolution_")) for file in files])
    
    e_30 = [ Resolution_convertion(input_path + "/slanted_e/"+file , perc) for file in files]

    e_err = [a[1] for a in e_30]

    e_30 = [a[0] for a in e_30]

    e_std = []

    chi_prob = []
    for i,energy in enumerate(range( len(e_30))):
        bins = [20 , 20 , 20 , 20 , 20 , 20 , 20 , 35 , 80]
        
        count, edges = np.histogram(e_30[energy], bins=n_bins)
        valid_bins = (count>3)&((edges[1:] > 0) & (edges[:-1] < 8 * np.mean(e_30[energy])))
        print( valid_bins)
        # Build mask for data points in valid bins
        bin_indices = np.digitize(e_30[energy], edges) - 2
        mask = valid_bins[bin_indices]
        e_30[energy] = e_30[energy][mask]


        mean = np.mean(e_30[energy])
        std = np.std(e_30[energy])
        # count, edges = weighted_binning(data, bins)
        count , edges = np.histogram( e_30[energy] , bins[i])
        cost = ExtendedBinnedNLL(count, edges, model_cdf)
        n = Minuit(cost, mu=mean, sigma=std, N=len(e_30[energy]))
        n.migrad(ncall=1000)
        n.hesse()
        print( 1-chi2.cdf( n.fval , n.ndof) , n.fval)
        plt.title( f"electron distribution at {starting_energy[energy]}GeV {perc}%")
        # Plot histogram using weighted binning
        plt.hist(e_30[energy], bins=edges, histtype="step")
        plt.plot(
            np.linspace(min(e_30[energy]), max(e_30[energy]), len(edges) - 1),
            (n.values[2] * norm.pdf(
            np.linspace(min(e_30[energy]), max(e_30[energy]), len(edges) - 1),
            loc=n.values[0], scale=n.values[1]
            )) * np.diff(edges)
        )
        plt.xlabel("risetime [ns]")
        plt.ylabel("count")
        # Insert values and errors of the interpolation
        fit_mu = n.values[0]
        fit_sigma = n.values[1]

        fit_mu_err = n.errors[0]
        fit_sigma_err = n.errors[1]

        chi2_val = n.fval
        chi2_ndof = n.ndof
        chi2_prob = 1 - chi2.cdf(chi2_val, chi2_ndof)
        q_square = chi2_val / chi2_ndof if chi2_ndof > 0 else np.nan
        plt.text(
            0.05, 0.95,
            f"$\\mu$ = {fit_mu:.3f} $\pm$ {fit_mu_err:.3f}\n"
            f"$\\sigma$ = {fit_sigma:.3f} $\pm$ {fit_sigma_err:.3f}\n"
            f"$\\chi^2$ = {chi2_val:.2f} / {chi2_ndof}\n"
            f"Q$^2$ = {q_square:.2f}\n"
            f"p = {chi2_prob:.3f}",
            transform=plt.gca().transAxes,
            fontsize=10,
            verticalalignment='top',
            bbox=dict(boxstyle="round", facecolor="white", alpha=0.7)
        )
        # plt.axvline(np.min(e_30[energy]), color='green', linestyle='--', label='Min')
        # plt.axvline(np.max(e_30[energy]), color='green', linestyle='--', label='Max')
        plt.savefig("data_analysis/time_resolution/hist_fit/" + f"{starting_energy[energy]}GeV_{perc}.jpeg")
        # plt.show()
        plt.clf()
        plt.close()

