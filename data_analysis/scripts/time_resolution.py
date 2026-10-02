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
input_file = argv[1] if len(argv)>1 else "compacted_data/slanted_e/100.0GeV/merge_Groupd.root"
# input_dir = input_file.removesuffix(input_file.split("/")[-1]).replace("compacted_data" , "big_data") if len(argv)>1 else "big_data/slanted_e/100.0GeV/"
output_file_path = argv[2].replace(".root" , ".csv") if len(argv) > 2 else None
root_path = argv[3] if len(argv) > 3 else None


energy = float(input_file.split("/")[-2].removesuffix("GeV"))

# fig paths
risetime_fig_path = f"fig/risetime/{energy}GeV/"
peak_fig_path = f"fig/peak/{energy}GeV/"


# interpolation/analysis variable
parabolic_fit_range = int(argv[4]) if len(argv) > 4 else 2  # n of elements to the left and the right to detect the peak(depends on the resolution of the data in input)
err_acceptability = float(argv[5]) if len(argv) > 5 else 5  # Number of sigmas for noise threshold for peak detection 
threshold_coefficient = float(argv[6]) if len(argv) > 6 else 0.0003 * (np.log2(energy) + 1) # threshold for the creation of new points in the risetime percentages. It serves as a starting point and as an additional threshold in case the scan doesn't detect any ideal point
baseline_sampling_factor = int(argv[7]) if len(argv) > 7 else 200  # Number of points taken for noise studies (this parameter is also taken as a barrier for the percentages selection)
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

def OutGroupd_convertion( path: str):
    ausy = []
    files = os.listdir(path)
    for i in files:
        if "OutGroupd" in i:
            ausy.append(MergeGroupd_convertion( path + i))
    return np.concatenate(ausy)

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

def IIR_filter(pulse):
    return lfilter(filter_factors , 1 , np.array(pulse , dtype=np.float32))

def cell_selection( mod_pulse, data):
    for event in range(len(mod_pulse)):
        for cell in range(16):
            mean, std = Noise( mod_pulse[event , cell])
            f_function =IIR_filter(mod_pulse[event , cell])
            f_min = min(f_function)
            if (np.abs(mean - f_min)> err_acceptability*std): data[event]["cell considered"].append( cell )
            


def data_analysis(mod_pulse, data):
    print( "starting peak interpolation")
    for event in range(len(mod_pulse)):
        cell = cell_considered
        # for cell in data[event]["cell considered"]:
        # Baseline calculation
        data[event]["baseline"].append((np.mean(mod_pulse[event][cell][:baseline_sampling_factor]), np.std(mod_pulse[event][cell][:baseline_sampling_factor])))
        # print( np.std(mod_pulse[event][cell][:baseline_sampling_factor]) , "ERROR BASELINE")
        debugging_bool = False
        
        # Peak analysis (clear or fit)
        
        # data[event]["peak"].append(Clear_Peak(mod_pulse[event][cell] , np.std(mod_pulse[event][cell][:baseline_sampling_factor])) if Check_Peak(mod_pulse[event][cell]) else Find_Peak(mod_pulse[event][cell] , np.std(mod_pulse[event][cell][:baseline_sampling_factor]) , fix = debugging_bool ))
        data[event]["peak"].append(Find_Peak(mod_pulse[event][cell] , np.std(mod_pulse[event][cell][:baseline_sampling_factor]) , fix = debugging_bool ))
        # plt.savefig(peak_fig_path + f"peak_{energy}GeV_{event}.jpeg")
        # plt.clf()
        # plt.close()
        if event+1 !=1001:
            bar_length = 40
            progress = min((event+1) / 1000, 1.0)
            block = int(bar_length * progress)
            print(f"\rProgress: [{'#' * block}{'-' * (bar_length - block)}] {event+1}/1000 ", end='', flush=True)
        
        
        # Calculate peak-to-baseline ratios at different percentages
        # data[event]["threshold"].append([data[event]["baseline"][-1][1]/5 , data[event]["baseline"][-1][1]/5])
        l_th = [[(data[event]["peak"][-1][0] - data[event]["baseline"][-1][0]) * i / 100,
                np.sqrt(np.power(data[event]["peak"][-1][2], 2) + np.power(data[event]["baseline"][-1][1], 2)) * i / 100]
            for i in range(10, 100, 10)]
        l_th.insert(0, [l_th[0][0]/5 , l_th[0][1]/5 ])
        # l_th.insert( 0 , [0 , 0])
        data[event]["threshold"].append(l_th)
        # print(np.sqrt(np.power(data[event]["peak"][-1][2] , 2) + np.power(data[event]["baseline"][-1][1] , 2))*0.5 , "ERROR THRESHOLD")

        data[event]["integral"].append( integral_calculation( mod_pulse[event][cell] , pulse_delimitation(mod_pulse[event][cell][:data[event]["peak"][-1][1]:] , data[event]["baseline"][-1][0]) , data[event]["peak"][-1][1]+pulse_delimitation(mod_pulse[event][cell][data[event]["peak"][-1][1]::] , data[event]["baseline"][-1][0] , sense=1)))
    print( "finishing peak interpolation")


