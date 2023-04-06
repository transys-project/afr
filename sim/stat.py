import argparse
import datetime
import os
import subprocess as sp
from multiprocessing import Pool

import numpy as np


def stat(param):
    fname, args, prefix = param
       
    if args.queuing:
        fname_queuing = os.path.join(prefix, fname + '_queuing.tmp')
        f_queuing = open(fname_queuing, 'w')
    if args.interarrival:
        last_arrival = -1
        fname_interarrival = os.path.join(prefix, fname + '_interarrival.tmp')
        f_interarrival = open(fname_interarrival, 'w')
    if args.smooth:
        last_interarrival = -1
        inter_arrival = -1
        fname_smooth = os.path.join(prefix, fname + '_smooth.tmp')
        f_smooth = open(fname_smooth, 'w')
    if args.total:
        fname_total = os.path.join(prefix, fname + '_total.tmp')
        f_total = open(fname_total, 'w')
    if args.decode:
        fname_decode = os.path.join(prefix, fname + '_decode.tmp')
        f_decode = open(fname_decode, 'w')
    if args.network:
        fname_network = os.path.join(prefix, fname + '_network.tmp')
        f_network = open(fname_network, 'w')

    with open(os.path.join(args.log, args.settings, fname)) as f:
        while True:
            line = f.readline().split()
            if not line:
                break
            if args.queuing:
                queuing = float(line[2])
                f_queuing.write("%.2f\n" % queuing)
            if args.interarrival:
                if last_arrival < 0:
                    # actually the time after decoding
                    last_arrival = float(line[0]) + float(line[2]) + float(line[3])
                else:
                    inter_arrival = float(line[0]) + float(line[2]) + float(line[3]) - last_arrival
                    f_interarrival.write("%.2f\n" % inter_arrival)
                    last_arrival = float(line[0]) + float(line[2]) + float(line[3])
            if args.smooth:
                if last_interarrival < 0:
                    if inter_arrival >= 0:
                        last_interarrival = inter_arrival
                else:
                    smooth = abs(inter_arrival - last_interarrival)
                    f_smooth.write("%.2f\n" % smooth)
                    last_interarrival = inter_arrival
            if args.total:
                total = float(line[4])
                f_total.write("%.2f\n" % total)
            if args.decode:
                decode = float(line[3])
                f_decode.write("%.2f\n" % decode)
            if args.network:
                network = float(line[1])
                f_network.write("%.2f\n" % network)
        
    # sort results to calculate cdf
    if args.queuing:
        f_queuing.close()
        sp_queuing = sp.Popen('sort -T ./ -n ' + fname_queuing + ' -o ' + fname_queuing, shell=True)
    if args.interarrival:
        f_interarrival.close()
        sp_interarrival = sp.Popen('sort -T ./ -n ' + fname_interarrival + ' -o ' + fname_interarrival, shell=True)
    if args.smooth:
        f_smooth.close()
        sp_smooth = sp.Popen('sort -T ./ -n ' + fname_smooth + ' -o ' + fname_smooth, shell=True)
    if args.total:
        f_total.close()
        sp_total = sp.Popen('sort -T ./ -n ' + fname_total + ' -o ' + fname_total, shell=True)
    if args.decode:
        f_decode.close()
        sp_decode = sp.Popen('sort -T ./ -n ' + fname_decode + ' -o ' + fname_decode, shell=True)
    if args.network:
        f_network.close()
        sp_network = sp.Popen('sort -T ./ -n ' + fname_network + ' -o ' + fname_network, shell=True)
    
    # calculate per-log cdf
    # if args.queuing:
    #     sp_queuing.wait()
    #     sp_queuing = sp.Popen("awk -vstep=$(awk 'END{printf(\"%.4f\\n\", NR/10000)}' " + fname_queuing + " | bc) 'BEGIN{cnt=1} {sum+=$1;if (NR>=int(cnt*step)){print cnt,$0;cnt=cnt+1+int(NR-cnt*step)}} END{printf(\"Avg %.3f\\n\", sum/NR)}' " + fname_queuing + " > " + os.path.join(args.result, fname + '_queuing.log'), shell=True) 
    # if args.interarrival:
    #     sp_interarrival.wait()
    #     sp_queuing = sp.Popen("awk -vstep=$(awk 'END{printf(\"%.4f\\n\", NR/10000)}' " + fname_interarrival + " | bc) 'BEGIN{cnt=1} {sum+=$1;if (NR>=int(cnt*step)){print cnt,$0;cnt=cnt+1+int(NR-cnt*step)}} END{printf(\"Avg %.2f\\n\", sum/NR)}' " + fname_interarrival + " > " + os.path.join(args.result, fname + '_interarrival.log'), shell=True) 
    # if args.total:
    #     sp_total.wait()
    #     sp_queuing = sp.Popen("awk -vstep=$(awk 'END{printf(\"%.4f\\n\", NR/10000)}' " + fname_total + " | bc) 'BEGIN{cnt=1} {sum+=$1;if (NR>=int(cnt*step)){print cnt,$0;cnt=cnt+1+int(NR-cnt*step)}} END{printf(\"Avg %.2f\\n\", sum/NR)}' " + fname_total + " > " + os.path.join(args.result, fname + '_total.log'), shell=True) 

    if args.queuing:
        sp_queuing.wait()
    if args.interarrival:
        sp_interarrival.wait()
    if args.smooth:
        sp_smooth.wait()
    if args.total:
        sp_total.wait()
    if args.decode:
        sp_decode.wait()
    if args.network:
        sp_network.wait()


