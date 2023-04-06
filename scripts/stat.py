import numpy as np
import os
import argparse
import subprocess as sp
from multiprocessing import Pool


def stat(param):
    fname, args = param
       
    if args.queuing:
        fname_queuing = os.path.join(args.result, fname + '_queuing.tmp')
        f_queuing = open(fname_queuing, 'w')
    if args.interarrival:
        last_arrival = -1
        fname_interarrival = os.path.join(args.result, fname + '_interarrival.tmp')
        f_interarrival = open(fname_interarrival, 'w')
    if args.total:
        fname_total = os.path.join(args.result, fname + '_total.tmp')
        f_total = open(fname_total, 'w')

    with open(os.path.join(args.log, fname)) as f:
        while True:
            line = f.readline().split()
            if not line:
                break
            if args.queuing:
                queuing = float(line[3])
                f_queuing.write("%.2f\n" % queuing)
            if args.interarrival:
                if last_arrival < 0:
                    # actually the time after decoding
                    last_arrival = float(line[0]) + float(line[2]) + float(line[3])
                else:
                    inter_arrival = float(line[0]) + float(line[2]) + float(line[3]) - last_arrival
                    f_interarrival.write("%.2f\n" % inter_arrival)
                    last_arrival = float(line[0]) + float(line[2]) + float(line[3])
            if args.total:
                total = float(line[4])
                f_total.write("%.2f\n" % total)
        
    # sort results to calculate cdf
    if args.queuing:
        f_queuing.close()
        sp_queuing = sp.Popen('sort -n ' + fname_queuing + ' -o ' + fname_queuing, shell=True)
    if args.interarrival:
        f_interarrival.close()
        sp_interarrival = sp.Popen('sort -n ' + fname_interarrival + ' -o ' + fname_interarrival, shell=True)
    if args.total:
        f_total.close()
        sp_total = sp.Popen('sort -n ' + fname_total + ' -o ' + fname_total, shell=True)
    
    if args.queuing:
        sp_queuing.wait()
    if args.interarrival:
        sp_interarrival.wait()
    if args.total:
        sp_total.wait()

    # calculate per-log cdf
    if args.queuing:
        sp_queuing = sp.Popen("awk -vstep=$(awk 'END{printf(\"%.4f\\n\", NR/10000)}' " + fname_queuing + " | bc) 'BEGIN{cnt=1} {sum+=$1;if (NR>=int(cnt*step)){print cnt,$0;cnt=cnt+1+int(NR-cnt*step)}} END{printf(\"Avg %.3f\\n\", sum/NR)}' " + fname_queuing + " > " + os.path.join(args.result, fname + '_queuing.log'), shell=True) 
    if args.interarrival:
        sp_queuing = sp.Popen("awk -vstep=$(awk 'END{printf(\"%.4f\\n\", NR/10000)}' " + fname_interarrival + " | bc) 'BEGIN{cnt=1} {sum+=$1;if (NR>=int(cnt*step)){print cnt,$0;cnt=cnt+1+int(NR-cnt*step)}} END{printf(\"Avg %.2f\\n\", sum/NR)}' " + fname_interarrival + " > " + os.path.join(args.result, fname + '_interarrival.log'), shell=True) 
    if args.total:
        sp_queuing = sp.Popen("awk -vstep=$(awk 'END{printf(\"%.4f\\n\", NR/10000)}' " + fname_total + " | bc) 'BEGIN{cnt=1} {sum+=$1;if (NR>=int(cnt*step)){print cnt,$0;cnt=cnt+1+int(NR-cnt*step)}} END{printf(\"Avg %.2f\\n\", sum/NR)}' " + fname_total + " > " + os.path.join(args.result, fname + '_total.log'), shell=True) 

    if args.queuing:
        sp_queuing.wait()
    if args.interarrival:
        sp_interarrival.wait()
    if args.total:
        sp_total.wait()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--log', type=str)
    parser.add_argument('--result', type=str)

    parser.add_argument('--queuing', action='store_true')
    parser.add_argument('--interarrival', action='store_true')
    parser.add_argument('--total', action='store_true')

    parser.add_argument('--threads', type=int, help='Number of parallel threads')
    args = parser.parse_args()

    if not os.path.exists(args.result):
        os.mkdir(args.result)

    fnames = os.listdir(args.log)
    # RELEASE
    if args.threads:
        pool = Pool(args.threads)
    else:
        pool = Pool()
    pool.map(stat, [(fname, args) for fname in fnames])
    pool.close()
    pool.join()

    # DEBUG
    # for fname in fnames:
    #     stat((fname, args))

    # Con'd
    # cat and sort all-long results
    if args.queuing:
        fname_queuing_all = os.path.join(args.result, "queuing_all.tmp")
        sp_queuing = sp.Popen("cat " + os.path.join(args.result, "*_queuing.tmp") + " | sort -n -o " + fname_queuing_all, shell=True)
    if args.interarrival:
        fname_interarrival_all = os.path.join(args.result, "interarrival_all.tmp")
        sp_interarrival = sp.Popen("cat " + os.path.join(args.result, "*_interarrival.tmp") + " | sort -n -o " + fname_interarrival_all, shell=True)
    if args.total:
        fname_total_all = os.path.join(args.result, "total_all.tmp")
        sp_total = sp.Popen("cat " + os.path.join(args.result, "*_total.tmp") + " | sort -n -o " + fname_total_all, shell=True)

    if args.queuing:
        sp_queuing.wait()
    if args.interarrival:
        sp_interarrival.wait()
    if args.total:
        sp_total.wait()

    # calculate all-log cdf
    if args.queuing:
        sp_queuing = sp.Popen("awk -vstep=$(awk 'END{printf(\"%.4f\\n\", NR/10000)}' " + fname_queuing_all + " | bc) 'BEGIN{cnt=1} {sum+=$1;if (NR>=int(cnt*step)){print cnt,$0;cnt=cnt+1+int(NR-cnt*step)}} END{printf(\"Avg %.3f\\n\", sum/NR)}' " + fname_queuing_all + " > " + os.path.join(args.result, 'queuing_all.log'), shell=True) 
    if args.interarrival:
        sp_queuing = sp.Popen("awk -vstep=$(awk 'END{printf(\"%.4f\\n\", NR/10000)}' " + fname_interarrival_all + " | bc) 'BEGIN{cnt=1} {sum+=$1;if (NR>=int(cnt*step)){print cnt,$0;cnt=cnt+1+int(NR-cnt*step)}} END{printf(\"Avg %.2f\\n\", sum/NR)}' " + fname_interarrival_all + " > " + os.path.join(args.result, 'interarrival_all.log'), shell=True) 
    if args.total:
        sp_queuing = sp.Popen("awk -vstep=$(awk 'END{printf(\"%.4f\\n\", NR/10000)}' " + fname_total_all + " | bc) 'BEGIN{cnt=1} {sum+=$1;if (NR>=int(cnt*step)){print cnt,$0;cnt=cnt+1+int(NR-cnt*step)}} END{printf(\"Avg %.2f\\n\", sum/NR)}' " + fname_total_all + " > " + os.path.join(args.result, 'total_all.log'), shell=True) 
    
    if args.queuing:
        sp_queuing.wait()
    if args.interarrival:
        sp_interarrival.wait()
    if args.total:
        sp_total.wait()

    # clear up tmp files
    os.system('rm ' + os.path.join(args.result, '*.tmp'))