def integral_calculation( pulse , start_index , end_index):
    return cumulative_trapezoid( pulse[start_index:end_index] )


def Check_Peak(pulse: np.array):
    """
    Checks if the peak is clear based on its deviation from the local mean.

    Parameters
    ----------
    pulse : np.array
        Input pulse array.

    Returns
    -------
    is_not_significant : bool
        True if the peak is not significant, else False.
    """
    ipeak = pulse.tolist().index(min(pulse))
    close_peak = pulse[max(ipeak - parabolic_fit_range, 0):min(ipeak + parabolic_fit_range, len(pulse)):]
    if abs(min(pulse)) > 100*np.std( pulse[:baseline_sampling_factor:]):
        return True
    return False


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
    m.migrad(ncall=400)



    if m.valid:
        ipeak = m.values[1] / (2 * m.values[0])
        peak_val = model_parabola( ipeak , *m.values)
        err = np.sqrt(np.power(m.values[1]*m.covariance[0][0] , 2) - 2*m.values[0]*m.values[1]*np.power(m.covariance[0][1] , 2) + np.power( m.covariance[1][1]*m.values[0] , 2)/np.power(m.values[0] , 4))/2
        x_err = err/np.abs(m.values[0]*ipeak - m.values[1])
        err = x_err
        
        if abs(ipeak - tmpeak) > parabolic_fit_range_1:
            if parabolic_fit_range_1 > len(pulse)/2:
                return Find_Peak( pulse , base_err*1.5 , fix = fix)
            # print( ipeak , tmpeak , parabolic_fit_range_1)
            return Find_Peak( pulse , base_err,  parabolic_fit_range_1+2 , fix = fix)
        
        # print( err , "ERROR FIND PEAK")
        # print( m.values[1] / (2 * m.values[0]) , "PEAK VALUE")
        if True:
            # plt.plot(pulse)
            # plt.plot(np.arange( tmpeak - parabolic_fit_range_1 - 3 , tmpeak + parabolic_fit_range_1 + 3) , pulse[tmpeak - parabolic_fit_range_1 - 3 : tmpeak + parabolic_fit_range_1 + 3 :])
            # plt.scatter(
            #     [ipeak, tmpeak],
            #     [peak_val, pulse[tmpeak]],
            #     color="red",
            #     s=100,
            #     label=f"ipeak=({ipeak:.2f},{peak_val:.2f})"
            # )
            # Fit_plot( x , y , y_err , m , model_parabola)
            ausy = 0

    
        
        if consistent:
            if abs(prev_peak[1] - ipeak) < 0.5:
                return [peak_val, round(ipeak) , err , ipeak]
            else: return Find_Peak( pulse , base_err , parabolic_fit_range_1= parabolic_fit_range_1+2 , fix = fix)
        else: 
            return Find_Peak( pulse , base_err , parabolic_fit_range_1= parabolic_fit_range_1+2 , fix = fix , consistent= True , prev_peak=[peak_val , ipeak])
    else:
        print( err)
        Fit_plot( np.arange(max(ipeak - parabolic_fit_range_1, 0), min(ipeak + parabolic_fit_range_1, len(pulse))) , close_peak , err , m ,  model_parabola)
        if parabolic_fit_range_1 < 30:
            return Find_Peak( pulse , base_err , parabolic_fit_range_1= parabolic_fit_range_1+2 , fix = fix)
        else: return Find_Peak( pulse , base_err*1.5 , fix = fix)

