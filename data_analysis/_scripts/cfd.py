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

n_bins = 40

def Resolution_convertion(path: str):
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

    data = np.where( (data > 0) & (data < 8*np.mean(data)) , data , 0)
    count, edges = np.histogram(data, bins=bins)
    valid_bins = count >= 5
    # Build mask for data points in valid bins
    bin_indices = np.digitize(data, edges) - 2
    mask = valid_bins[bin_indices]
    data = data[mask]
    data = data[data.nonzero()]

    iteration += 1
    mean = np.mean(data)
    std = np.std(data)
    # count, edges = weighted_binning(data, bins)
    count , edges = np.histogram( data , bins)
    cost = ExtendedBinnedNLL(count, edges, model_cdf)
    n = Minuit(cost, mu=mean, sigma=std, N=len(data))
    n.migrad(ncall=1000)
    n.hesse()

    # Plot histogram using weighted binning
    plt.hist(data, bins=edges, histtype="step")
    plt.plot(
        np.linspace(min(data), max(data), len(edges) - 1),
        (n.values[2] * norm.pdf(
            np.linspace(min(data), max(data), len(edges) - 1),
            loc=n.values[0], scale=n.values[1]
        )) * np.diff(edges)
    )
    plt.axvline(np.min(data), color='green', linestyle='--', label='Min')
    plt.axvline(np.max(data), color='green', linestyle='--', label='Max')
    plt.savefig("data_analysis/time_resolution/hist_fit/" + energy_label)
    plt.clf()
    plt.close()
    if n.valid:
        if n.fval / n.ndof > 5:
            if not removetail:
                return gauss_fit(remove_tail(data), percentage_index, bins, iteration, removetail=True, initial_data=initial_data, energy_label=energy_label)
            else:
                if not failed:
                    if bins < 8:
                        return gauss_fit(initial_data, percentage_index, failed=True, removetail=True , initial_data=initial_data, energy_label=energy_label)
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

