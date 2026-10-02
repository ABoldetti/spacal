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
from sys import argv,exit
from array import array

import ROOT
#import pyroot as ROOT

def usage():
    print("Usage: python time_resolution.py <input_file> [output_file] [err_acceptability] [threshold_coefficient] [baseline_sampling_factor] [exp_gap] [parabolic_fit_range]")
    print("  <input_file>: Path to the input ROOT file.")
    print("  [output_file]: (Optional) Output text file. Defaults to input_file with replacements.")
    print("  [err_acceptability]: (Optional) Number of sigmas for noise threshold (default: 10).")
    print("  [threshold_coefficient]: (Optional) Threshold for risetime percentages (default: 0.005).")
    print("  [baseline_sampling_factor]: (Optional) Number of points for noise studies (default: 10).")
    print("  [exp_gap]: (Optional) Number of points for exponential interpolation (default: 100).")
    print("  [parabolic_fit_range]: (Optional) Range for parabolic fit (default: 20).")
    print("Example:")
    print("  python time_resolution.py big_data.root")
    exit(1)

if len(argv) == 0:
        usage()



# Global configuration variables
# input and output paths
input_file = argv[1] if len(argv)>1 else "compacted_data/slanted_pi/10.0GeV/merge_Groupd.root"
# input_dir = input_file.removesuffix(input_file.split("/")[-1]).replace("compacted_data" , "big_data") if len(argv)>1 else "big_data/slanted_e/100.0GeV/"
output_file_path = argv[2].replace(".root" , ".csv") if len(argv) > 2 else None
root_path = argv[3] if len(argv) > 3 else None


energy = float(input_file.split("/")[-2].removesuffix("GeV"))

# fig paths
risetime_fig_path = f"fig/risetime/{energy}GeV/"
peak_fig_path = f"fig/peak/{energy}GeV/"
interpolated_fig_path = f"fig/interpolated/{energy}GeV/"


# interpolation/analysis variable
parabolic_fit_range = int(argv[4]) if len(argv) > 4 else int(np.floor(10/(np.log10(energy) + 1))) # n of elements to the left and the right to detect the peak(depends on the resolution of the data in input)
err_acceptability = float(argv[5]) if len(argv) > 5 else 5  # Number of sigmas for noise threshold for peak detection 
threshold_coefficient = float(argv[6]) if len(argv) > 6 else 0.0003 * (np.log2(energy) + 1) # threshold for the creation of new points in the risetime percentages. It serves as a starting point and as an additional threshold in case the scan doesn't detect any ideal point
baseline_sampling_factor = int(argv[7]) if len(argv) > 7 else 100  # Number of points taken for noise studies (this parameter is also taken as a barrier for the percentages selection)
exp_gap = int(argv[8]) if len(argv) > 8 else 100  # number of points taken for exponential interpolation



cell_considered = 5

n =100
filter_factors= np.ones(n)/n
risetime_interpolation = 200


# Data storage dictionary
struct = {
    "cell considered": [],
    "baseline": [],
    "peak": [],
    "threshold": [],
    "integral": []
}


def MergeGroupd_convertion(path: str):
    """
    Reads ROOT file and extracts 'mod0_ph' and 'mod0_pulse' arrays from the tree.

    Parameters
    ----------
    path : str
        Path to the ROOT file.

    Returns
    -------
    mod_ph : np.ndarray
        Array of photon counts.
    mod_pulse : np.ndarray
        Array of pulse shapes.
    """
    
    file = uproot.open(path)
    tree = file["tree"]
    mod_pulse = tree["mod0_pulse"].array(library="np")

    mod_pulse = [np.array([np.array(cell) for cell in event ]) for event in mod_pulse]
    mod_pulse = np.array(mod_pulse)
    return mod_pulse

# Data storage dictionary
struct = {
    "cell considered": [],
    "baseline": [],
    "peak": [],
    "threshold": [],
    "integral": []
}




def data_analysis(mod_pulse, data):
    print( "starting peak interpolation")
    for event in range(len(mod_pulse)):
        for cell in range(16):
            # Baseline calculation
            data[event]["baseline"].append((np.mean(mod_pulse[event][cell][:baseline_sampling_factor]), np.std(mod_pulse[event][cell][:baseline_sampling_factor])))
            # print( np.std(mod_pulse[event][cell][:baseline_sampling_factor]) , "ERROR BASELINE")
            debugging_bool = False
        
        
            data[event]["peak"].append(Find_Peak(mod_pulse[event][cell] , np.std(mod_pulse[event][cell][:baseline_sampling_factor]) , fix = debugging_bool ))
        
        if event+1 !=1001:
            bar_length = 40
            progress = min((event+1) / 1000, 1.0)
            block = int(bar_length * progress)
            print(f"\rProgress: [{'#' * block}{'-' * (bar_length - block)}] {event+1}/1000 ", end='', flush=True)
        
    print( "finishing peak interpolation")