# incriminated code
def Risetime_detection(pulse: np.array, th: float , baseline: bool , fix: bool , peak , sense = 0):
    """
    Detects the risetime crossing a given threshold.

    Parameters
    ----------
    pulse : np.array
        Input pulse array.
    th : float
        Threshold value.

    Returns
    -------
    index : float or int
        Index where the pulse crosses the threshold.
    """
    norm_data = pulse[:list(pulse).index(min(pulse)):]

    index = list(norm_data).index(th) if th in norm_data else None
    if index is not None:
        return index
    
    
    threshold = threshold_coefficient
    if baseline:
        threshold = 50*threshold_coefficient
    base = risetime_interpolation
    std_dev = np.std(norm_data[:base:])
    pulse_val = []
    index_val = []
    while True:
        for el in range(len(norm_data) - 1, base, -1):

            
            
            if np.abs(norm_data[el] - th) < threshold and np.abs(norm_data[el - 1] - th) < threshold and (norm_data[el - 1] - th) * (norm_data[el] - th) < 0:
                interpolated = el - 1 + (th - norm_data[el - 1]) / (norm_data[el] - norm_data[el - 1])
                if baseline:
                    fig, (ax_main, ax_zoom) = plt.subplots(1, 2, figsize=(12, 5), gridspec_kw={'width_ratios': [2, 1]})
                
                    # Main plot: whole pulse
                    ax_main.plot(np.arange( len(pulse) ), pulse, label="Pulse")
                    ax_main.scatter([el, el-1 ], [norm_data[el], norm_data[el-1] ], color="red", s=100, label="Considered Points")
                    ax_main.scatter(
                        peak[0], peak[1], s=100, color="purple",
                        label=f"actual peak ({round(peak[0])}, {round(peak[1])})"
                    )
                    # Draw a horizontal line for the threshold, but only across the pulse region
                    ax_main.axhline(
                        th, xmin=0.6, xmax=0.8, linestyle="--", color="green", label="Threshold (th)"
                    )
                    ax_main.axhline(
                        th + threshold, xmin=0.6, xmax=0.8, linestyle="--", color="orange",
                        label="th + threshold"
                    )
                    ax_main.axhline(
                        th - threshold, xmin=0.6, xmax=0.8, linestyle="--", color="orange",
                        label="th - threshold"
                    )
                    x_intercept = el - 1 + (th - norm_data[el - 1]) / (
                        norm_data[el] - norm_data[el - 1]
                    )
                    ax_main.axvline(
                        x_intercept, linestyle="--", color="blue",
                        label=f"x = {x_intercept:.2f}"
                    )
                    ax_main.legend()
                    ax_main.set_title("Full Pulse")
                    ax_main.scatter(
                        interpolated, th, color="cyan", s=50,
                        label="interpolated point"
                    )
                    # Zoomed plot: region around crossing
                    zoom_range = np.arange(
                        max(el - 4, 0), min(el + 3, len(norm_data))
                    )
                    ax_zoom.plot(
                        zoom_range,
                        norm_data[max(el - 4, 0):min(el + 3, len(norm_data))],
                        label="Pulse"
                    )
                    # Only plot considered points if they're in the zoom range
                    for idx in [el, el - 1]:
                        ax_zoom.scatter(
                            idx, norm_data[idx], color="red", s=100,
                            label="Considered Points" if idx == el else ""
                        )
                    ax_zoom.scatter(
                        interpolated, th, color="cyan", s=50,
                        label="interpolated point"
                    )
                    ax_zoom.axhline(
                        th, linestyle="--", color="green", label="Threshold (th)"
                    )
                    ax_zoom.axhline(
                        th + threshold, linestyle="--", color="orange",
                        label="th + threshold"
                    )
                    ax_zoom.axhline(
                        th - threshold, linestyle="--", color="orange",
                        label="th - threshold"
                    )
                    ax_main.legend()
                
                

                # print( "interpolated works")
                return interpolated
                
                if el not in index_val:
                    pulse_val.append(norm_data[el])
                    index_val.append(el)
                if el-1 not in index_val:
                    pulse_val.append(norm_data[el-1])
                    index_val.append(el-1)

            if (norm_data[el] - th) > threshold + std_dev  and (norm_data[el - 1] - th) > threshold + std_dev and (norm_data[el - 2] - th) > threshold + std_dev:
                break
        if threshold > np.abs(min(norm_data)):
            base -= 4
            threshold = 0
        if len(pulse_val) != 0: 
            if len(pulse_val) == 2:
                interpolated = el - 1 + (th - norm_data[el - 1]) / (norm_data[el] - norm_data[el - 1])
                # print( "interpolated works")
                return interpolated
            print( "LINEAR" , baseline)
            return linear_fit( index_val , pulse_val , std_dev , th)
        threshold += threshold_coefficient

