import numpy as np
import uproot
import matplotlib.pyplot as plt

input_file = "compacted_data/slanted_pi/100.0GeV/merge_Groupd.root"

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


if __name__ == "__main__":
    mod_pulse = MergeGroupd_convertion(input_file)
    signal_pulse = mod_pulse[:, 16:]

    pulse = signal_pulse[1][5]
    plt.plot(pulse, color="grey")
    peak = np.min(pulse)
    baseline = np.max(pulse)
    ten_percent = 0.1 * peak
    ninety_percent = 0.9 * peak
    fifty_percent = 0.5 * peak

    # Find indices where pulse crosses 10% and 90% of peak (rising edge)
    idx_10 = np.argmax(pulse <= ten_percent)
    idx_90 = np.argmax(pulse <= ninety_percent)
    # find the sample just before and just after the 50% threshold crossing
    crossings = np.where(pulse <= fifty_percent)[0]
    if crossings.size > 0:
        idx_50_2 = int(crossings[0])                      # first sample at-or-below 50% (after crossing)
        idx_50 = int(idx_50_2 - 1) if idx_50_2 > 0 else 0  # sample just before crossing (clamped to 0)
    else:
        # fallback: use nearest sample to the threshold and its neighbor
        idx_50_2 = int(np.argmin(np.abs(pulse - fifty_percent)))
        idx_50 = int(idx_50_2 - 1) if idx_50_2 > 0 else idx_50_2

    # Draw horizontal lines only up to the crossing points
    plt.hlines(ten_percent, 0, idx_10, color='red', linestyle='--', label='10% of peak')
    plt.hlines(ninety_percent, 0, idx_90, color='red', linestyle='--', label='90% of peak')
    plt.hlines(fifty_percent, 0, idx_50, color='red', linestyle='--', label='50% of peak')

    plt.vlines(idx_10, np.max(pulse), ten_percent, color='blue', linestyle=':', label='10% crossing')
    plt.vlines(idx_50, np.max(pulse), fifty_percent, color='lightgrey', linestyle=':', label='50% crossing')
    plt.vlines(idx_90, np.max(pulse), ninety_percent, color='blue', linestyle=':', label='90% crossing')

    # Denote baseline
    plt.axhline(baseline, color='purple', linestyle='-', label='Baseline')
    plt.text(len(pulse) - 1, baseline, 'Baseline', va='bottom', ha='right', color='purple')

    # Denote peak with a circle
    peak_idx = np.argmin(pulse)
    plt.scatter(peak_idx, peak, color='orange', s=80, label='Peak', zorder=5)

    # Denote the dots used to calculate risetime (10% and 90% crossings) as empty circles
    plt.scatter(idx_10, pulse[idx_10], facecolors='none', edgecolors='red', s=60, zorder=6, label='10% crossing dot')
    plt.scatter([idx_50 , idx_50_2], [pulse[idx_50] , pulse[idx_50_2]], facecolors='none', edgecolors='grey', s=60, zorder=6, label='50% crossing dots')
    plt.scatter(idx_90, pulse[idx_90], facecolors='none', edgecolors='red', s=60, zorder=6, label='90% crossing dot')

    risetime = idx_90 - idx_10
    plt.text(idx_10 - 10 if idx_10 - 10 > 0 else 0, peak * 0.95, f'Risetime: {risetime}', ha='right', color='blue')

    plt.xlabel("Time [sampling units]")
    plt.ylabel("Voltage")
    plt.legend()
    plt.savefig("pulse_description.pdf")

