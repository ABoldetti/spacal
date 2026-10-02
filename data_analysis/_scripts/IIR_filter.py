import uproot
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import lfilter

def Out_Groupd_convertion(path: str):
    """
    Reads ROOT file and extracts 'mod0_ph' and 'mod0_pulse' arrays from the tree.
    Returns:
        mod_ph: numpy array of photon counts
        mod_pulse: numpy array of pulse shapes
    """
    file = uproot.open(path)
    tree = file["tree"]
    mod_ph = tree["mod0_ph"].array(library="np")
    mod_pulse = tree["mod0_pulse"].array(library="np")

    mod_ph = [i for i in mod_ph]
    mod_ph = np.array(mod_ph)

    mod_pulse = [i for i in mod_pulse]
    mod_pulse = np.array(mod_pulse)
    
    return mod_ph, mod_pulse


def IIR_filter(pulse):
    return lfilter(filter_factors , 1 , np.array(pulse , dtype=np.float32))
n =100
filter_factors= np.ones(n)/n
normalization_factor = 1

if __name__ =="__main__":
    mod_ph , mod_pulse =Out_Groupd_convertion("big_data/1/100.0GeV/OutGroupd_0.root")
    for j in range(255):
        for i in range(16):
            print(i)
            min_idx = np.argmin(mod_pulse[j, i+16])
            plt.axvline(x=min_idx, color='r', linestyle='--')
            plt.plot( np.arange(0 , len(mod_pulse[j,i+16])),  mod_pulse[j][i+16] , color="green",  alpha = 0.1)

            filtered_signal = lfilter(filter_factors , 1,np.array(mod_pulse[j , i+16] , dtype=np.float32))
            plt.plot(np.arange(0 , len(mod_pulse[j,i+16])),  filtered_signal)
            plt.show()