def exponential_fit( pulse , err , th):
    point = Risetime_detection( pulse , th)
    x = np.arange(int(np.floor(point)) , len(pulse)-15)
    y = pulse[int(np.floor(point)):-15:]
    y_err = err*np.ones_like( y )

    ls = LeastSquares( x , y , y_err , model_exp)
    m = Minuit( ls , A = 100 , tau = 0.15 , t0 = point)
    m.migrad( ncall=100000)
    print( m.values)
    print( m.values["A"])
    Fit_plot( x , y , y_err , m , model_exp)

    if m.valid:
        return m.values , m.covariance
    else:
        values , _ = curve_fit( model_exp , x , y , [1 , 1] , y_err)
        ls = LeastSquares( x , y , y_err , model_exp)
        m = Minuit( ls , A = values[0] , t = values[1])
        m.migrad( ncall=1000)
        return m.values , m.covariance
    
def linear_fit( x_arr , y_arr ,  err , th):

    ls = LeastSquares( x_arr , y_arr , err*np.ones_like( x_arr) , model_line)
    m = Minuit( ls , 1 , -1)
    m.migrad( ncall=1000)
    m.hesse()
    # Fit_plot( x_arr , y_arr , err*np.ones_like( x_arr) , m , model_line)
    interpolated = (th - m.values["q"])/m.values["m"]
    # print( interpolated , x_arr , "INTERPOLATION VALUES")
    if interpolated > max(x_arr):
            # print("Failed Linear Fit")
            print( np.mean(x_arr) , interpolated)
    if min(x_arr) < interpolated < max(x_arr):
        # print( "Working interpolation")
        return interpolated
    return np.mean( x_arr)
    
    


def threshold_with_exp_fit( values , covariance , th):
    return (np.log( th/values["A"])/values["tau"])-values["t0"] , np.mean(covariance)



def pulse_delimitation(pulse: np.array, th: float , sense = 0):

    """
    Delimits the position in a pulse array where the signal crosses a specified threshold.

    Parameters
    ----------
    pulse : np.array
        The input array representing the pulse signal.
    th : float
        The threshold value to detect the crossing point in the pulse.
    sense : int, optional
        Direction of search for the threshold crossing:
        - If 0 (default), searches backwards from the end of the array.
        - If non-zero, searches forwards from the start of the array.

    Returns
    -------
    int
        The index in the pulse array where the threshold crossing occurs.
        If no crossing is found, returns `baseline_sampling_factor`.

    Notes
    -----
    - Uses global variables `threshold_coefficient` and `baseline_sampling_factor` for thresholding logic.
    - If the threshold is found directly in the pulse, returns its index.
    - Otherwise, iteratively searches for the crossing point, adjusting the threshold and base as needed.
    - May plot the pulse for debugging if the threshold exceeds a certain value.

    """
    i = pulse.index(th) if th in pulse else None
    if type(i) == int:
        return i
    threshold = threshold_coefficient
    base = baseline_sampling_factor

    if sense:
        while True:
            for el in range(len(pulse)):
                if np.abs(pulse[el] - th) < threshold and np.abs(pulse[el - 1] - th) < threshold and (pulse[el - 1] - th) * (pulse[el] - th) < 0:
                    return el
                if (pulse[el] - th) > threshold and (pulse[el - 1] - th) > threshold and (pulse[el - 2] - th) > threshold:
                    break
            if threshold > 15: 
                plt.plot( pulse)
                plt.scatter( [el , el-1] , [pulse[el] , pulse[ el - 1 ]])
                plt.axhline( th , linestyle ="--" )
                plt.axhline( pulse[el]-threshold , linestyle ="--")
                plt.axhline( pulse[el] + threshold , linestyle ="--")
                plt.show()
            if threshold > np.abs(min(pulse)):
                base -= 1
                threshold = threshold_coefficient
            if base == 0:
                return baseline_sampling_factor
            threshold += threshold_coefficient
    else:
        while True:
            for el in range(len(pulse) - 1, base, -1):
                if np.abs(pulse[el] - th) < threshold and np.abs(pulse[el - 1] - th) < threshold and (pulse[el - 1] - th) * (pulse[el] - th) < 0:
                    return el
                if (pulse[el] - th) > threshold and (pulse[el - 1] - th) > threshold and (pulse[el - 2] - th) > threshold:
                    break
            if threshold > np.abs(min(pulse)):
                base -= 1
                threshold = threshold_coefficient
            if base == 0:
                return baseline_sampling_factor
            threshold += threshold_coefficient

