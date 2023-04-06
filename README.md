# AFR
This repo contains all necessary codes for the implementation of the AFR paper. Specifically, 
- `scripts/` contains the evaluation and statistics scripts for the paper.
- `sim/` contains the codes for the frame-rate adaption simulator.
- `*data*/` are the data folders containing the online traces and evaluation outputs.

In general, when new traces are collected, scripts in the `scripts\` folder are needed to preprocess and parse the traces. Then the simulator in the `sim\` could be executed to run the simulation and output the log files. Finally, scripts in the `scripts\` would be needed again to calculate the needed statistics from the output logs.

Please refer to the readme files in each folder for specific usages in detail.
