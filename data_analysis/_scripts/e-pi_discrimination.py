import uproot
import numpy as np
import matplotlib.pyplot as plt
import os
from sys import argv

# Define start and end percentage for energy threshold
p_start = 10
p_end = 90

# Output directory for results
output_dir = "data_analysis/e_pi_disc"
# Check if threshold file already exists
threshold_exist = os.path.exists(output_dir + f"/end{p_end}%/threshold.csv")

# Default bounds for energy and risetime
r_bound = 1000
l_bound = 0
u_bound = 1000
d_bound = 0

# Number of bins for heatmap
x_len = 10
y_len = 10

def Resolution_convertion(path: str):
    """
    Reads ROOT file and extracts 'mod0_ph' and 'mod0_pulse' arrays from the tree.

    Parameters
    ----------
    path : str
        Path to the ROOT file.

    Returns
    -------
    risetime_diff : np.ndarray
        Difference in risetime between p_end and p_start.
    e_cell : list of np.ndarray
        List of energy arrays for each cell.
    e_tot : np.ndarray
        Array of total reconstructed energy.
    """
    file = uproot.open(path)
    t_res = file["time_resolution"]
    e_res = file["energy_resolution"]

    t_keys = t_res.keys()
    e_keys = e_res.keys()[1::]

    risetime = []
    # Extract risetime arrays for p_start and p_end
    for key in t_keys:
        if str(p_start) in key and not "error" in key:
            risetime.append(t_res[key].array(library="np"))
        if str(p_end) in key and not "error" in key:
            risetime.append(t_res[key].array(library="np"))
    # Extract total reconstructed energy
    e_tot = e_res["full_reconstructed_energy"].array(library="np")
    e_cell = []
    # Extract cell indices from keys
    cell = [int(key.split("_")[1]) for key in t_keys]
    # Ensure all risetime arrays are from the same cell
    if not all(x == cell[0] for x in cell):
        raise KeyError("not every raisetime is from the same cell")
    # Extract energy arrays for each cell
    for key in e_keys:
        e_cell.append(e_res[key].array(library="np"))
    # Return difference in risetime, cell energies, and total energy
    return risetime[1] - risetime[0], e_cell, e_tot

def significancy(n_e, n_pi):
    """
    Calculate significance for electron events.

    Parameters
    ----------
    n_e : int
        Number of electron events.
    n_pi : int
        Number of pion events.

    Returns
    -------
    float
        Significance value.
    """
    if n_e == 0: return 0
    return n_e / np.sqrt(n_e + n_pi)

def other_significancy(n_e, n_pi):
    """
    Calculate significance for pion events.

    Parameters
    ----------
    n_e : int
        Number of electron events.
    n_pi : int
        Number of pion events.

    Returns
    -------
    float
        Significance value.
    """
    if n_pi == 0: return 0
    return n_pi / np.sqrt(n_pi + n_e)