def model_exp(x, A, tau , t0):
    """
    Exponential function for fitting.

    Parameters
    ----------
    x : array_like
        Input x values.
    A : float
        Amplitude parameter.
    t : float
        Exponential parameter.

    Returns
    -------
    y : array_like
        Output values.
    """
    return (1-np.exp(tau * (x - t0), dtype=np.float128)) * A

def model_line( x , m , q):
    return m*x +q

def  model_parabola(x, a, b, c):
    """
    Parabolic function for fitting.

    Parameters
    ----------
    x : array_like
        Input x values.
    a : float
        Quadratic coefficient.
    b : float
        Linear coefficient.
    c : float
        Constant term.

    Returns
    -------
    y : array_like
        Output values.
    """
    return a * np.power(x, 2) - b * x + c


def err_prop(a, b, sa, sb):
    """
    Error propagation for ratio a/b.

    Parameters
    ----------
    a : float
        Numerator.
    b : float
        Denominator.
    sa : float
        Error in numerator.
    sb : float
        Error in denominator.

    Returns
    -------
    error : float
        Propagated error.
    """
    return a / b * np.sqrt(np.power(sa, 2) / np.power(a, 2) + np.power(sb, 2) / np.power(b, 2))


def Fit_plot(x_fit, y_fit, y_err, m, func):
    """
    Plots the fit result.

    Parameters
    ----------
    x_fit : array_like
        X values for fit.
    y_fit : array_like
        Y values for fit.
    y_err : array_like
        Errors for Y values.
    m : Minuit
        Minuit fit object.
    func : callable
        Fit function.
    """
    x_fit = np.array( x_fit)
    y_fit = np.array( y_fit)
    y_err = np.array( y_err)
    plt.errorbar(x_fit, y_fit, yerr=y_err, fmt='o', label='Data')
    plt.plot(x_fit, func(x_fit, *m.values), label='Fit')
    plt.legend()


