# 1. Single module simulation

This section will explain how to prepare and run a single module simulation. This type of study is mainly meant to explore in detail the **performance** of new detector technologies. 

First of all, some very important messages: 

- This tutorial will show how to build a **SPACAL** module from ground up, but remember that we can simulate **SHASHLIK** modules just as well, and we will in fact include them in the full ECAL simulations later
- We will not have time to show all the **possible options** of the toolkit. If you start working with the HybridMC, you will gradually find them out either in the documentation, or by asking advice to the developers.


## 1.1 First run


Just to help make things easier, let's define a useful **terminal variable** to quickly locate the folder where you downloaded the simulation code. E.g., for my laptop this would be

```
SPACAL=/home/marco/cernbox/Universita/LHCb/Simulations/Spacal/
```

The simulation executable is located in the build folder `$SPACAL/build/FibresCalo`. You can run locally the simulation in 5 modalities (they are explained automatically if you run FibresCalo without arguments):

1. **Visualization only**:

`$SPACAL/build/FibresCalo <configuration file>`

2. **Standard exec**:

`$SPACAL/build/FibresCalo <configuration file> <output file>`

This modality will use the GPS file specified in the configuration file, at the key "gps_instructions_file".

3. **Exec with GPS**:

`$SPACAL/build/FibresCalo <configuration file> <output file> <gps file>`

This modality will use the GPS file specified in the command line argument `<gps file>`, ignoring the key "gps_instructions_file" written in the configuration file.

4. **Exec with GPS, and manually setting random seed**:

`$SPACAL/build/FibresCalo <configuration file> <output file without extension> <gps file> <random seed>`

This modality will use the GPS file specified in the command line argument `<gps file>`, ignoring the key "gps_instructions_file" written in the configuration file, and will also set the seed for random generator to the value specified by the user with the last command line argument.

5. **Exec with GPS, and manually setting random seed and flux**:

`$SPACAL/build/FibresCalo <configuration file> <output file without extension> <gps file> <random seed> <flux file>`

This modality will use as particle source the flux file specified by `<flux file>`. The `<gps file>` can be a simple text file with just one line, i.e. `/run/beamOn 1`. The program will also set the seed for random generator to the value specified by the user in `<random seed>`. 



## 1.2 Appetizer: a full study in a few commands 

Most of the times, running a full study on a prototype module using the Hybrid-MC framework is a matter of **just a few commands**. We will go deeper into the details of configuration files in a moment, but for now let's just jump into the action. We start by copying this tutorial folder somewhere on our PC  

```
cd
cp -r $SPACAL/documentation/Tutorial/1.SingleModuleStudy . 
cd 1.SingleModuleStudy
```

Here we have a folder `FullStudy`, that contains 2 sub folders

