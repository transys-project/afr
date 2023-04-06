import argparse
import datetime
import os
import random
import sys
import numpy as np

import algorithm
import env
import traceloader

target_arri_seq = []
random.seed(10)

def files_generator(args):
    if not os.path.exists(os.path.join(args.log, args.settings)):
        os.makedirs(os.path.join(args.log, args.settings))
    if not os.path.exists(os.path.join(args.action, args.settings)):
        os.makedirs(os.path.join(args.action, args.settings))
    if not os.path.exists(os.path.join(args.result, args.settings)):
        os.makedirs(os.path.join(args.result, args.settings))

def excute_simulation(args, fname, qlen_map_seq = [], qwait_map_seq = []):
    # initialize the states
    dec_env = env.Environment(args, fname)
    fpath = os.path.join(args.trace, fname)
    traces = traceloader.TraceLoader(fpath, args.min_trace_length)

    trace_end = 0   # flag whether we read the end of the trace
    target_arrv = 1 / 60  # the initial factor
    is_pause = False # not pausing encoder
    
    alg = algorithm.Algorithm(args, fname)
    alg.qlen_target_map_seq = qlen_map_seq
    alg.qwait_target_map_seq = qwait_map_seq

    while not trace_end:
        line, trace_end = traces.load_line(target_arrv)
        qlen, qwait, arrv_intvl, serv_intvl, rtt = dec_env.step(line)
        target_arrv = alg.predict(qlen, qwait, arrv_intvl, serv_intvl, rtt)
        
    del traces
    del dec_env
    del alg

def run_single_trace(param):
    fname, args = param

    # skip short logs (it should've already been removed when processing the logs, only for sure)
    with open(os.path.join(args.trace, fname), 'r') as f:
        cnt = -1
        shortFlag = True
        for cnt, line in enumerate(f.readlines()):
            cnt += 1
            if (cnt > args.short_session):
                shortFlag = False
                break
        if shortFlag:
            print(fname, "short flow", cnt)
            return

    if args.algorithm == 'qlen' or args.algorithm == 'qwait': # enumerate baselines
        map_seq = []
        # generate real input to target_arriv mapping list
        for idx in target_arri_seq:
            map_seq.append(algorithm.TARGET_ARRIVAL_INTERVAL[idx])
        excute_simulation(args, fname, qlen_map_seq = map_seq, qwait_map_seq = map_seq)
        return

    excute_simulation(args, fname)