def Noise(pulse: np.array):
    """
    Calculates the mean and standard deviation of the baseline noise.

    Parameters
    ----------
    pulse : np.array
        Input pulse array.

    Returns
    -------
    mean : float
        Mean of the baseline noise.
    std : float
        Standard deviation of the baseline noise.
    """
    noise = pulse[:baseline_sampling_factor:]
    return np.mean(noise), np.std(noise)

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
    print("Opening file:", input_file)
    mod_pulse = MergeGroupd_convertion(input_file)
    # mod_pulse = OutGroupd_convertion( input_dir)

    # Separate empty and signal channels
    noise_channels = mod_pulse[:, :16]
    signal_pulse = mod_pulse[:, 16:]
    

    # Prepare data structure for each event
    data = [copy.deepcopy(struct) for _ in range(len(signal_pulse))]

    # Select cells with significant signal above noise
    # cell_selection(signal_pulse, data)

    # Analyze selected pulses
    data_analysis(signal_pulse, data)

    risetime_perc = []
    risetime_perc_err = []


    counter_events = 0
    print( "starting risetime detection")
    # incriminated code
    for event_idx in range(len(signal_pulse)):


        cell = cell_considered
        pulse = signal_pulse[event_idx][cell]
        baseline_mean = data[event_idx]["baseline"][0][0]
        peak_index = data[event_idx]["peak"][0][1]
        peak_value = data[event_idx]["peak"][0][0]
        peak_idx_real = data[event_idx]["peak"][0][3]
        peak_err_real = data[event_idx]["peak"][0][2]
        norm_data = np.array(pulse[:peak_index + 50] - baseline_mean)
        thresholds = data[event_idx]["threshold"][0]

        peak = [peak_idx_real , peak_value]
        risetime_list = []
        risetime_list_err = []

        counter_events += 1
        # Loading bar for every 1000 events
        if counter_events !=1001:
            bar_length = 40
            progress = min(counter_events / 1000, 1.0)
            block = int(bar_length * progress)
            print(f"\rProgress: [{'#' * block}{'-' * (bar_length - block)}] {counter_events}/1000 ", end='', flush=True)
        baseline_bool = True
        debugging_bool = False

        for i,stage in enumerate(thresholds):
            if i in [1 , len(thresholds) -1]:
                baseline_bool = True

            point= Risetime_detection(list(norm_data), stage[0] , baseline = baseline_bool , fix=debugging_bool , peak = peak)
            if baseline_bool:
                plt.savefig(risetime_fig_path+f"interpolation_{i}_{energy}GeV_{counter_events}.jpeg")
                plt.clf()
                plt.close()
            baseline_bool = False
            risetime_list.append(point)
            risetime_list_err.append(np.sqrt( np.power( data[event_idx]["baseline"][0][1] , 2) + np.power( stage[1] , 2)))


            # print( np.sqrt( np.power( data[event_idx]["baseline"][0][1] , 2) + np.power( stage[1] , 2)) , "ERROR ENDING")
        risetime_list.append(peak_idx_real)  # Add peak value
        risetime_list_err.append( peak_err_real )
        risetime_perc.append(risetime_list)
        risetime_perc_err.append(risetime_list_err)

    print("ending risetime detection")

    # Convert risetime data to float and prepare for CSV
    p_list = [[float(val) for val in event] for event in risetime_perc]
    err_list = [[float(val) for val in event] for event in risetime_perc_err]

    if output_file_path is not None:
        print("Writing data to CSV:", output_file_path)
        try:
            with open(output_file_path, "a") as myfile:
                for row in p_list:
                    myfile.write(','.join(str(x) for x in row) + '\n')
        except Exception:
            with open(output_file_path, "w") as myfile:
                for row in p_list:
                    myfile.write(','.join(str(x) for x in row) + '\n')

    
    
        print("Writing errors to CSV:", output_file_path.replace(".csv" , "err.csv"))
        try:
            with open(output_file_path.replace(".csv" , "err.csv"), "a") as myfile:
                for row in p_list:
                    myfile.write(','.join(str(x) for x in row) + '\n')
        except Exception:
            with open(output_file_path.replace(".csv" , "err.csv"), "w") as myfile:
                for row in p_list:
                    myfile.write(','.join(str(x) for x in row) + '\n')

    # Prepare ROOT output
    if root_path is not None:
        root_output_file = f"{root_path}/resolution_{energy}GeV.root"
        print("Writing data to ROOT file:", root_output_file)
        os.makedirs(root_path, exist_ok=True)

        output_root_file = ROOT.TFile(root_output_file, "UPDATE")
        tree = ROOT.TTree("time_resolution", "Time resolution results")

        # Remove existing tree if present
        with uproot.open(root_output_file) as f:
            for key in f.keys():
                if "time_resolution" in key:
                    output_root_file.Delete(key)

        n_events = len(risetime_perc)
        perc = len(risetime_perc[0])
        th_array = [array("f", [0]) for _ in range(perc)]
        th_err_array = [array("f", [0]) for _ in range(perc)]
        for i in range(perc):
            data_branch_name = f"cell_{cell_considered}_th_{(i)*10}%"
            data_branch_title = f"cell{cell_considered} threshold {(i)*10} index%\F"
            tree.Branch(data_branch_name, th_array[i], data_branch_title)
            err_branch_name = f"cell_{cell_considered}_th_{(i)*10}%_error"
            err_branch_title = f"cell{cell_considered} threshold {(i)*10} index error%\F"
            tree.Branch(err_branch_name, th_err_array[i], err_branch_title)
        for event in range(n_events):
            for th in range(perc):
                th_array[th][0] = risetime_perc[event][th]
                th_err_array[th][0] = risetime_perc_err[event][th]
            tree.Fill()

        output_root_file.Write()
        output_root_file.Close()

