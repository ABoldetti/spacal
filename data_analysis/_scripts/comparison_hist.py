import uproot
import numpy as np
import matplotlib.pyplot as plt

def compare_histograms(file1_path, hist1_name, output1):
    # Open ROOT files and get histograms
    with uproot.open(file1_path) as file1:
        tree1 = file1["tree"]
        hist1 = tree1[hist1_name]
        h1_values = hist1.array(library = "np")



    # Plot both histograms in the same figure but in 2 separated subplots
    # Calculate moments for first histogram
    mean1 = np.mean(h1_values)
    std1 = np.std(h1_values)
    ratio1 = std1 / mean1 if mean1 != 0 else np.nan

    fig, axs = plt.subplots(figsize=(8, 5))
    axs.hist(h1_values, bins=50, color='blue', histtype='step',
             label=f"Mean: {mean1:.2f}, Std: {std1:.2f}, Ratio: {ratio1:.3f}")
    axs.set_title("Integral distribution at 10GeV")
    axs.set_ylabel("Counts")
    axs.set_xlabel("Integral value [Vt]")
    axs.set_xlim(min(h1_values), max(h1_values))
    axs.legend()

    fig.tight_layout()
    fig.savefig(output1)
    plt.close(fig)





if __name__ == "__main__":
    # Example usage
    compare_histograms(
        "data_analysis/readout/slanted_e/10.0GeV.root", "mod0_cell22_reco_energy",
        "data_analysis/comparison/10GeV_hist1.pdf"
    )