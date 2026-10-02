import math
import os
import stat
import sys
import argparse
import subprocess
from subprocess import Popen, PIPE, STDOUT
import shutil
from shutil import copyfile


def main(args):
    
    crystal_inner_cladding_fraction   = 0.02
    crystal_outer_cladding_fraction   = 0.02
    esr_transmittance = 0              # probability for a optical photon to cross ESR - default = 0
    separation_thickness = 1           # ignored if cell_separation_type != 2
    separation_material  = 5           # ignored if cell_separation_type != 2. 5 = Aluminum

    ### user parameters
    # cry_size_x                    # crystal side in x [mm]
    # cry_air_layer                 # size of air gap between crystal and abs, on each side of the crystal [mm]
    # cry_pitch_x                   # pitch in x [mm]
    # n_cells_per_side              # n of cells per module in x and y direction
    # cry_n                         # n of crystals per cell in x and y direction
    # int_gap_mat                   # internal gap material 1 = air
    # cry_mat                       # crystal material 
    # cry_size_z                    # list of crystal lengths e.g. for front and back sections
    # cry_shape                     # 0 = squared, 1 = round. DEFAULT = 0. If = 1, cell_crystal_size_x interpreted as diameter (y is ignored)
    # hole_shape                    # 0 = squared, 1 = round. DEFAULT = 0. If = 1, cell_crystal_size_x interpreted as diameter (y is ignored)
    # cry_cladding                  # double cladding. 0 = no, 1 = yes
    # cell_separation_type          # 0 = nothing (air) - 1 = aluminization - 2 = reflector (esr)

    
    ##### W and GAGG (32 modules)
    ##### With longitudinal segmentation
    cry_size_x = 1.                
    cry_air_layer = 0.1            
    cry_pitch_x = 1.67             
    n_cells_per_side = 8         
    cry_n = 9                     
    int_gap_mat = 1              
    cry_mat = 8
    cry_size_z = [45,105]
    cry_shape    = 0          
    hole_shape   = 0          
    cry_cladding = 0          
    cell_separation_type = 2
    
    ##### W and GAGG (32 modules)
    ##### No longitudinal segmentation
    # cry_size_x = 1.                 
    # cry_air_layer = 0.1            
    # cry_pitch_x = 1.67            
    # n_cells_per_side = 8         
    # cry_n = 9                    
    # int_gap_mat = 1              
    # cry_mat = 8
    # cry_size_z = [150]
    # cry_shape    = 0         
    # hole_shape   = 0         
    # cry_cladding = 0         
    # cell_separation_type = 0   

    ##### Pb and Polystyrene (144 modules)
    ##### With longitudinal segmentation
    # cry_size_x = 1.               
    # cry_air_layer = 0.1           
    # cry_pitch_x = 1.67            
    # n_cells_per_side = 4           
    # cry_n = 18                    
    # int_gap_mat = 1               
    # cry_mat = 12
    # cry_size_z = [80,210]
    # cry_shape    = 1         
    # hole_shape   = 1         
    # cry_cladding = 1         
    # cell_separation_type = 2
    


    ### calculations
    
    # calc zpos to have the module centered
    sections = len(cry_size_z)
    if sections == 2:
      zpos = [-0.5*cry_size_z[1],0.5*cry_size_z[0]]
      cell_separator_position = -0.5*(cry_size_z[1]-cry_size_z[0])     # in mm
    else:
      zpos = [0]
      cell_separator_position = 0     # in mm
      cell_separation_type = 0 # force this
    cell_size = cry_n * cry_pitch_x # here we are assuming squared cells, please...
    cry_size_y = cry_size_x
    cry_pitch_y = cry_pitch_x

    cell_name  = []
    cell_pos_x = []
    cell_pos_y = []
    cell_pos_z = []
    cell_x_elements = []
    cell_y_elements = []
    cell_crystal_size_x = []
    cell_crystal_size_y = []
    cell_crystal_size_z = []
    cell_crystal_pitch_x = []
    cell_crystal_pitch_y = []
    cell_crystal_material = []
    cell_air_layer = []
    cell_int_gap_material = []
    cell_cry_shape    = []
    cell_hole_shape   = []
    cell_cry_cladding = []

    counter = 0
    # print("|", end = '')
    for k in range(sections):
        for i in range(n_cells_per_side):
            xpos = cell_size*i + cell_size/2.0 - cell_size*n_cells_per_side/2.0
            for j in range(n_cells_per_side):
                ypos = cell_size*j + cell_size/2.0 - cell_size*n_cells_per_side/2.0
                cell_name.append(str(counter))
                cell_pos_x.append(round(xpos,2))
                cell_pos_y.append(round(ypos,2))
                cell_pos_z.append(round(zpos[k],2))
                cell_x_elements.append(cry_n)
                cell_y_elements.append(cry_n)
                cell_crystal_size_x.append(cry_size_x)
                cell_crystal_size_y.append(cry_size_y)
                cell_crystal_size_z.append(cry_size_z[k])
                cell_crystal_pitch_x.append(cry_pitch_x)
                cell_crystal_pitch_y.append(cry_pitch_y)
                cell_crystal_material.append(cry_mat)
                cell_air_layer.append(cry_air_layer)
                cell_int_gap_material.append(int_gap_mat)
                cell_cry_shape   .append(cry_shape)
                cell_hole_shape  .append(hole_shape)
                cell_cry_cladding.append(cry_cladding)
                counter = counter + 1

    print("cell_name  = |", end = '')
    for i in cell_name:
        print("%s|" %i, end = '')
    print("")

    print("cell_pos_x  = |", end = '')
    for i in cell_pos_x:
        print("%.2f|" %i, end = '')
    print("")

    print("cell_pos_y  = |", end = '')
    for i in cell_pos_y:
        print("%.2f|" %i, end = '')
    print("")

    print("cell_pos_z  = |", end = '')
    for i in cell_pos_z:
        print("%.2f|" %i, end = '')
    print("")

    print("cell_x_elements  = |", end = '')
    for i in cell_x_elements:
        print("%d|" %i, end = '')
    print("")

    print("cell_y_elements  = |", end = '')
    for i in cell_y_elements:
        print("%d|" %i, end = '')
    print("")

    print("cell_crystal_size_x  = |", end = '')
    for i in cell_crystal_size_x:
        print("%.2f|" %i, end = '')
    print("")

    print("cell_crystal_size_y  = |", end = '')
    for i in cell_crystal_size_y:
        print("%.2f|" %i, end = '')
    print("")

    print("cell_crystal_size_z  = |", end = '')
    for i in cell_crystal_size_z:
        print("%.2f|" %i, end = '')
    print("")

    print("cell_crystal_pitch_x  = |", end = '')
    for i in cell_crystal_pitch_x:
        print("%.2f|" %i, end = '')
    print("")

    print("cell_crystal_pitch_y  = |", end = '')
    for i in cell_crystal_pitch_y:
        print("%.2f|" %i, end = '')
    print("")

    print("cell_crystal_material  = |", end = '')
    for i in cell_crystal_material:
        print("%d|" %i, end = '')
    print("")

    print("cell_air_layer  = |", end = '')
    for i in cell_air_layer:
        print("%.2f|" %i, end = '')
    print("")

    print("cell_int_gap_material  = |", end = '')
    for i in cell_int_gap_material:
        print("%d|" %i, end = '')
    print("")

    print("cell_crystal_shape  = |", end = '')
    for i in cell_cry_shape:
        print("%d|" %i, end = '')
    print("")

    print("cell_hole_shape  = |", end = '')
    for i in cell_hole_shape:
        print("%d|" %i, end = '')
    print("")

    print("cell_crystal_cladding  = |", end = '')
    for i in cell_cry_cladding:
        print("%d|" %i, end = '')
    print("")

    print("crystal_inner_cladding_fraction = %f" %crystal_inner_cladding_fraction)
    print("crystal_outer_cladding_fraction = %f" %crystal_outer_cladding_fraction)
    print("cell_separation_type    = %d" %cell_separation_type)
    print("cell_separator_position = %f" %cell_separator_position)
    print("esr_transmittance       = %f" %esr_transmittance)
    print("separation_thickness    = %f" %separation_thickness)
    print("separation_material     = %d" %separation_material)
    sys.exit()




if __name__ == "__main__":
    main(sys.argv[1:])
