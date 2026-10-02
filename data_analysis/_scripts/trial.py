import uproot
import numpy as np
import matplotlib.pyplot as plt
from iminuit import Minuit
from iminuit.cost import LeastSquares
import warnings
from scipy.integrate import cumulative_trapezoid
from scipy.optimize import curve_fit 
from scipy.signal import lfilter
import copy
import os
from error_propagation import propagazione_errore
from IPython.display import display
from sys import argv,exit
import ROOT
from array import array



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
    risetime_err = np.array(risetime_err)
    
    result = [ risetime[i] for i in range(1 , len(risetime))]

    err = [ risetime_err[i] for i in range(1 , len(risetime))]

    return [result,err]


if __name__ =="__main__":


    energies = [100, 80, 60, 40, 20, 10, 5, 2, 1]
    results = []
    for E in energies:
        path = f"data_analysis/root_resolution/slanted_e/resolution_{E}.0GeV.root"
        results.append(Resolution_convertion(path))
        

    fig, axs = plt.subplots(len(energies), 1, figsize=(8, 3 * len(energies)), sharex=True)

    # Plot histograms as before
    for idx, (E, res) in enumerate(zip(energies, results)):
        for i, data in enumerate(res[0]):
            axs[idx].hist(data, histtype="step", label=f'{E} GeV [{i}]')
        axs[idx].set_title(f'Histogram for {E} GeV')
        # axs[idx].legend()
        axs[idx].set_ylabel('Counts')
        axs[idx].grid(True)
        axs[idx].text(0.95, 0.95, f"std([-1])={np.std(res[0][-1]):.3f}\nstd([-2])={np.std(res[0][-2]):.3f}",
                      transform=axs[idx].transAxes, fontsize=10, verticalalignment='top', horizontalalignment='right')

    # Compute standard deviations for each energy and each data set
    stds = []
    for res in results:
        stds.append([np.std(data) for data in res[0]])

    # Plot standard deviations in a new figure
    fig2, axs2 = plt.subplots(1, 1, figsize=(8, 6))
    stds_arr = np.array(stds)
    for i in range(stds_arr.shape[1]):
        axs2.plot(energies, stds_arr[:, i], marker='o', label=f'Std [{i}]')
    axs2.set_xlabel('Energy (GeV)')
    axs2.set_ylabel('Standard Deviation')
    axs2.set_title('Standard Deviations vs Energy')
    axs2.legend()
    axs2.grid(True)

    axs[-1].set_xlabel('Value')
    plt.tight_layout()
    fig.savefig("data_analysis/time_resolution/slanted_e/"+"cfg_summary.pdf")
    fig2.savefig("data_analysis/time_resolution/slanted_e/"+"cfg_std.pdf")
    plt.show()