if __name__ == "__main__":
    # List all ROOT files for electrons
    files = os.listdir("root_resolution/slanted_e")

    # Create output directory if it doesn't exist
    os.makedirs(output_dir + f"/end{p_end}%", exist_ok=True)

    # Sort files by energy value
    files = sorted(files, key=lambda x: int(x.split(".")[0].removeprefix("resolution_")))

    # Extract starting energies from filenames
    starting_energy = np.array([int(file.split(".")[0].removeprefix("resolution_")) for file in files])
    for file in files:
        # Extract risetime and energy for electrons and pions
        r_e, cell_e, e_e = Resolution_convertion("root_resolution/slanted_e/" + file)
        r_pi, cell_pi, e_pi = Resolution_convertion("root_resolution/slanted_pi/" + file)
        energy = file.removeprefix("resolution_").removesuffix(".root")
        # If threshold file doesn't exist, write bounds for each energy
        if not threshold_exist:
            with open(output_dir + f"/end{p_end}%/threshold.csv", "a") as f:
                f.write("{0} , {1} , {2} , {3} , {4}\n".format(
                    min(e_e) * 0.99, min(r_e) * 0.99, max(e_e) * 1.01, max(r_e) * 1.01,
                    float(file.split(".")[0].removeprefix("resolution_"))
                ))

    for file in files:
        energy = file.removeprefix("resolution_").removesuffix(".root")
        # Extract risetime and energy for electrons and pions
        r_e, cell_e, e_e = Resolution_convertion("root_resolution/slanted_e/" + file)
        r_pi, cell_pi, e_pi = Resolution_convertion("root_resolution/slanted_pi/" + file)

        mask_e = r_e > 0
        mask_pi = r_pi > 0
        e_e = e_e[mask_e]
        r_e = r_e[mask_e]
        e_pi = e_pi[mask_pi]
        r_pi = r_pi[mask_pi]
        cell_e = [np.array(c)[mask_e] for c in cell_e]
        cell_pi = [np.array(c)[mask_pi] for c in cell_pi]

        # Sum energy over all cells for electrons
        sum_cell_e = []
        for i in range(len(cell_e[0])):
            sum = 0
            for j in range(len(cell_e)):
                sum += cell_e[j][i]
            sum_cell_e.append(sum)

        # Sum energy over all cells for pions
        sum_cell_pi = []
        for i in range(len(cell_pi[0])):
            sum = 0
            for j in range(len(cell_pi)):
                sum += cell_pi[j][i]
            sum_cell_pi.append(sum)

        # Convert energy and risetime to numpy arrays
        x_e = np.array(e_e)
        y_e = np.array(r_e)
        x_pi = np.array(e_pi)
        y_pi = np.array(r_pi)

        # Find common axis ranges for histograms
        x_min = min(x_e.min(), x_pi.min())
        x_max = max(x_e.max(), x_pi.max())
        y_min = min(y_e.min(), y_pi.min())
        y_max = max(y_e.max(), y_pi.max())

        # Calculate number of bins based on starting energy
        bins = int(round(100 * (1 - np.exp(-starting_energy[files.index(file)]))))
        x_bins = np.linspace(x_min, x_max, bins)
        y_bins = np.linspace(y_min, y_max, bins)

        # Create 2D histograms for electrons and pions
        heatmap_e, _, _ = np.histogram2d(x_e, y_e, bins=[x_bins, y_bins])
        heatmap_pi, _, _ = np.histogram2d(x_pi, y_pi, bins=[x_bins, y_bins])

        extent = [x_min, x_max, 0, y_max]

        # Plot heatmaps for electrons and pions
        fig, axs = plt.subplots(1, 2, figsize=(12, 5))

        # Electron heatmap
        axs[0].imshow(
            heatmap_e.T,
            extent=extent,
            origin='lower',
            aspect='auto',
            cmap='magma',           # Brighter colormap
            vmin=0,                 # Set minimum value
            vmax=heatmap_e.max() * 0.7  # Lower vmax to stretch colors
        )
        axs[0].set_xlabel("energia evento per elettrone")
        axs[0].set_ylabel("risetime")
        axs[0].set_title("electron distribution " + energy)
        fig.colorbar(axs[0].images[0], ax=axs[0], label='Counts')

        # Pion heatmap
        axs[1].imshow(
            heatmap_pi.T,
            extent=extent,
            origin='lower',
            aspect='auto',
            cmap='magma',           # Brighter colormap
            vmin=0,
            vmax=heatmap_pi.max() * 0.7
        )
        axs[1].set_xlabel("energia evento per pione")
        axs[1].set_ylabel("risetime")
        axs[1].set_title("pion distribution " + energy)
        fig.colorbar(axs[1].images[0], ax=axs[1], label='Counts')
        plt.tight_layout()

        # Save heatmap plots
        plt.savefig(output_dir + f"/end{p_end}%/{energy.removesuffix(".0GeV")}/e_pi_disc_{energy}.pdf")
        plt.clf()
        plt.close(fig)

        # Read threshold bounds from CSV file
        with open(output_dir + f"/end{p_end}%/threshold.csv", "r") as myfile:
            matrix = [list(map(float, line.strip().split(','))) for line in myfile if line.strip()]

        energies_idx = [matrix[i][-1] for i in range(len(matrix))]
        if float(file.split(".")[0].removeprefix("resolution_")) in energies_idx:
            idx = energies_idx.index(float(file.split(".")[0].removeprefix("resolution_")))
            l_bound = matrix[idx][0]
            d_bound = matrix[idx][1]
            r_bound = matrix[idx][2]
            u_bound = matrix[idx][3]

        # Create masks for selected bounds
        mask_e = (e_e >= l_bound) & (e_e <= r_bound) & (r_e >= d_bound) & (r_e <= u_bound)
        mask_pi = (e_pi >= l_bound) & (e_pi <= r_bound) & (r_pi >= d_bound) & (r_pi <= u_bound)

        # Slice data according to bounds
        sliced_e_e = e_e[mask_e]
        sliced_r_e = r_e[mask_e]
        sliced_e_pi = e_pi[mask_pi]
        sliced_r_pi = r_pi[mask_pi]

        # Plot scatter plots for all and sliced data
        fig, axs = plt.subplots(1, 2, figsize=(12, 5))

        # Left: all data
        axs[0].scatter(e_e, r_e, s=5, label='Electron', alpha=0.5)
        axs[0].scatter(e_pi, r_pi, s=5, label='Pion', alpha=0.5)
        # Draw rectangle for selected bounds
        rect = plt.Rectangle(
            (l_bound, d_bound),           # (x, y) lower left corner
            r_bound - l_bound,            # width
            u_bound - d_bound,            # height
            linewidth=2,
            edgecolor='red',
            facecolor='none',
            linestyle='--',
            label='Selected bounds'
        )
        axs[0].add_patch(rect)
        axs[0].set_xlabel("Energia evento")
        axs[0].set_ylabel("Risetime")
        axs[0].set_title(f"Scatter plot e/pi (all) {energy}")
        axs[0].legend()

        # Right: sliced data
        axs[1].scatter(sliced_e_e, sliced_r_e, s=5, label='Electron', alpha=0.7)
        axs[1].scatter(sliced_e_pi, sliced_r_pi, s=5, label='Pion', alpha=0.7)
        axs[1].set_xlabel("Energia evento")
        axs[1].set_ylabel("Risetime")
        axs[1].set_title(f"Scatter plot e/pi (cutted) {energy}")
        axs[1].legend()

        plt.tight_layout()
        # Save scatter plot
        plt.savefig(output_dir + f"/end{p_end}%/{energy.removesuffix(".0GeV")}/e_pi_scatter_{energy}.pdf")
        print(energy)
        plt.clf()
        plt.close()

    for file in files:
        energy = file.removeprefix("resolution_").removesuffix(".root")
        # Extract risetime and energy for electrons and pions
        r_e, cell_e, e_e = Resolution_convertion("root_resolution/slanted_e/" + file)
        r_pi, cell_pi, e_pi = Resolution_convertion("root_resolution/slanted_pi/" + file)

        # Read threshold bounds from CSV file
        with open(output_dir + f"/end{p_end}%/threshold.csv", "r") as myfile:
            matrix = [list(map(float, line.strip().split(','))) for line in myfile if line.strip()]

        energies_idx = [matrix[i][-1] for i in range(len(matrix))]
        if float(file.split(".")[0].removeprefix("resolution_")) in energies_idx:
            idx = energies_idx.index(float(file.split(".")[0].removeprefix("resolution_")))
            l_bound = matrix[idx][0]
            d_bound = matrix[idx][1]
            r_bound = matrix[idx][2]
            u_bound = matrix[idx][3]

        # Create matrix for significance values
        mat = np.zeros((x_len, y_len))
        # Create bin edges for energy and risetime
        x_index = [l_bound + (r_bound - l_bound) * i / x_len for i in range(x_len)]
        x_index.append(r_bound)
        y_index = [d_bound + (u_bound - d_bound) * i / x_len for i in range(y_len)]
        y_index.append(u_bound)

        # Calculate significance for each bin
        for x in range(x_len):
            for y in range(y_len):
                l_bound = x_index[x]
                r_bound = x_index[x + 1]
                d_bound = y_index[y]
                u_bound = y_index[y + 1]

                mask_e = (e_e >= l_bound) & (e_e <= r_bound) & (r_e >= d_bound) & (r_e <= u_bound)
                mask_pi = (e_pi >= l_bound) & (e_pi <= r_bound) & (r_pi >= d_bound) & (r_pi <= u_bound)

                sliced_e_e = e_e[mask_e]
                sliced_r_e = r_e[mask_e]
                sliced_e_pi = e_pi[mask_pi]
                sliced_r_pi = r_pi[mask_pi]

                n_e = len(sliced_e_e)
                n_pi = len(sliced_e_pi)
                mat[x][y] = significancy(n_e, n_pi)

        # Plot significance heatmap
        fig, ax = plt.subplots()
        im = ax.imshow(mat.T, origin='lower', aspect='auto', vmin=0, vmax=10)

        # Set ticks at the start and end, and evenly spaced
        xtick_positions = np.linspace(-0.5, x_len - 0.5, x_len + 1)
        ytick_positions = np.linspace(-0.5, y_len - 0.5, y_len + 1)
        ax.set_xticks(xtick_positions)
        ax.set_yticks(ytick_positions)
        ax.set_xticklabels([f"{x_index[i]:.2f}" for i in range(x_len + 1)], rotation=45)
        ax.set_yticklabels([f"{y_index[i]:.2f}" for i in range(y_len + 1)])

        ax.set_xlabel("Energy bins")
        ax.set_ylabel("Risetime bins")
        ax.set_title("electron distribution " + energy)
        fig.colorbar(im, ax=ax, label='significancy')
        plt.tight_layout()
        # Save significance heatmap
        plt.savefig(output_dir + f"/end{p_end}%/{energy.removesuffix(".0GeV")}/significancy{energy}.pdf")
        # plt.show()
        plt.clf()
        plt.close()
