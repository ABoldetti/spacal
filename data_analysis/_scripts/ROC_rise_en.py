import uproot
import numpy as np
import matplotlib.pyplot as plt
import os
from sklearn.metrics import auc
from mpl_toolkits.mplot3d import Axes3D

# Initial parameters
p_start = 10
p_end = 90  


input_path = "/home/bobolde/coding/spacal/"
output_dir = "data_analysis/e_pi_disc"
threshold_exist = os.path.exists(output_dir + f"/end{p_end}%/threshold.csv")

# Default bounds for energy and risetime
r_bound = 1000
l_bound = 0
u_bound = 1000
d_bound = 0

x_sec = 10  
y_sec = 10  



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
    e_tot = e_res["full_reconstructed_energy"].array(library="np")
    e_cell = []
    cell = [int(key.split("_")[1]) for key in t_keys]
    if not all(x == cell[0] for x in cell):
        raise KeyError("not every raisetime is from the same cell")
    # Extract energy arrays for each cell
    for key in e_keys:
        e_cell.append(e_res[key].array(library="np"))
    
    return risetime[1] - risetime[0], e_cell, e_tot

def significancy(n_e, n_pi):
    """
    Calculates the significance for electron events.
    """
    if n_e == 0: return 0
    return n_e / np.sqrt(n_e + n_pi)

def other_significancy(n_e, n_pi):
    """
    Calculates the significance for pion events.
    """
    if n_pi == 0: return 0
    return n_pi / np.sqrt(n_pi + n_e)

def true_positive( frac , tot):
    return frac/tot


if __name__ == "__main__":
    # List all electron files
    files = os.listdir("root_resolution/slanted_e")

    # Create output directory if it doesn't exist
    os.makedirs(output_dir + f"/end{p_end}%", exist_ok=True)

    # Sort files by energy value
    files = sorted(files, key=lambda x: int(x.split(".")[0].removeprefix("resolution_")))

    # Extract starting energies from filenames
    starting_energy = np.array([int(file.split(".")[0].removeprefix("resolution_")) for file in files])


    for file in files:
        energy = file.removeprefix("resolution_").removesuffix(".root")
        r_e, cell_e, e_e = Resolution_convertion("root_resolution/slanted_e/" + file)
        r_pi, cell_pi, e_pi = Resolution_convertion("root_resolution/slanted_pi/" + file)


        # Read threshold values from CSV
        with open(output_dir + f"/end{p_end}%/threshold.csv", "r") as myfile:
            matrix = [list(map(float, line.strip().split(','))) for line in myfile if line.strip()]

        energies_idx = [matrix[i][-1] for i in range(len(matrix))]
        if float(file.split(".")[0].removeprefix("resolution_")) in energies_idx:
            idx = energies_idx.index(float(file.split(".")[0].removeprefix("resolution_")))
            l_bound = matrix[idx][0]
            d_bound = matrix[idx][1]
            r_bound = matrix[idx][2]
            u_bound = matrix[idx][3]

        # Apply threshold cuts to electron and pion data
        mask_e = (e_e >= l_bound) & (e_e <= r_bound) & (r_e >= d_bound) & (r_e <= u_bound)
        mask_pi = (e_pi >= l_bound) & (e_pi <= r_bound) & (r_pi >= d_bound) & (r_pi <= u_bound)

        sliced_e_e = e_e[mask_e]
        sliced_r_e = r_e[mask_e]
        sliced_e_pi = e_pi[mask_pi]
        sliced_r_pi = r_pi[mask_pi]

        # Initialize matrices to store counts
        count_e_matrix = np.zeros((x_sec, y_sec))
        count_pi_matrix = np.zeros((x_sec, y_sec))

        en_steps = np.linspace(l_bound, r_bound, x_sec)
        rt_steps = np.linspace(d_bound, u_bound, y_sec)

        true_pos = []
        false_pos = []

        for i, en in enumerate(en_steps):
            for j, rt in enumerate(rt_steps):
                mask_e = (sliced_e_e > en) & (sliced_r_e > rt)
                mask_pi = (sliced_e_pi > en) & (sliced_r_pi > rt)

                selected_e_e = sliced_e_e[mask_e]
                selected_e_pi = sliced_e_pi[mask_pi]
                print( sliced_e_pi.size)
                print(energy)
                print( count_pi_matrix)


                count_e_matrix[i, j] = selected_e_e.size
                count_pi_matrix[i, j] = selected_e_pi.size
                true_pos.append( true_positive( selected_e_e.size , sliced_e_e.size))
                if sliced_e_pi.size != 0:
                    false_pos.append( true_positive( selected_e_pi.size , sliced_e_pi.size))
                else:
                    false_pos.append( 0)
                

        # Calculate true positive rate and false positive rate matrices
        true_positive_matrix = count_e_matrix / sliced_e_e.size
        if sliced_e_pi.size != 0:
            false_positive_matrix = count_pi_matrix / sliced_e_pi.size

        # Prepare meshgrid for plotting
        X, Y = np.meshgrid(np.linspace(0, 1, x_sec), np.linspace(0, 1, y_sec))
        Z = false_positive_matrix.T  # Transpose to match meshgrid shape
        auc_3d = np.trapezoid(np.trapezoid(Z, X[0]), Y[:,0])

        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        ax.plot_surface(X, Y, Z, cmap='viridis')

        # Rotate the plot for better visualization
        ax.view_init(elev=30, azim=-60)  # You can adjust elev and azim as needed

        ax.set_xlabel('True Positive Rate (X)')
        ax.set_ylabel('True Positive Rate (Y)')
        ax.set_zlabel('False Positive Rate (Z)')
        ax.set_title('3D ROC Surface ' + energy + f"\nAUC: {auc_3d}")

        # plt.show()
        plt.savefig(f"data_analysis/e_pi_disc/ROC_risetime/ROC_2D_{energy}.pdf")

        # Sort true_pos and false_pos pairs by increasing true_pos
        sorted_pairs = sorted(zip(true_pos, false_pos), key=lambda x: x[1])
        true_pos, false_pos = zip(*sorted_pairs)

        if "100" in energy:
            print( false_pos)

        roc_auc = auc(false_pos, true_pos)
        plt.figure(figsize=(7, 5))
        plt.plot(false_pos, true_pos, marker='o', linestyle='-', label=f'Energy {energy} (AUC={roc_auc:.3f})')
        plt.plot([0, 1], [0, 1], color='gray', linestyle='--', label='Random (AUC=0.5)')
        plt.xlabel('False Positive Rate')
        plt.ylabel('True Positive Rate')
        plt.title(f'ROC Curve for electrons at {energy}')
        plt.legend()
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.tight_layout()
        plt.savefig(input_path + "data_analysis/e_pi_disc/ROC_risetime/ROC_1D_"+ energy + ".pdf")
        # plt.show()
        plt.clf()
        plt.close()

        
                