```
FullStudy/
├── OpticalCalibration
│   ├── base.cfg
│   └── optical_calibration.sh
└── SingleModuleStudy
    ├── base.cfg
    ├── gps_e_3+3.mac
    ├── prepare.sh
    └── SignalConfigFile_HPKR7600U-20_FL1_CFD02.cfg
```
As you can see, this is just some configuration files and a couple of bash scripts (notice that the `base.cfg` file is the same in both folders, here it's just copied twice for convenience). Full studies in general are performed on a computing cluster, and we will execute this one on **LXPLUS**. Let's copy these 2 folders somewhere on our AFS space. For me, for example:

```
cd FullStudy
scp -r OpticalCalibration SingleModuleStudy lxplus:/afs/cern.ch/work/m/mpizzich/simulations/jobs/Tutorial/
```

Then let's access LXPLUS, and go to the folder where we just copied the files

```
ssh lxplus
cd /afs/cern.ch/work/m/mpizzich/simulations/jobs/Tutorial/
```

We will now quickly submit a full study. You could do the same, but if you wish to, **wait for the end of this tutorial**: the 2 bash scripts mentioned above contain a couple of parameters that are set for my LXPLUS configuration, and you will learn how to adapt them to your during the course of this tutorial.

### Optical Calibration
 
We start the Optical Calibration with 

```
cd OpticalCalibration
source optical_calibration.sh
./runAll_jobs.sh
```

This prepares **1000 jobs** to be executed via HTCondor to LXPLUS, and then submits them. The jobs are all identical (that is, except for the random seed), so it won't matter if some of them fail, it will just reduce your statistics.

Now we wait for them to finish. 

When all jobs are completed, first we check if any output file is corrupted. This is not mandatory, but sometimes the next step might file if a file *particularly* corrupted is present. To do that, we move to the folder where output files have been saved, and delete very small files

```
cd /eos/experiment/spacal/Simulations/Tutorial/OpticalCalibration
find -name "*.root" -type 'f' -size -5k -delete
```

Now we merge the output files and create the **calibration file**. This is done via another single job, that we prepare using the script `optical_merge.sh` in the same folder from where we created and submitted the previuos jobs

```
cd -
./optical_merge.sh $SPACAL /eos/experiment/spacal/Simulations/Tutorial/OpticalCalibration/ 10 200 10
cd MergeOptical_10_200_10/
condor_submit jobs.sub
```
where `$SPACAL` is the variable defined above, `/eos/experiment/spacal/Simulations/Tutorial/OpticalCalibration` is the folder where the output files are stored, and the 3 following numbers define the binning of the PFDs that are built in the merging process.  

The optical calibration data will be saved in the output file, `/eos/experiment/spacal/Simulations/Tutorial/OpticalCalibration/calibration_10_200_10.data`.

Keep in mind that this entire Optical Calibration step doesn't have to be repeated: if you wish to perform other studies on this module configuration, or include this module in a full ECAL simulation, the Optical Calibration file remains valid.

### Module Study

We can now prepare and submit the full module study with 

```
cd /afs/cern.ch/work/m/mpizzich/simulations/jobs/Tutorial/SingleModuleStudy
./prepare.sh lxplus pgun
./runAll_jobs_full.sh
```

A new sub folder will be created in the current directory, `jobs`: this contains all the **HTCondor jobs** folders automatically prepared. The last command automatically submits everything to the cluster.

So while we wait for the jobs to be completed, a beam of 1000 electrons will be sent to a 12.12x12x12 cm^2 **longitudinally split SPACAL module** made of a **Tungsten** absorber and **GAGG** crystals, for each of the energies in this list [GeV]:

```
1 2 5 10 20 35 50 100
```
The pulses generated for each of the **128 detector channels** of the module will be recorded for each electron event, and the result analyzed (we'll see this part later).

This will take some time (again about 1-2 hours). Once this will be done, we will have the entire dataset ready for analysis in `/afs/cern.ch/work/m/mpizzich/simulations/jobs/Tutorial/SingleModuleStudy`. 

### Data analysis

Everyone can of course write their own analysis code on the output files. We have prepared some programs for this, that you can use to understand how to handle the output data formats. We will see this later, but in fact, we will just run one command and get (among others) these plots:

![Alt text](Images/image_015.png?raw=true "Title")
![Alt text](Images/image_016.png?raw=true "Title")

But let's now stop here, and go back to the fundamentals of the Hybrid-MC framework to understand how we have set up such a study.

## 1.3 Hybrid-MC from the ground up

Let's now see how to go from the preparation of a module configuration file to the production of energy resolution and timing resolution plots.

We go back to our local PC, and we start from a simple configuration file, `base.cfg`, the one in this folder (`documentation/Tutorial/1.SingleModuleStudy/base.cfg`). Let's visualize immediately the module described by this configuration file. Run

```
$SPACAL/build/FibresCalo base.cfg
```

You should see something like this, after some rotation:

![Alt text](Images/image_001.png?raw=true "Title")

Let's see how we obtained this module, and how to modify it.

### 1.3.1 General parameters

Open `base.cfg` with a text editor. As you can see, configuration files in our toolkit are just simple text files, with lots of comments (comments start with a `#` character). Keep in mind that all the possible configuration parameters that you can use in these files are documented in:

```
documentation/Parameters/Configuration_parameters.md
```

The first key to set is 

```
technology = 0         
```

This selects the **module technology type**, which for the moment can be either SPACAL (`technology = 0`) or SHASHLIK (`technology = 1`). In this example we will focus on a SPACAL module, hence the choice. Anyway, just for fun try to change this key in 

```
technology = 1         
```

You will see something like this:

![Alt text](Images/image_018.png?raw=true "Title")

For the sake of this tutorial, let's change back `technology` to 0, and move on. 

Afterwards, you can choose the **simulation type**. As explained in the comments

```
[...]
## The simulation types are:
## 0) only energy deposition
## 1) full ray tracing
## 2) hybrid simulation
## 3) optical calibration
```

In general we will perform hybrid simulations, so

```
simulationType = 2
```

Next, we choose the **particle source type**, i.e. the method to shoot particles into the module. For single module studies, the most convenient way is to use the Geant4 General Particle Source (GPS) method. As you will see, this is just a text file with some macro commands that defines the incident beam. We select this method and the GPS file by setting 

```
useGPS      = true
gps_instructions_file = gps_e_3+3.mac
```

In practice, you already saw that the GPS file can be passed directly from command line, which is much more convenient in a lot of use cases. For anyway these keys can stay like this.

Now we can have a look at the **visualization options**. These are relevant only for the *viz modality* that we just performed, and control which types of volumes are visualized. At the moment, all volumes are ON, for the sake of this tutorial, but you will learn quickly that as the number of crystals in a module grows, visualizing all elements becomes too heavy on the PC resources. 

Next section controls what the simulation writes in **output** file. These parameters are actually overridden by the key `simulationType`, if that is given, so we can safely ignore them.


### 1.3.2 Module geometry

Next we start the definition of our module. In the configuration file you will find a long description of how a calorimeter is created in our simulation, but this will become relevant later. For the moment, just keep in mind that we are describing a single SPACAL module here. Jump to the section

```
#####################
### SPACAL MODULE
#####################
```
Given the symmetry of SPACAL, we have found convenient to arrange the modules as made by 5 big blocks, that are placed next to each other along the z direction (so the x-y plane is representing the module section):

```
#
#   |         |           |          |           |         |
#   | READOUT | INTERFACE | ABSORBER | INTERFACE | READOUT |
#   |         |           |          |           |         |
# -----------------------------------------------------------------> z
#
```
The `ABSORBER` is the actual SPACAL module, and is surrounded by two `INTERFACE` volumes, one in the front and one in the back, that connect it to the two `READOUT` volumes. The section of these volumes is computed automatically on the basis of the absorber section, while the thickness has to be provided:

```
interface_length = 10 # in mm
readout_length = 5 # in mm
```
As you can imagine, the readout volumes are meant to host the PMTs, if one wants to include them in the simulation. The interface volumes will host instead everything that stands between the SPACAL module and the PMTs. 

Because of how the HybridMC is developed, whatever is outside of the module is irrelevant (at least for the light propagation, but it can have an impact on the incident particle beam). Therefore, the default option will build readout and interfaces as simple volumes of air. 

We can now define the absorber:

```
## ABSORBER
# The absorber volume. these options are self explanatory
absorber_name     = abs_one
absorber_size_x   = 121.2
absorber_size_y   = 121.2
absorber_size_z   = 150.
absorber_pos_x    = 0.
absorber_pos_y    = 0.
absorber_pos_z    = 0.
absorber_material = 8
```

This is a simple box, placed in the center of the calorimeter volume. Dimensions and positions are in mm, as it is always the case in the HybridMC. The last parameter specifies the absorber material. A list of possible materials can be found just above this section. Our choice for this module is pure Tungsten, with 19.1 g/cm^3 density. 

Next, we define the properties of the internal surface of the absorber in terms of reflectivity. These parameters are needed by the Geant4 Unified Model for optical surfaces. If you are curious about it, you can for example have a look at [these slides](https://indico.cern.ch/event/789510/contributions/3279418/attachments/1818134/2972494/AH_OpticalPhotons_slides.pdf). Anyway, we consider these parameters to describe roughly the surface state of the Tungsten material used for the SPACAL modules produced for our test beam experiments. 

We are now at the definition of cells. In our simulation, a *cell* is the fundamental unit of the readout chain. Basically, a cell corresponds to a readout channel. Even if there are no real readout channels in the simulation (like we said, we don't include any light guide or PMT..), the logic division in cells is still useful for the various steps of the HybridMC chain. 

Fundamentally, a cell is just a collection of holes in an absorber. These holes are filled with crystals (with some air gaps). An absorber can contain one or more cells. Here it is worth to report the detailed explanation of each parameter. Read the rest of the comments in `base.cfg` to get more info on materials etc. 

```
# cell_name                         # name of the cell
# cell_pos_x                        # cell center position in x [mm]
# cell_pos_y                        # cell center position in y [mm]
# cell_pos_z                        # cell center position in z [mm]
# cell_x_elements                   # number of elements within the cell, in x direction. An element is a hole filled with a crystal
# cell_y_elements                   # number of elements within the cell, in y direction. An element is a hole filled with a crystal
# cell_crystal_size_x               # crystal size for this cell, in x [mm]
# cell_crystal_size_y               # crystal size for this cell, in y [mm]
# cell_crystal_size_z               # crystal size for this cell, in z [mm]
# cell_crystal_pitch_x              # pitch between crystals in this cell, in x [mm]
# cell_crystal_pitch_y              # pitch between crystals in this cell, in x [mm]
# cell_crystal_material             # pitch between crystals in this cell, in x [mm]
# cell_air_layer                    # thickness of air gap between a crystal the absorber wall [mm]. This is meant per side
# cell_crystal_shape                # shape of crystal section. 0 = rectangular, 1 round 
# cell_hole_shape                   # shape of hole section. 0 = rectangular, 1 round 
# cell_crystal_cladding             # presence of cladding. 0 = no, 1 = yes
# crystal_inner_cladding_fraction   # thickness of internal cladding layer, in fraction of total diameter 
# crystal_outer_cladding_fraction   # thickness of outer cladding layer, in fraction of total diameter
# cell_int_gap_material             # material . 1 = air, 2 = optical grease
# cell_separation_type              # 0 = nothing (air) - 1 = aluminization - 2 = reflector (esr)
# cell_separator_position = -30.    # in mm
# esr_transmittance = 0             # probability for a optical photon to cross ESR - default = 0
# separation_thickness = 1          # ignored if cell_separation_type != 2
# separation_material  = 5          # ignored if cell_separation_type != 2
```

The parameters that produce the module you are visualizing are the following:

```
####################
####################
cell_name  = |0|
cell_pos_x  = |0.00|
cell_pos_y  = |0.00|
cell_pos_z  = |0.00|
cell_x_elements  = |9|
cell_y_elements  = |9|
cell_crystal_size_x  = |1.00|
cell_crystal_size_y  = |1.00|
cell_crystal_size_z  = |150.00|
cell_crystal_pitch_x  = |1.67|
cell_crystal_pitch_y  = |1.67|
cell_crystal_material  = |8|
cell_air_layer  = |0.10|
cell_int_gap_material  = |1|
cell_crystal_shape  = |0|
cell_hole_shape  = |0|
cell_crystal_cladding  = |0|
crystal_inner_cladding_fraction = 0.020000
crystal_outer_cladding_fraction = 0.020000
cell_separation_type    = 0
cell_separator_position = 0.000000
esr_transmittance       = 0.000000
separation_thickness    = 0.000000
separation_material     = 5
####################
####################
```

The parameters that you see written between `||` are in fact lists of values. The various cells are described by each entry in these lists, and all these list needs to be of the same length. 

**Be careful!** It is your responsibility to ensure that the crystals are not too long or too short, and that they are placed in the right positions, with respect to the absorber! In other words, if for example the absorber length here was set to 160 mm, the crystal would be too short and no optical photon would ever emerge from them! 

Before moving on with the remaining parameters, let's play a bit with the cell definition to understand how to set up different type of modules. The module we defined has just 1 cell, made of 9x9 crystals, with no longitudinal separation. We can obtain a longitudinal separation for example by defining another cell, placed in the same x-y coordinates. By carefully choosing the z positions of these two cells, we can obtain a properly segmented module. 

Modify the parameters reported above as follows:

```
####################
####################
cell_name  = |0|1|
cell_pos_x  = |0.00|0.00|
cell_pos_y  = |0.00|0.00|
cell_pos_z  = |-52.50|22.50|
cell_x_elements  = |9|9|
cell_y_elements  = |9|9|
cell_crystal_size_x  = |1.00|1.00|
cell_crystal_size_y  = |1.00|1.00|
cell_crystal_size_z  = |45.00|105.00|
cell_crystal_pitch_x  = |1.67|1.67|
cell_crystal_pitch_y  = |1.67|1.67|
cell_crystal_material  = |8|8|
cell_air_layer  = |0.10|0.10|
cell_int_gap_material  = |1|1|
cell_crystal_shape  = |0|0|
cell_hole_shape  = |0|0|
cell_crystal_cladding  = |0|0|
crystal_inner_cladding_fraction = 0.020000
crystal_outer_cladding_fraction = 0.020000
cell_separation_type    = 2
cell_separator_position = -30.000000
esr_transmittance       = 0.000000
separation_thickness    = 1.000000
separation_material     = 5
####################
####################
```

As you can see, we now have two cells defined. They are $45 mm$ and $105 mm$ long, placed in z = -52.50 mm and $z = 22.50 mm. We defined the separation as made an aluminum foil 1 mm thick. The optical separation between the two sections is simulated like an Enhanced Specular Reflector (ESR), with 100 percent reflectivity. The separation is placed at z=-30mm and this is done manually. It means that you actually need to get this number correct, exactly between the two sections, given dimensions and position. 

Run again the visualization mode:

![Alt text](Images/image_002.png?raw=true "Title")

As you can see, we have now two clearly separated sections. You might have a question, though: if the absorber length is set to 150 mm, and the crystals are 45+105 mm but separated by 1 mm, isn't the absorber too short? The answer is no, because whenever a `separation_thickness` is set, the `absorber_size_z` value is increased accordingly.

Before moving to the final module configuration, let's play a bit with some parameters. You will have noticed that crystals and holes can be defined both as circular or rectangular. If we modify these parameters

```
cell_crystal_material  = |12|12|
cell_crystal_shape  = |1|1|
cell_crystal_cladding  = |1|1|
```

We will get double cladded polystyrene fibers in squared holes:

![Alt text](Images/image_003.png?raw=true "Title")

Playing with the configuration file can become complicated, especially if you need to write manually the several tens of cells that compose a module. As you can imagine, the production of these cell parameters can be easily scripted. We wrote a small python script, `make_strings.py`, which you may find useful. Run it with

```
python3 make_strings.py
```

If you replace the cell configuration parameters with the output of this script, you will get a standard W+GAGG SPACAL module. Don't run the visualization mode just yet. 

First, take a look at the `make_strings.py`. There you will find comments to explain how to use it to prepare other modules, and also some example that would produce some typical SPACAL configurations. 

Now, if you try to visualize the module, you will notice that things get consistently slower. Unfortunately the Geant4 visualization can become very heavy for PCs when many volumes are created (it is anyway only meant for debugging). So before even trying, modify the visualization parameters by setting all the *Visibility* keys to 0 except `moduleVisibility` and `holeVisibility` (but leave `wireFrame = 1`! ). You will see this:

![Alt text](Images/image_004.png?raw=true "Title")

OK now we are almost ready to start the first simulation, but we still have a few parameters to explain. The first 2 concern the crystal scintillator optical properties. Most optical properties are of course written directly in the definition of each crystal. We let the user decide on the surface state of the scintillators. 

```
crystal_lateral_depolishing = 0.05
crystal_exit_depolishing    = 0.05
```

Again, the definition is a Geant4 technicality and we don't need to go into details here. For now, just know that these 2 parameters control how *depolished* the lateral and front/back (i.e. exit) surfaces of the scintillators are. The value reported here of 0.05 is a typical value used to simulate scintillators that look polished at naked eye, but that in fact are not well simulated by a perfect polishing condition (which can be chosen by commenting these keys, or setting them to 0). This is typical of inorganic scintillators. Plastic scintillators instead are well described by perfectly polished surfaces, and you will see that we defined them as such in the config files of Pb-Poly modules.

Next, the user can define a re-scaling of the bulk absorption length of the crystal. 

```
abs_length_scale_factor = 4       # multiply the abs length of the crystal material by a factor. - default = 1
```

To be clear, experimentally we cannot measure the *absorption length* alone of a material, but rather we evaluate the *attenuation length*, which is determined of course by the *absorption length*, but also by the crystal surface state, the wrapping condition, the type of optical coupling with the readout etc. With so many free parameters, at some point we need to manually scale at least one of them to match experimental measurements. This parameters let you scale the entire histogram that defines the *absorption length* of the material used as scintillator in this module. This combination of parameters is what we found to describe better the first set of measurements we perform at the beginning of SPACAL development. For the moment we still stick to these values, even if soon we will have much more measurements to refine this evaluation.

Finally, we are arrived to the last parameter to set. This is very important, and in fact deserves its own section.

#### 1.3.3 Photon logging

When (or where) is the information saved in our simulations? For the particle in the showers (i.e. all particle that deposit energy) the answer is *everywhere*. We save every single energy deposition event, wherever it happens in the simulation world. When it comes to optical photons, this is not the case: it would be pointless (and unfeasible) to log all the bounces of optical photons around the modules, so we define a very clear condition for logging them. Whenever an optical photon enters a specific volume, that we call `logging_volume`, it is killed and recorded. Optionally, the user can also decide to restrict the logging only to photons that enter the `logging_volume` coming from a specific volume, the `pre_volume`. This can be useful in some cases, but in general it is not used. Anyway, a `logging_volume` in our simulation is recognized as any volume whose name starts with a specific string:

```
################################################
# PHOTON LOGGING                               #
################################################
## keys to control at which position the optical photons are killed and recorded as "detected"
## Photons are considered detected if they enter the logging_volume
## and optionally the user can also impose that they have to be entering it coming from pre_volume
logging_volume         = Gap_Abs_Interface
# pre_volume             = crystal
```

As you know, in hybrid simulations we want to transports photons up to the moment when they exit the crystals going towards the detector volumes. Hence, we define the `logging_volume` as the volumes just next to the crystal exit faces. If you check carefully in the visualization mode, you will see that these volumes are called `Gap_Abs_Interface...`. 

It is important to underline here one thing. The name of the two volumes that corresponds to the condition `logging_volume = Gap_Abs_Interface` are 

```
Gap_Abs_Interface_Positive_Z_
Gap_Abs_Interface_Negative_Z_
```

The *Negative* and *Positive* part reflects the fact that if the module is centered in z = 0, one of these volumes will be in the negative part of the z axis, and the other in the positive part. This is important because it means that if we define `logging_volume = Gap_Abs_Interface` we will record photons **on both sides of the SPACAL module**. In other words, we are constructing a double readout module. This is of course what we want, since the module is longitudinally segmented. But what if we wanted to implement a non-segmented module, with single side readout? Logically, the solution is to specify the logging volume for example as

```
logging_volume  = Gap_Abs_Interface_Positive
```
This would record photons only when they exit from the positive z part of the module. But, of course, the photons exiting on the other side of the module would be lost! Just like in reality, to prevent this from happening we will place a mirror on the negative side of the module, with this key

```
esr_on_negative_exit = 1
```

You will see this implemented for example in the module of Run4 ECAL simulations. Obviously, single readout on the other side is also possible 

```
logging_volume  = Gap_Abs_Interface_Negative
esr_on_positive_exit = 1
```

but since in most configurations we shoot particles from negative z, in general we keep the readout on the opposite side of the incoming beam.

### 1.3.4 Shoot one particle

We can now shoot the first particle in the module, and see what happens. First we will have a quick look at the viz modality (for the last time), then we will move on to the more interesting theme of output files.

Modify the visualization by setting all the *Visibility* keys to 0 except `moduleVisibility` (but leave `wireFrame = 1`! ). Run the simulation in viz modality, and you will just see a box. 

Now open the GPS file, `gps_e_3+3.mac`. Copy all its content in the *Session* box, at the bottom of Geant4 GUI. Press enter to run it, and after a few second you will see something like this

![Alt text](Images/image_005.png?raw=true "Title")

This represents the shower particles (in yellow and red) and the optical photons, that as you can see propagate in the crystal fibers. These are just Cherenkov photons, as you know from the explanation of the HybridMC method. 

You can have a look at `gps_e_3+3.mac` to understand how the primary particle was generated. 

```
# Macro file for the
# initialization of G4GeneralParticleSource

/gps/particle e-

/gps/pos/type Plane
/gps/pos/shape Square
/gps/pos/centre -8.91 -8.91 -200  mm
/gps/pos/halfx 0.85  mm
/gps/pos/halfy 0.85  mm

# pointing, 3+3 degrees tilt
/gps/direction 0.052264 0.052264 0.997265

# run

/gps/energy 1 GeV
#/run/printProgress 1

/run/beamOn 1
```

Refer to the Geant4 General Particle Source documentation for details, but in any case this macro sets the particle to electrons, then defines a planar beam of squared shape, placed in a certain position and with given dimensions. Then it sets a beam direction, fixes the energy and shoots 1 particle.

### 1.3.5 Run a full simulation chain

We will now run a full simulation chain with the configuration files we have at hand. This will be a useful example of the step by step procedure of the HybridMC, although in reality afterwards most of the times you will not run the steps by hand, and also most likely not on your own PC.

#### Step 1. Geant4 simulation

The first logic step of an HybridMC consists in shooting some primary particle in a module, allowing the shower to deposit energy. At the same time, Cherenkov photons are generated and propagated, while scintillation photons are not. 

We already have everything in hand to perform this step (which actually just did in interactive mode). We just perform a small modification to make the output a bit more interesting. Modify the `gps_e_3+3.mac` file by replacing the last line with

```
/run/beamOn 5
```

We will shoot in total 8 electrons, 5 in the first Run, 3 in the second. Let's do it by running the command

```
$SPACAL/build/FibresCalo base.cfg out gps_e_3+3.mac
```

As you can see, we are using  the exec modality 3., by passing directly the GPS file by command line. After a few seconds, the output of this simulation is stored in the file `out.root`. Please keep in mind that the format of our output files (for the files produced in this step as well as in all other steps of the framework) a full documentation is available at:

```
documentation/OutputFiles/OutputFiles.md
```

Let's open `out.root` and take a look around:

![Alt text](Images/image_006.png?raw=true "Title")

Several `TTree`, some histogram and a folder are saved into this file. It's worth describing them in more details. Let's start with the most valuable ones
```
shower     -> TTree with energy depositions data
primaries  -> TTree with primary particles data
photons    -> TTree with optical photons data
LAPPD      -> TTree with LAPPD data
```

The first TTree, `shower`, contains the information on each energy deposition that happened during the simulation. That is, an entry is saved in this TTree every time that some energy is saved somewhere. Open it with ROOT

```
root -l out.root
```
then start a TBrowser and you will see *what* we save:

![Alt text](Images/image_007.png?raw=true "Title")


Besides information on the run and the event number (an event corresponds to one primary), this TTree has data on the type of particle that deposited energy, its position and momentum, the deposition time, the amount of energy and much more. 

The variable names are quite straightforward, but we refer you to the Output Files document for more details.

Just for fun, let's plot the shower shape of all 5 events

```
shower->Draw("z:x >> (500,-100,100,500,-100,100)","totalEnDep","COLZ")
```

![Alt text](Images/image_008.png?raw=true "Title")

You can clearly see how the module is split in 2 at z = -30 mm. 

The other interesting TTree is **photons**. It contains data on all the optical photons that reached the `logging_volume` defined above. 

![Alt text](Images/image_009.png?raw=true "Title")

Again, the variable names are quite straightforward, but we refer you to the Output Files documentation for more details. Same goes for the other contents of `out.root`.

#### Step 2. Optical calibration

In order to complete a full HybridMC chain, it is essential to perform a calibration of the module under study. As you know, this is a full ray tracing simulations where several point-like isotropic sources of optical photons are placed in a grid of points of a single scintillator of the module (or two scintillators in a longitudinally split module). This implies adapting the geometry that we just built, to reduce it to a single crystal module. 

But don't worry, you don't need to do it by hand! We wrote a program that take any module configuration file, and automatically produces an optical calibration configuration. On top of that, it also prepares all the folders and scripts to submit the entire calibration campaign (which will be split in several jobs, since as you can imagine is quite CPU consuming) to a computing cluster, or even on your PC. 

We call this program `prepareOpticalCalibration.py`. It runs with some command line options, that for this example are already written in the  `optical_calibration.sh` file:

```
source /cvmfs/sft.cern.ch/lcg/views/LCG_105/x86_64-el9-gcc13-opt/setup.sh

SIMPATH="$SPACAL"
CONFIG="base.cfg"
BASEFOLDEROUT="out"
BASEFOLDERJOB='jobs'
ZN='151' 
EMIN='1.5'
EMAX='2.7'
EN='6'
PRIMARIES='1000000'
JOBS='1000'
QUEUE='workday'

python3 ${SIMPATH}/parametrization/prepareOpticalCalibration.py \
--build ${SIMPATH}/build \
--config ${CONFIG} \
--baseFolderOut ${BASEFOLDEROUT} \
--baseFolderJobs ${BASEFOLDERJOB} \
--zn ${ZN} \
--emin ${EMIN} \
--emax ${EMAX} \
--en ${EN} \
--primaries ${PRIMARIES} \
--jobs ${JOBS} \
--queue ${QUEUE} 
```

First of all, this script is set up to run on LXPLUS, so as first thing it will source the LCG_105 environment.

As you can see, you need to pass to the program the location of the simulation build folder with `--build`, the module configuration file with `--config`, a folder where the output files will be saved `--baseFolderOut`, and a folder where the job scripts will be written with `--baseFolderJobs`. 

Then, you specify the calibration grid. The program automatically computes the x-y-z dimensions of the crystals to probe from the config file, so you just need to decide how many points to probe in each direction. Furthermore, the number of points in x and y are set to 1 by default (and this is usually OK for thin crystals), so you just need to choose the number of points along z with `--zn`. 

The energy is sampled just like space. That is, the point sources emit monochromatic photons, but we need to scan the emission spectrum of the scintillator in order to have a good calibration. `prepareOpticalCalibration.py` needs the range that you want to scan with `--emin` and `--emax` and the number of energy points with `--en`. To choose the appropriate range, you can take a look at the crystal emission spectrum in the `out.root` file we just produced (the `enHisto_8` histogram). 

You then specify how many optical photons you want to produce for each (x-y-z-en) combination, and the number of jobs into which you want to split the calibration. Finally, since this is most likely going to run on LXPLUS, you need to specify which queue you want to use, in the HTCondor jargon.

Now we don't have time to run a real optical calibration, but we can run a very short one just as example. If you are on your local machine, modify this file by commenting the `source` command and adding the flag `--local \` just before the last line. Also, reduce (dramatically) the simulation length by changing 

```
ZN=151
PRIMARIES='8'
JOBS='4'
```

Save and run the script with 

```
source optical_calibration.sh
```

This will produce another python script to run all the jobs in parallel

```
python3 runLocal_jobs.py
```

After a few seconds you will have 4 new files in the `out` sub-folder. You need to merge them and create the final calibration file, by moving to the out folder and running

```
$SPACAL/build/mergeCalibration -f ./ -p out -o calibration_small.data
```

These would be se same steps you execute on LXPLUS to run a full calibration. Clearly, you will need to keep the `source` command, set a proper `--baseFolderOut` to a location where you have enough space (roughly 100 GB for the out* files), wait for the jobs to finish and then merge manually the dataset. The `calibration.data` will be less then a gigabyte, and after you produced it you can remove all the out* files.

Obviously this calibration file is too small to be of any use. We already performed a proper calibration for this type of module, in what we described in Section 

```
scp lxplus:/eos/experiment/spacal/Simulations/Tutorial/OpticalCalibration/calibration.data .
```

where of course `lxplus` for me is an alias to the standard `username@lxplus.cern.ch` syntax.

In general, the optical calibrations of several different module configurations are stored CalibrationLibrary folder on our shared EOS space. Provided you have access to that, more specifically in

```
/eos/experiment/spacal/Simulations/CalibrationLibrary/
```

Each sub-folder contains the calibration file and the module configuration that was used to produce it. We suggest to use these calibration files for studies that involve typical **SPACAL** and **SHASHLIK** modules (for example for physics studies on full ECAL detectors, as we will see later). 


#### Step 3. Hybrid Propagation

We can now move on to the job of adding scintillation photons to our output files. This is done using the program 

```
$SPACAL/build/propagateHybrid -i out.root -o hybrid.root -c calibration.data
```

As you can see, the program simply needs the input file (i.e. the output of step 1), the optical calibration file and the name of the output file. Let's have a look at this newly created `hybrid.root`

![Alt text](Images/image_010.png?raw=true "Title")

As you can see, the structure is similar to `out.root`, but the `photons` TTree has been replaced by `hybrid`. Having a look inside, you will see that it contains information on each optical photon (Scintillation and Cherenkov) recorded at the logging volumes. For example, let's draw the distribution of time of arrival of all photons extracted from the negative z side of the module, in the first 10 ns: 

```
hybrid->Draw("timestamp >> (1000,0,10)","z<0")
```

![Alt text](Images/image_011.png?raw=true "Title")

You will notice here that besides the `timestamp` variable that contains the time of arrival of each photon, information is stored also on the 3 contributions to the timestamp formation, i.e.

```
t_deposition    -> time of particle creation by energy deposition from the em shower
t_generation    -> time due to the process generating the photon
t_propagation   -> time from photon generation to extraction
```

You can check easily that for example the `t_generation` value is always equal to 0 for Cherenkov photons. Try drawing for example `hybrid->Draw("t_generation","processNumber == 1")`.

#### Step 4. Pulse formation

Once the photons are generated and transported to the extraction volumes, they can be used to produce actual pulses. This involves of course assigning photons to different photodetectors, applying some filters (taking into account the collection efficiency from the moment the photon exits from the crystals to its entrance into the photodetector), taking into account the quantum efficiency, the photodetector response etc. 

All these operations are performed by `simReadout`. The syntax is very simple:

```
$SPACAL/build/simReadout -c SignalConfigFile_HPKR7600U-20_FL1_CFD02.cfg -i hybrid.root -o OutGroupd
```

So again, besides input and output, a configuration file is needed. The number of modules, cells and their geometry is automatically retrieved from the maps in `hybrid.root`.


The configuration file allows to set all the input and output name branches, as well as the digitization settings (gate, binning, delay, electronic noise, etc...).   

*Program Workflow:*
The program takes in input the hybrid file, groups the photons by event, module and cell and produce pulses.
1. Some photons are discarded to simulate losses in the coupling. This can be tuned in the configuration file through the parameter ```UnifLossFac```, defined as Number of photons exiting the fibers / Number of photons reaching the photodetector. For instance if ```UnifLossFac = 3```, 1 photon every 3 reaches the photodetector. 
2. The photodetector response is simulated. QE is taken into account and, for each photon detected, the timestamp of arrival is smeared according to the detector single photon time response (SPTR), an overall delay is added simulating cables and the pulse is produced. All the relevant parameters can be set in the configuration file.

The output of this program will contain 2 + 2 x #modules in the simulation branches. That is, for a single module simulation, it will contain 2 + 2 = 4 branches.
They are:
- ```Total_Light``` (int): for each event, total number or photons detected (or photoelectrons produced) in the whole calorimeter. Useful to understand the total amount of energy deposited.
- ```modulesHit``` (std::vector<int>): for each event, vector containing the ID of the modules detecting at least one photon during that event.
- ```modN_ph``` (std::vector<int>) where N is the ID of the module: for each event, vector with as many entries as the number of cells in the module N. Each entry is the number of photons detected in each cell.
- ```modN_pulse``` (std::vector<std::vector<float>>) where N is the ID of the module: for each event, vector with as many entries as the number of cells in the module N. Each entry is a std::vector<float> containing the simulated and digitised pulse.

To visualize the output file, it is possible to use the ROOT macro `$SPACAL/scripts/pulseVisualization.C`. It will show the pulses of an event of a module. These, along the input file, can be selected in the macro through 3 variables. 

Let's copy it here

```
cp $SPACAL/scripts/pulseVisualization.C .
```

and open it with a text editor. Let's modify the lines 16-18 in this way:

```
std::string inFile = "OutGroupd.root";   // INPUT FILE NAME
int nModule = 0;                         // MODULE DESIRED
int nEvent  = 0;                         // EVENT DESIRED
```
and run the macro with

```
root -l -b -q pulseVisualization.C
```
This will produce a ROOT file, `output_pulseVisualization.root`. Inside, you can find all the pulses generated, for event number 0, on the 128 detectors  (64 in front, 64 in the back), coupled to our module. The detectors reflect the definitions of cells that we wrote in `base.cfg`. Given the GPS file we used, you will see something interesting in detectors number 36, 37, 100, 101 etc. For example

![Alt text](Images/image_012.png?raw=true "Title")

![Alt text](Images/image_013.png?raw=true "Title")

Obviously, if you want to visualize pulses for another event, change the `nEvent` key in `pulseVisualization.C`. 

If you want to see quickly how the detectors are numbered, take a look inside the `OutGroupd.root` file. There you will find the maps (`cell_map_[front|back]_N`) of cell numbers (front and back). The positions reported in the map are referred to the coordinate system of the module itself.

![Alt text](Images/image_014.png?raw=true "Title")

A map of module numbers is also present, which is relevant particularly in case of full ECAL configurations. However, beware that the old way to store module positions, i.e. the TH2 histogram `module_ID_map`, is not valid anymore in case of rotated modules. The TH2 is left in the output files for back-compatibility reasons, and its information is still valid if no module is rotated. The correct spatial information on the modules is anyway always contained in the new TTree `modules`, where for each module you can find


```
ID              = local module ID (local = referred to the module type, so not useful for end users)
globalID        = global module ID, unique identifier for each of the 3312 ECAL modules
type            = module type
material        = material number for the module absorber
x               = x position of the module center [mm]
y               = y position of the module center [mm]
z               = z position of the module center [mm]
angle_x         = rotation angle wrt to x axis [degrees]
angle_y         = rotation angle wrt to y axis [degrees]
angle_z         = rotation angle wrt to z axis [degrees]
dx              = length in x direction [mm] 
dy              = length in y direction [mm] 
dz              = length in z direction [mm] 
separation_z    = z position of front/back separation (if any)
sections        = number of longitudinal sections (1 or 2)
```

Plese refer to this TTree (saved in both `OutGroupd` and `OutTrigd` output files) rather than on `module_ID_map`.


#### Step 5. Time and energy information

Any type of analysis can be applied to the pulses we just produced. Users can of course write their own code to extract time and energy information, using different level of sophistication. We wrote a code to extract energy and timing by counting the number of photoelectrons on each photodetector and applying constant fraction discriminator (CFD) technique to get a timestamp for each pulse. 

This program is called `ApplyCFD`. It takes as input the output file of `simReadout` and creates an output ROOT file which contains all the information of the input file plus a branch of timestamps per branch of pulses. Additionally, it draws the pulse of an event for each branch of pulses.
It can be run with:

```
$SPACAL/build/ApplyCFD -c SignalConfigFile_HPKR7600U-20_FL1_CFD02.cfg -i OutGroupd.root -o OutTrigd -t 0.2
```
The flags stand for:
- *c* Configuration file
- *i* Input data file
- *o* Output data file
- *t* Peak fraction whereat the threshold is set. If the value is valid, it overrides that set in the configuration file. [optional]

Some configuration parameters required by the ```ApplyCFD``` are in common with ```simReadout```, therefore they can share the same configuration file. In fact, the digitization parameters are in common for the two programs.
Key parameters are:
- ```baseLineSamples``` : Number of samples used to calculate mean and sigma of the baseline
- ```peakFraction```    : Fraction of the pulse peak at which the timestamp will be calculated.
- ```convert_to_ns```   : All the timestamps and the plots will be converted in time units. The conversion factor between clock units and time is calculated from the digitizer parameters in the configuration file. OFF by default.


The output of this program will be a copy of the input tree where the ```modN_pulse``` branches are delete and replaced by:
- ```modN_t``` (std::vector<float>) where N is the ID of the module: for each event, vector with as many entries as the number of cells in the module N. Each entry is the timestamp obtained with CFD on the pulse. If the algorithm failed, for instance due to a pulse indistinguishable from the electronic noise, a negative timestamp is returned. Hence, *always filter out negative values when doing timing analysis*

### 1.3.6 Put everything together: a full module study

The data we produced so far in the final `OutTrigd.root` can be analyzed to draw interesting plots on the module performance. Obviously, with just 5 electrons shot at 1 GeV, there's not much we can plot. But before starting to dig into this step by step procedure, we had already submitted a full study, with a configuration file which should be precisely the one you produced now. 

Furthermore, you also already know by now how to produce the Optical Calibration of the module described in `base.cfg`. You've seen how to prepare it and submit it on LXPLUS (same procedure as local, uncommenting the source command, removing the `--local` flag and specifying a proper output folder) and also how to merge it. All we need to understand is how we've performed all the steps above in just one go, at the beginning of this tutorial.

In the Hybrid-MC, everything can be prepared for execution by a single python script, `$SPACAL/parametrization/prepareChain.py`. Thanks to this script, it is possible to prepare full simulations campaigns for running on 3 different **platforms**:

- On a local PC
- On the LXPLUS computing cluster, via HTCondor
- On the grid, via Ganga

and with 2 different types of input particles, which defines two **modalities**:

- Single particles, using Geant4 particle gun
- A flux of particles coming from an LHC collision

In general, we will refer to the **platforms** as:

- *local*
- *lxplus*
- *grid*

and to the **modalities** as:
- *pgun*
- *flux*

We already have in hands all we need to start. Namely

```
base.cfg
gps_e_3+3.mac
```

The `/gps/energy` and `/run/beamOn` commands in `gps_e_3+3.mac` will in fact be overridden by `prepareChain.py` (so you can leave them there). Let's have a quick look to the command line parameters, with some explanation. Don't be scared, as you will see later we've already packaged all you need to input in an appropriate bash script.


```
--config            <value>    - main config file                              (required)
--baseFolderJobs    <value>    - main jobs folder                              (required)
--baseFolderOut     <value>    - main output folder                            (required)        
--build             <value>    - path to spacal build folder                   (required)
--events            <value>    - total number of primary particles to shoot for a any energy (required)  
--baseGPS           <value>    - base GPS file          
--listEnergy        <value>    - list of energies to simulate      
--listEvents        <value>    - for each energy, how may primaries to shoot per job  
--listQueue         <value>    - for each energy, on which queue to submit the jobs
--listCalibrations  <value>    - list of optical calibration binary files [calibration.data]
--listTypes         <value>    - list of module type associated to a calibration file
--pulse                        - flag to enable pulse formation and analysis
--pulseConfig       <value>    - signal formation configuration file for pulse analysis
--useFlux           <value>    - input particle flux file (enables use of flux)
--local                        - flag to choose local platform (by default platform is lxplus)
--grid                         - flag to choose grid platform (by default platform is lxplus)
--onlyEnDepo                   - force chain to stop at step 1 in the chain (before hybrid propagation)
--discardEnergyDepositions     - flag to disable copying outN files to the output folder
--keepHybrid                   - flag to enable copying hybrid files to the output folder
--keepGroupBy                  - flag to enable copying Groupd files to the output folder
--requestDisk       <value>    - request a certain amount of disk space on the target node on LXPLUS
--chi                          - flag to perform and copy the output of the photoelectrons/energy analysis
```

Some parameters require further explanation. In particular the lists of energy, queues and events:

```
These lists and the parameter "events" determine how many jobs will be prepared.
For example, suppose you want to perform a pgun simulation with energies (in GeV)

1 2 3 4 5 10 25 50 75 100

and shooting always 1000 electrons per energy. 
By some tests you performed, you also know how long one event takes per each energy. 
So you want to run for example 25 primaries per job for energies from 1 GeV to 5 GeV, 
then 10 primaries for 10 GeV, 5 primaries for 25 GeV, and finally 2 primaries for 50, 
75 and 100 GeV. You calculated that for 1 and 2 GeV the appropriate queue would be the 
"longlunch" one, while "workday" will be better suited for the others. 
You can therefore use the arguments like this:

--events 1000 
--listEnergy 1 2 3 4 5 10 20 35 50 100 
--listEvents 25 25 25 25 25 10 5 2 2 2 
--listQueue longlunch longlunch workday workday workday workday workday workday workday workday

This will automatically create (1000/25) = 40 jobs (so 40 lines in the corresponding args.txt file) 
for the first 5 energies, (1000/10) = 100 jobs for 10 GeV and so on.
```

and the list of calibration files and types

```
These lists determine which optical calibration files to use, 
and what module type is associated with a specific calibration file.

As we will see, it is possible to simulate more than one type of modules per simulation. 
This of course forces the need to use more than one optical calibration in order to perform 
the hybrid propagation. The user will need to perform an optical calibration for each module type, 
then pass the optical calibration files as list to the flag --listCalibrations. 
Furthermore, the user will need to tell the module type of each calibration to the simulation program, 
by a list with the flag --listTypes. 
IMPORTANT: the lists need to be in the same order!

If the simulation is performed without using multiple modules, 
then the user can specify only one calibration file in --listCalibration, 
and omit the --listTypes flag.
```

Furthermore, it is interesting to notice that by default, if `--pulse` is specified and a `--pulseConfig` is provided, the full chain described before is performed, but only the `out*` files (output of step 1) and the `OutTrigd*` will be copied to the output folder. This default choice is mainly due to historical reasons (besides the fact that you want at least to save the final files). You can control anyway which files are copied to the target folders by using the `--discardEnergyDepositions`, `--keepHybrid` and `--keepGroupBy` flags. 

Finally, notice that if none of the flags `--local` or `--grid` are provided, the script will assume that you want to prepare jobs for a LXPLUS run. 

Now that we've seen how `prepareChain.py` can be run, you can certainly understand the role of `prepare.sh`: is is just a simple bash script that wraps the command line arguments that we pass to `prepareChain.py`. It has been written just for convenience, and in fact there is no need for you to use it. We have been preparing simulations directly with `prepareChain.py` for a long time as well. Take `prepare.sh` as a template to automatize your work, if you wish. 

We can now go back to LXPLUS, and take a **closer look** to the `prepare.sh` script options, to understand what you will need to modify in order to run it.

There are several comments explaining what is what in the script, especially in what is called `Section 1.`, but for now let's just follow this guide. You are interested in `Section 2.` and `Section 3.`, which you need to modify if you want to use this script yourself. In fact, these scripts are already prepared for *flux* modality so there's not many modifications to do. 

#### Section 2.

This section is modified on the basis of the chosen **platform**. As you can see in `Section 2.` the **platform** cases are already split, so in fact they will automatically adapt to the different platforms. Nevertheless, unfortunately the values written there are necessarily in most cases valid only of a specific user (this cannot be generalized easily), so you need to set these variables as follows:

- **SIMPATH:** This corresponds to the location where you downloaded the HybridMC code from gitlab. The **SIMPATH** values reported there are valid for my PC and my lxplus, but they won't be valid for yours, so you need to change them. So depending on the **platform**:
    - *local* : path to your local HybridMC code folder
    - *lxplus* : path to your lxplus HybridMC code folder
    - *grid* : path to your lxplus HybridMC code folder


- **LISTCALIBRATIONS:** Here you would need to modify only for the *local* case. This would mean that you produced or copied the correct optical calibration file(s) in your local machine. You can leave the paths for the other 2 cases as they are. They corresponds to the correct Optical calibration files available on LXPLUS and on the grid, and you don't need to produce new ones. 

- **FLUX:** This will be relevant when we perform flux simulation, and can be ignored now. Anyway, same as previous point, for *lxplus* and *grid* runs you could leave everything like it is, but you can of course also use another flux file. For *local*, copy a flux file somewhere on your local machine and write its path in FLUX.

#### Section 3.

This section is modified on the basis of the simulation **modality**. The meaning of each key is reported in the script itself, anyway now we want to run a *pgun* simulation and this script is already set for that, so there is almost nothing to do. Just modify this value:

- **BASEFOLDEROUT:** This is the main folder of the output files. If you don't specify a full path, a sub-folder of the current directory will be assumed. Otherwise the full path will be created. It is suggested to always set this to a EOS folder for simulations that are not *local*. So to summarize:
    - *local* : leave it as `out`, it will create a sub-folder in current directory
    - *lxplus* : choose a EOS folder
    - *grid*   : choose a EOS folder

Notice that the other keys have been set as explained above for `prepareChain.py`. We are therefore jobs to create jobs that will shoot to the module 1000 electrons at 8 different energies. For each energy, the jobs will shoot a different number of electrons per job (for example, 50 electrons of 1 GeV per job, but only 4 electrons of 35 GeV per job). The jobs will be all submitted to the `testmatch` queue, if we run on lxplus.

### 1.3.7 Analyze output files

Let's now take a look at the output folder of our initial simulation campaign

```
/eos/experiment/spacal/Simulations/Tutorial/SingleModuleStudy
```


As we said before, these output files can be analyzed as you prefer. In order to see an example of some information that can be extracted from this simulation, and also to provide you with some template programs to understand how to read and analyze the output files, we are going to show a typical energy and timing resolution investigation. All can be performed with some programs and scripts we wrote. Just copy the content of the folder `Analysis` into the main `BASEFOLDEROUT` folder defined before, then always from `BASEFOLDEROUT` run 

```
./go.sh $SPACAL
```

where the `$SPACAL` holds the location where you downloaded the simulation code on LXPLUS, just like before. The analysis time may vary depending on the batch computer you logged to, but it's not going to take more than some minute. In the end, you will find several plots and text files in the `BASEFOLDEROUT` folder, as you can see in this example `/eos/experiment/spacal/Simulations/Tutorial/SingleModuleStudy.` 

Let's take a look for example to `energy_resolution.png`

![Alt text](Images/image_015.png?raw=true "Title")

or to `timing_all.png`

![Alt text](Images/image_016.png?raw=true "Title")

Here, the timing resolution is extracted only from the cells where the beam is aiming to, both from the front and the back of the module. Furthermore, the timestamps of front and back cells are combined, with 3 methods: a simple average ((t_front+t_back)/2), with weighting the timestamps on the timing resolution of the cells themselves at a given energy, and using the covariance factor. 

You have now a **complete example** on how to perform a single module study. Take a look into the code used to generate these last plots and you will find a good starting point to understand how to manage the output files and write your own analysis.

Let's go now to the next step of the tutorial, i.e.

```
documentation/Tutorial/2.ECALstudy/ECALStudy.md
```




