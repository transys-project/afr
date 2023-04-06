# AFR Simulator

## Structure of the simulator

The files used in the simulator:
```
.
├── algorithm.py
├── env.py
├── main.py
└── traceloader.py
```
Specifically,
- `main.py` is the main loop of the simulator. It parses arguments, prepares input and output directories, starts processes, and dispatches traces to each process. It calls `env.py` to set up a simulation environment, `traceloader.py` to load traces into the simulator, and `algorithm.py` to simulate the algorithm based on the trace.
- `env.py` sets up the simulation environment. It sets up the environment for each trace, and maintains the timeline and frame generation states. It works at the granularity of frame: upon a new frame arrival, it will compute the waiting time, arrival interval, service interval, etc., and return these results to the `main.py`.
- `algorithm.py` implements the AFR algorithm and several baseline algorithms. It takes the current network and queue states as input, and then calculates the target frame-rate. The actual return value of algorithms is the *slowdown* factor, which is the ratio of the target frame-rate over the current frame-rate (details introduced below).
- `traceloader.py` load one line (one frame) from the trace file in each loop, according to the slowdown factor from `algorithm.py`. The slowdown factor is a scaling factor to the timeline of the trace file. It returns the information of the next frame to the environment.

In summary, the main loop of the simulator is:
```
while not trace_end:
    line, trace_end = traces.load_line(slowdown)
    qlen, qwait, arrv_intvl, serv_intvl, rtt = dec_env.step(line)
    slowdown = alg.predict(qlen, qwait, arrv_intvl, serv_intvl, rtt)
```

## Arguments of `main.py`

Input and output settings
| Args | Default value | Explanation | Mode: Local | Mode: Remote | Mode: Debug | 
|:---:|:---:|:---:|:---:|:---:|:---:|
| `--trace` | `../traces` | The directory contains the trace directory. | `../online_data/cut` | `../traces` | `test-trace` |
| `--log` | `../logs` | The directory *prefix* where resulting logs are generated (for performance analysis). The actual log directory is a sub-folder, with the name of settings, of the parameter. | `../online_data/logs` | `../logs` | `test-trace` |
| `--action` | `../actions` | The directory *prefix* where frame rate actions are generated (for frame-rate & smoothness analysis). | `../online_data/actions` | `../actions` | `test-action` |
| `--result` | `../results` | The directory *prefix* where some deprecated are generated (for frame loss analysis). | `../online_data/results` | `../results` | `test-result` |

For other parameters, please refer to the help of each parameter in argparse. An example command to run AFR with full dataset:
```
python main.py --trace ../online_data/cut --log ../online_data/logs --action ../online_data/actions --result ../online_data/results --algorithm afr --mode release
```
**Attention! Be careful when running the simulator with full dataset. The output logs and results will overwrite previous outputs!**

To monitor the simulation process, you can first clear up the output folder before simulation, and then comparing the number of files in the output folder with the input trace folder with `ls {folder} | wc -l`.

Since the simulation time is very long with numerous traces, you can debug the simulator with a small set of traces (located in `test-*/`). For example,
```
python main.py --trace test-trace --log test-log --action test-action --result test-result --algorithm afr --mode debug

# for enumerate baselines
python main.py --trace test-trace --log test-log --action test-action --result test-result --algorithm qlen --qlen_target_arri_seq 0123 --mode debug
```

## How does `env.py` work?
The main fucntion of the environment is implemented in the `step()` function. It takes one frame as input, calculates the dequeued frames between the arrival of two frames, and enqueues the newly arrival frame. The final queue states are then returned to the main loop.

## How does `traceloader.py` work?
The main function of the trace loader is the `load_line()` function. It reads the slowdown factor, enqueues the slowdown factor to a staged queue (to simulate the network delay), dequeues the slowdown factor according to their network delay, and calculates the frame information based on linear interpolation between frames.

## How does `algorithm.py` work?
The algorithms implemented here are quite straightforward. Please referred to the inline comments for the usage of each algorithm.

## Usage of `stat.py`
Besides the main components of the simulator, we also need to analyze the statistics of the logs. The `stat.py` has the following argument:

|Argument|Explanation|
|:---:|:---|
|`--log`| The directory storing logs, the same as the log in the argument of `main.py`.|
|`--result`| The directory to generate output results, the same as the log in the argument of `main.py`.|
|`--queuing`| If this flag is set, the percentiles of the queuing delay will be generated to `queuing_all.log`. |
|`--interarrival`| If this flag is set, the percentiles of the interarrival time will be generated to `interarrival_all.log`. |
|`--smooth`| If this flag is set, the percentiles of the difference of the interarrival time will be generated to `smooth_all.log`. |
|`--total`| If this flag is set, the percentiles of the total delay will be generated to `total_all.log`. |
|`--settings`| The settings that need statistics. Be consistent with the folder name in the `log` argument. |
|`--filter`| Filter is used to categorize the network type, device type, client type, etc. `w` used for wildcard. It includes devType (UNKNOWN, DESKTOP, LAPTOP, PHONE, PAD, STB, TV), netType (NONE, MOBILE, ETHERNET, WIFI, OTHER), clientType (WinPC, IOS, MacPC, Android), decodeType (SOFTWARE, HARDWARE). For example, `w20w` represents all Ethernet and Windows sessions. |
|`--flowinfo`| The log file storing the classification for each flow, working with `--filter`. The default value is `../online_data/flowinfo.log` |

An example usage:
```
python stat.py --log test-log --result test-result --filter w20w --queuing --interarrival --smooth --total --settings afr_0.00200_0.001_0.250 --flowinfo ../online_data/flowinfo.log
```
Then you can find all results in `test-result/w20w/afr_0.00200_0.001_0.250`.