if __name__ == "__main__":
    starttime = datetime.datetime.now()
    parser = argparse.ArgumentParser()
    parser.add_argument('--log', type=str)
    parser.add_argument('--result', type=str)
    parser.add_argument('--settings', type=str)

    parser.add_argument('--queuing', action='store_true')
    parser.add_argument('--interarrival', action='store_true')
    parser.add_argument('--smooth', action='store_true')
    parser.add_argument('--total', action='store_true')
    parser.add_argument('--decode', action='store_true')
    parser.add_argument('--network', action='store_true')

    parser.add_argument('--threads', type=int, help='Number of parallel threads')
    parser.add_argument('--filter', type=str, default='w2w1', 
        help='devType (UNKNOWN, DESKTOP, LAPTOP, PHONE, PAD, STB, TV), \n' + 
             'netType (NONE, MOBILE, ETHERNET, WIFI, OTHER), \n' + 
             'clientType (WinPC, IOS, MacPC, Android), \n' + 
             'decodeType (SOFTWARE, HARDWARE)')
    parser.add_argument('--flowinfo', type=str, default='../online_data/flowinfo.log')
    parser.add_argument('--flowlist', type=str)
    args = parser.parse_args()

    if args.filter[0] != "N": # N means none
        devType = args.filter[0]
        netType = args.filter[1]
        clientType = args.filter[2]
        decodeType = args.filter[3]

        filtered_sid = []
        with open(args.flowinfo, 'r') as f:
            while True:
                line = f.readline().split()
                if not line:
                    break
                devCond = devType == 'w' or devType == line[2]
                netCond = netType == 'w' or netType == line[4]
                clientCond = clientType == 'w' or clientType == line[6]
                decodeCond = decodeType == 'w' or decodeType == line[8]
                if devCond and netCond and clientCond and decodeCond:
                    filtered_sid.append(line[0])
        if args.flowlist:
            fnames = np.loadtxt(args.flowlist, dtype=str).tolist()
            prefix = os.path.join(args.result, args.filter + '_' + os.path.split(args.flowlist)[-1], args.settings)
        else:
            fnames = os.listdir(os.path.join(args.log, args.settings))
            prefix = os.path.join(args.result, args.filter, args.settings)

        fnames_new = []
        for fname in fnames:
            sid = fname.split('_')[0]
            if sid in filtered_sid:
                fnames_new.append(fname)
        print(len(fnames_new), '/', len(fnames))
        fnames = fnames_new
    else: # NX means running with sampling X traces
        fnames = os.listdir(os.path.join(args.log, args.settings))
        prefix = os.path.join(args.result, args.filter, args.settings)

    if not os.path.exists(prefix):
            os.makedirs(prefix)

    
    # RELEASE
    if args.threads:
        pool = Pool(args.threads)
    else:
        pool = Pool()
    pool.map(stat, [(fname, args, prefix) for fname in fnames])
    pool.close()
    pool.join()

    # DEBUG
    # for fname in fnames:
    #     stat((fname, args))

    # Con'd
    # cat and sort all-long results
    if args.queuing:
        fname_queuing_all = os.path.join(prefix, "queuing_all.tmp")
        sp_queuing = sp.Popen('ls ' + prefix + ' | grep "_queuing.tmp" | xargs -i cat ' + os.path.join(prefix, '{}') + ' | sort -T ./ -n -o ' + fname_queuing_all, shell=True)
    if args.interarrival:
        fname_interarrival_all = os.path.join(prefix, "interarrival_all.tmp")
        sp_interarrival = sp.Popen('ls ' + prefix + ' | grep "_interarrival.tmp" | xargs -i cat ' + os.path.join(prefix, '{}') + ' | sort -T ./ -n -o ' + fname_interarrival_all, shell=True)
    if args.smooth:
        fname_smooth_all = os.path.join(prefix, "smooth_all.tmp")
        sp_smooth = sp.Popen('ls ' + prefix + ' | grep "_smooth.tmp" | xargs -i cat ' + os.path.join(prefix, '{}') + ' | sort -T ./ -n -o ' + fname_smooth_all, shell=True)
    if args.total:
        fname_total_all = os.path.join(prefix, "total_all.tmp")
        sp_total = sp.Popen('ls ' + prefix + ' | grep "_total.tmp" | xargs -i cat ' + os.path.join(prefix, '{}') + ' | sort -T ./ -n -o ' + fname_total_all, shell=True)
    if args.decode:
        fname_decode_all = os.path.join(prefix, "decode_all.tmp")
        sp_decode = sp.Popen('ls ' + prefix + ' | grep "_decode.tmp" | xargs -i cat ' + os.path.join(prefix, '{}') + ' | sort -T ./ -n -o ' + fname_decode_all, shell=True)
    if args.network:
        fname_network_all = os.path.join(prefix, "network_all.tmp")
        sp_network = sp.Popen('ls ' + prefix + ' | grep "_network.tmp" | xargs -i cat ' + os.path.join(prefix, '{}') + ' | sort -T ./ -n -o ' + fname_network_all, shell=True)

    # calculate all-log cdf
    if args.queuing:
        sp_queuing.wait()
        sp_queuing = sp.Popen("awk -vstep=$(awk 'END{printf(\"%.4f\\n\", NR/10000)}' " + fname_queuing_all + " | bc) 'BEGIN{cnt=1} {sum+=$1;if (NR>=int(cnt*step)){print cnt,$0;cnt=cnt+1+int(NR-cnt*step)}} END{printf(\"Avg %.3f\\n\", sum/NR)}' " + fname_queuing_all + " > " + os.path.join(prefix, 'queuing_all.log'), shell=True) 
    if args.interarrival:
        sp_interarrival.wait()
        sp_interarrival = sp.Popen("awk -vstep=$(awk 'END{printf(\"%.4f\\n\", NR/10000)}' " + fname_interarrival_all + " | bc) 'BEGIN{cnt=1} {sum+=$1;if (NR>=int(cnt*step)){print cnt,$0;cnt=cnt+1+int(NR-cnt*step)}} END{printf(\"Avg %.2f\\n\", sum/NR)}' " + fname_interarrival_all + " > " + os.path.join(prefix, 'interarrival_all.log'), shell=True) 
    if args.smooth:
        sp_smooth.wait()
        sp_smooth = sp.Popen("awk -vstep=$(awk 'END{printf(\"%.4f\\n\", NR/10000)}' " + fname_smooth_all + " | bc) 'BEGIN{cnt=1} {sum+=$1;if (NR>=int(cnt*step)){print cnt,$0;cnt=cnt+1+int(NR-cnt*step)}} END{printf(\"Avg %.6f\\n\", sum/NR)}' " + fname_smooth_all + " > " + os.path.join(prefix, 'smooth_all.log'), shell=True) 
    if args.total:
        sp_total.wait()
        sp_total = sp.Popen("awk -vstep=$(awk 'END{printf(\"%.4f\\n\", NR/10000)}' " + fname_total_all + " | bc) 'BEGIN{cnt=1} {sum+=$1;if (NR>=int(cnt*step)){print cnt,$0;cnt=cnt+1+int(NR-cnt*step)}} END{printf(\"Avg %.2f\\n\", sum/NR)}' " + fname_total_all + " > " + os.path.join(prefix, 'total_all.log'), shell=True) 
    if args.decode:
        sp_decode.wait()
        sp_decode = sp.Popen("awk -vstep=$(awk 'END{printf(\"%.4f\\n\", NR/10000)}' " + fname_decode_all + " | bc) 'BEGIN{cnt=1} {sum+=$1;if (NR>=int(cnt*step)){print cnt,$0;cnt=cnt+1+int(NR-cnt*step)}} END{printf(\"Avg %.2f\\n\", sum/NR)}' " + fname_decode_all + " > " + os.path.join(prefix, 'decode_all.log'), shell=True) 
    if args.network:
        sp_network.wait()
        sp_network = sp.Popen("awk -vstep=$(awk 'END{printf(\"%.4f\\n\", NR/10000)}' " + fname_network_all + " | bc) 'BEGIN{cnt=1} {sum+=$1;if (NR>=int(cnt*step)){print cnt,$0;cnt=cnt+1+int(NR-cnt*step)}} END{printf(\"Avg %.2f\\n\", sum/NR)}' " + fname_network_all + " > " + os.path.join(prefix, 'network_all.log'), shell=True) 
    
    if args.queuing:
        sp_queuing.wait()
    if args.interarrival:
        sp_interarrival.wait()
    if args.smooth:
        sp_smooth.wait()
    if args.total:
        sp_total.wait()
    if args.decode:
        sp_decode.wait()
    if args.network:
        sp_network.wait()

    # clear up tmp files
    sp_clean = sp.Popen('ls ' + prefix + ' | grep ".tmp" | xargs -i rm ' + os.path.join(prefix, '{}'), shell=True)
    sp_clean.wait()
    endtime = datetime.datetime.now()
    print(f'{args.settings} totalTime: {(endtime - starttime).total_seconds()/60:.2f} minutes')