def Clear_Peak(pulse: np.array , err):
    """
    Returns the minimum value (peak) and its local standard deviation.

    Parameters
    ----------
    pulse : np.array
        Input pulse array.

    Returns
    -------
    peak_value : float
        Value of the peak.
    ipeak : int
        Index of the peak.
    """
    ipeak = pulse.tolist().index(min(pulse))
    # print( err , "ERROR CLEAN PEAK")
    return [pulse[ipeak], ipeak , err , ipeak]


def Find_Peak(pulse: np.array , base_err , parabolic_fit_range_1 = parabolic_fit_range , fix = False , consistent = False , prev_peak = []):
    """
    Fits a parabola to the peak region of the pulse.

    Parameters
    ----------
    pulse : np.array
        Input pulse array.

    Returns
    -------
    peak_value : float
        Fitted peak value or 0 if fit fails.
    peak_index : int
        Fitted peak index or 0 if fit fails.
    """
    ipeak = pulse.tolist().index(min(pulse))
    tmpeak = pulse.tolist().index(min(pulse))
    # Define interpolation variables for parabola fit
    x = np.arange(max(ipeak - parabolic_fit_range_1  , 0), min(ipeak + parabolic_fit_range_1 , len(pulse)))
    y = pulse[max(ipeak - parabolic_fit_range_1 , 0):min(ipeak + parabolic_fit_range_1, len(pulse))]
    y_err = base_err * np.ones_like(y)

    close_peak = y
    pop, _ = curve_fit(model_parabola, x, close_peak, [0.001, 0.001, pulse[ipeak]], y_err)
    ls = LeastSquares(x, close_peak, y_err, model_parabola)
    m = Minuit(ls, a=pop[0], b=pop[1], c=pop[2])
    m.limits["a"] = (0.000001 , None)
    m.migrad(ncall=1000)
    err = np.sqrt(np.power(m.values[1]*m.covariance[0][0] , 2) - 2*m.values[0]*m.values[1]*np.power(m.covariance[0][1] , 2) + np.power( m.covariance[1][1]*m.values[0] , 2)/np.power(m.values[0] , 4))/2
    ipeak = m.values[1] / (2 * m.values[0])
    peak_val = model_parabola( ipeak , *m.values)
    return [peak_val, round(ipeak) , err , ipeak]



def model_parabola(x, a, b, c):
    """
    Parabolic model function for curve fitting.

    Parameters
    ----------
    x : float or np.ndarray
        Input value(s).
    a : float
        Quadratic coefficient.
    b : float
        Linear coefficient.
    c : float
        Constant term.

    Returns
    -------
    float or np.ndarray
        Evaluated parabola at x.
    """
    return a * x**2 + b * x + c

#______________________________________________________________________________________________________________________________________
#
#--------------------------------------------------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------------------------------------------
#______________________________________________________________________________________________________________________________________
#

if __name__ == "__main__":
    warnings.simplefilter("always")

    os.makedirs( risetime_fig_path , exist_ok=True)
    os.makedirs( peak_fig_path , exist_ok=True)
    os.makedirs( interpolated_fig_path , exist_ok=True)
    print("Opening file:", input_file)
    mod_pulse = MergeGroupd_convertion(input_file)
    # mod_pulse = OutGroupd_convertion( input_dir)


    # Separate empty and signal channels
    noise_channels = mod_pulse[:, :16]
    signal_pulse = mod_pulse[:, 16:]
    data = [copy.deepcopy(struct) for _ in range(len(signal_pulse))]
    



    # Analyze selected pulses
    data_analysis(signal_pulse, data)
    sum_list = []
    for event in range(len(signal_pulse)):
        peak_val = 0
        for cell in range(16):
            peak_val += data[event]["peak"][cell][0]
            print( peak_val)
        sum_list.append(peak_val)
    
    
    # Remove all sum_list values greater than 1000
    filtered_sum_list = sum_list

    mean_val = np.mean(filtered_sum_list)
    std_val = np.std(filtered_sum_list)
    ratio = std_val / mean_val if mean_val != 0 else 0

    plt.figure(figsize=(8, 6))
    plt.hist(filtered_sum_list, bins=50, histtype="step")
    plt.xlabel('Peak Value [sampling units]')
    plt.ylabel('Count')
    plt.title('peak distribution at 10GeV')
    plt.legend([f"mean={mean_val:.2f}, std={std_val:.2f}, ratio={ratio:.2f}"])
    print(os.path.join(peak_fig_path, f"sum_list_hist_{energy}GeV.pdf"))
    plt.savefig(os.path.join(peak_fig_path, f"sum_list_hist_{energy}GeV.pdf"))
    plt.show()