def cfd(energy_selections, error_selections, percentage_index, energy_values, energy_idx):
    std_results = []
    matrix = 0
    with open("data_analysis/time_resolution/cfd/binning.csv", "r") as myfile:
            matrix = [list(map(int, line.strip().split(','))) for line in myfile if line.strip()]
            percentage = [ i[-1] for i in matrix]

    for perc in range(len(energy_selections)):
        if int((perc+1)*10) in percentage:
            bin = matrix[percentage.index(int((perc+1)*10))][energy_idx]
        else: bin = n_bins


        plt.title(f"energy: {energy_values[energy_idx]} , perc: {(perc+1)*10}%")
        _, std, _, cov = gauss_fit(
            energy_selections[perc],
            percentage_index,
            bins=bin,
            initial_data=energy_selections[perc],
            energy_label=f"{energy_values[energy_idx]}GeV_{(perc+1)*10}%"
        )
        std_results.append([std, cov[1, 1]])
    return std_results

      

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

    starting_energy = np.array([int(file.split(".")[0].removeprefix("resolution_")) for file in files])
    
    e_risetime = [ Resolution_convertion(input_path + "/slanted_e/"+file) for file in files]

    e_err = [a[1] for a in e_risetime]

    e_risetime = [a[0] for a in e_risetime]

    e_std = []


    chi_prob = []
    for energy in range( len(e_risetime)):
        
        e_std.append(cfd(e_risetime[energy] , e_err[energy] , False , starting_energy , energy))

    for percentage in range(10):
        e_perc_selection = np.array([i[percentage][0] for i in e_std], dtype=np.float32)
        
        e_perc_selection_err = np.array([i[percentage][1] for i in e_std], dtype=np.float32)


        # Fit energy resolution function to data
        e_time_resolution_fit = LeastSquares(starting_energy, e_perc_selection, e_perc_selection_err, e_res)
        e_resolution_minuit = Minuit(e_time_resolution_fit, a=0, b=0, c=0)
        e_resolution_minuit.fixed["b"] = True
        e_resolution_minuit.limits["a","c"] = (0.0000000001 , None)
        e_resolution_minuit.migrad()
        chi_square_prob = 1 - chi2.cdf(e_resolution_minuit.fval, df=e_resolution_minuit.ndof)
        chi_prob.append(chi_square_prob)


        energy_range = np.linspace(0.3, 105, 200)
        scale_factor = 1000  # Multiply y-axis by 2 orders of magnitude
        plt.errorbar(starting_energy, e_perc_selection * scale_factor, e_perc_selection_err * scale_factor, fmt="o", label="Data", markersize=4)
        plt.plot(energy_range, np.clip(e_res(energy_range, *e_resolution_minuit.values) * scale_factor, None, 210), label="Fit" , color = "red")
        plt.axhline(20, color='orange', linestyle='--', label='y=2')
        coeffs = e_resolution_minuit.values
        print(coeffs, "============================================")
        chi_square_prob_str = f"{(1 - chi2.cdf(e_resolution_minuit.fval, df=e_resolution_minuit.ndof)):.3g}"
        # Calculate errors for a and c
        errors = e_resolution_minuit.errors
        coeffs_str = (
            f"s={coeffs['a']*100:.2g}% ± {errors['a']*100:.2g}%,\n"
            f"c={coeffs['c']*100:.2g}% ± {errors['c']*100:.2g}%"
        )
        print(f"Time Resolution Fit: {(percentage+1)*10}%")
        plt.title(f"Time Resolution Fit: {(percentage+1)*10}%")
        plt.xlabel("Beam Energy [GeV]")
        plt.ylabel("Time resolution [ps]")


        # Make y-ticks denser
        ymin, ymax = plt.ylim()
        plt.yticks(np.linspace(round(4), round(210), 10))

        plt.text(
            0.5, 0.98,
            f"{(percentage+1)*10}%\n{coeffs_str}\n",
            ha='center', va='top',
            transform=plt.gca().transAxes,
            bbox=dict(facecolor='white', alpha=0.8, edgecolor='gray')
        )
        plt.tight_layout()
        plt.grid()
        plt.savefig(f"{output_path}/time_res/timeres_{(percentage+1)*10}.pdf")
        print( f"{output_path}/time_res/timeres_{(percentage+1)*10}.pdf")
        plt.clf()
    for energy in range(len(starting_energy)):
    
        e_perc_list = []
        # pi_perc_list = []
        e_perc_err_list = []
        # pi_perc_err_list = []
        for percentage in range(len(e_std[energy])):
            e_perc_list.append(e_std[energy][percentage][0])
            # pi_perc_list.append(pi_std[energy][percentage][0])
            e_perc_err_list.append(e_std[energy][percentage][1])
            # pi_perc_err_list.append(pi_std[energy][percentage][1])
        ls = LeastSquares(np.arange(10, 110, 10), e_perc_list, e_perc_err_list, model_parabola)
        m = Minuit(ls, 1, 1, 1)
        m.migrad(ncall=1000)
        min_fit = -m.values[1]/(2*m.values[0])

        # Plot error bars for each percentage point (y-axis multiplied by 1000)
        plt.errorbar(np.arange(10, 110, 10), np.array(e_perc_list) * 1000, np.array(e_perc_err_list) * 1000, fmt="o", color="royalblue", label="Data")

        # Overlay the fitted parabola curve (y-axis multiplied by 1000)
        perc_range = np.linspace(10, 100, 200)
        # plt.plot(perc_range, model_parabola(perc_range, *m.values) * 1000, "r--", label="Parabola Fit")

        plt.title(f"Error comparison at {starting_energy[energy]}GeV", fontsize=13)
        plt.xlabel("Percentage", fontsize=11)
        plt.ylabel(f"$\sigma_t$  [ps]", fontsize=11)
        plt.legend()
        plt.grid(True, linestyle=":", alpha=0.6)
        plt.tight_layout()
        plt.savefig(f"{output_path}/cfd/cfd_{starting_energy[energy]}GeV.pdf")
        plt.clf()
    
    # plt.scatter(np.arange(10, 100, 10), chi_prob)
    # plt.xlabel("Percentage")
    # plt.ylabel("Probability")
    # plt.savefig(output_path+"/prob_trend.png")
    # plt.show()