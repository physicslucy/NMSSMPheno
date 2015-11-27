#Example PyROOT Tree plotter/looper script

A very basic PyROOT script to showoff Python and PyROOT. It will produce a couple of simple plots and print some info to screen.

The script uses a ROOT file produced by `generateMC.exe`. So if you want to run it, inside the `NMSSMTools/Pythia` directory do the following:

1) Compile the program if you haven’t already:

```
make
```

2) Run it, generating 1K ggh(125) -> 2a -> 4tau events, and saving to ROOT file:


```
./generateMC.exe --card input_cards/ggh125_2a_4tau.cmnd -n 1000 --root
```

You should get a ROOT file named `ggh125_2a_4tau_ma1_8_13TeV_n1000_seed0.root`

3) Run the python script

```
cd example_study
./basicPlotter.py ggh125_2a_4tau_ma1_8_13TeV_n1000_seed0.root
```

For more info about ROOT classes, see the reference guide: https://root.cern.ch/doc/master/index.html

Happy plotting!