if __name__ == "__main__":
    starttime = datetime.datetime.now()
    parser = argparse.ArgumentParser()
    # Simulator settings
    parser.add_argument('--min-trace-length', type=int, default=5, help='The filter of minimum frame number for a flow')
    parser.add_argument('--max-queue-length', type=int, default=16, help='The capacity of pre-decoder queue')
    parser.add_argument('--short-session', type=int, default=7200, help='The minimum number of a valid flow')
    parser.add_argument('--frame-rate-level', type=int, default=5, help='Quantized frame rate level')
    parser.add_argument('--increase-delay', type=float, default=1, help='Delay of frame rate increase')
    parser.add_argument('--random_sample', type=int, default=0, help='Random sample from traces. 0 means all')

    # Input and output settings
    parser.add_argument('--trace', default='../traces', help='The directory contains the trace directory')
    parser.add_argument('--log', default='../logs', help='The directory where resulting logs are generated')
    parser.add_argument('--action', default='../actions', help='The directory where frame rate actions are generated')
    parser.add_argument('--result', default='../results', type=str)

    # Algorithm settings
    parser.add_argument('--algorithm', choices=['afr', 'bba', 'qlen', 'hta', 'native', 'afrqcn', 'qwait', '60fps', 'pause', 'txrate'], help='Frame rate control algorithm.')
    
    # Parameters for AFR
    parser.add_argument('--wzero', type=float, default=0.002, help='W0 in HTA')
    parser.add_argument('--xi-arrv', type=float, default=0.033, help='Xi-arrv in preprocess')
    parser.add_argument('--xi-serv', type=float, default=0.25, help='Xi-serv in preprocess')

    # Parameters for Qlen or Qwait
    parser.add_argument('--qlen_target_arri_seq', type=list, nargs='*', default='0123', help='sequence of mapping qlen to target arrival interval')
    parser.add_argument('--qwait_target_arri_seq', type=list, nargs='*', default="0123", help='sequence of mapping qwait to target arrival interval')

    # Parameters for pause
    parser.add_argument('--pause_dimension', choices=['len', 'wait', 'hta'], default= 'len', help='dimention for pause judging.')
    parser.add_argument('--pause_stop_threshold', type=int, default= 1, help='deactivate encoder pausing when pause_dimension < the threshold (contorller subject to dimention <= threshold).' )
    parser.add_argument('--pause_activate_threshold', type=int, default= 1, help='activate encoder pausing when pause_dimension > the threshold (must > pause_stop_threshold).')
    
    # Parameters for txrate
    parser.add_argument('--rho', type=float, default=0.95)
    
    # Performance settings
    parser.add_argument('--threads', type=int, help='Number of parallel threads')
    parser.add_argument('--mode', choices=['debug', 'release', 'ray'], default='release')
    args = parser.parse_args()

    if args.algorithm == '60fps':
        args.max_queue_length = np.inf

    # set the settings of this experiment, with parameters on the name of the folder
    if args.algorithm == 'afr' or args.algorithm == 'hta':
        args.settings = "%s_%.5f_%.3f_%.3f" % (args.algorithm, args.wzero, args.xi_arrv, args.xi_serv)
    elif (args.algorithm == 'qlen' or args.algorithm == 'qwait'):
        target_arri_seq = args.qlen_target_arri_seq[0]
        if args.algorithm == 'qwait':
            target_arri_seq = args.qwait_target_arri_seq[0]
        target_arri_seq = [int(item) for item in target_arri_seq]
        if len(target_arri_seq) < 4:
            print("length of qlen/qwait's input target_arri_seq must >= 4")
            sys.exit()
        args.settings = "%s_%d_%s" % (args.algorithm, len(target_arri_seq), ''.join([str(elem) for elem in target_arri_seq]))
    elif args.algorithm == 'pause':
        if args.pause_stop_threshold > args.pause_activate_threshold:
            print("pause baseline's pause_activate_threshold must > pause_stop_threshold")
            sys.exit()
        args.settings = "%s_%s_%d_%d" % (args.algorithm, args.pause_dimension, args.pause_stop_threshold, args.pause_activate_threshold)
    elif args.algorithm == 'txrate':
        args.settings = "%s_%.2f" % (args.algorithm, args.rho)
    elif args.algorithm == 'native':
        args.settings = "%s_%d" % (args.algorithm, args.max_queue_length)
    else:
        args.settings = args.algorithm
    
    files_generator(args)
        
    # check the type of the session (network, client, etc.)
    fnames = os.listdir(args.trace)

    # the simulation mode (affecting the performance)
    # the release mode takes up the resources on the local server. if args.thread is defined, it will take args.thread cores, otherwise all cores on this server.
    if args.mode == 'release':
        from multiprocessing import Pool
        if args.threads:
            pool = Pool(args.threads)
        else:
            pool = Pool()
        if args.random_sample == 0:
            pool.map(run_single_trace, [(fname, args) for fname in fnames])
        else:
            fnames.sort()
            pool.map(run_single_trace, [(fname, args) for fname in random.sample(fnames, args.random_sample)])
        pool.close()
        pool.join()

    # the ray mode has been deprecated
    elif args.mode == 'ray': 
        from ray.util.multiprocessing import Pool
        pool = Pool()
        pool.map(run_single_trace, [(fname, args) for fname in fnames])
        pool.close()
        pool.join()

    # the debug mode has no parallel acceleration
    elif args.mode == 'debug':
        if args.random_sample == 0:
            for fname in fnames:
                run_single_trace((fname, args))
        else:
            fnames.sort()
            for fname in random.sample(fnames, args.random_sample):
                run_single_trace((fname, args))

    endtime = datetime.datetime.now()
    print(f'{args.settings} totalTime: {(endtime - starttime).total_seconds()/60:.2f} minutes')
