import os
import numpy as np
import argparse
import datetime
import subprocess as sp
from multiprocessing import Pool


def stall_stats(params):
    fname, args = params
    awk_proc = sp.Popen("awk 'BEGIN{stall=0} {if($5>" + str(args.delay_thres) + "){stall++}} END{print NR,stall/NR}' " + 
        os.path.join(args.log, args.settings, fname), shell=True, stdout=sp.PIPE)
    out, err = awk_proc.communicate()
    awk_proc.wait()
    return [fname, out]


if __name__ == '__main__':
    starttime = datetime.datetime.now()
    parser = argparse.ArgumentParser()
    parser.add_argument('--log', type=str, default='../online_data/logs')
    parser.add_argument('--result', type=str, default='../online_data/results')
    parser.add_argument('--settings', type=str)
    parser.add_argument('--delay-thres', type=int, default=100)
    parser.add_argument('--filter', type=str, default='wwww', 
    help='devType (UNKNOWN, DESKTOP, LAPTOP, PHONE, PAD, STB, TV), \n' + 
            'netType (NONE, MOBILE, ETHERNET, WIFI, OTHER), \n' + 
            'clientType (WinPC, IOS, MacPC, Android), \n' + 
            'decodeType (SOFTWARE, HARDWARE)')
    parser.add_argument('--flowinfo', type=str, default='../online_data/flowinfo.log')
    parser.add_argument('--worker', type=int)
    args = parser.parse_args()

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

    fnames = os.listdir(os.path.join(args.log, args.settings))
    fnames_new = []
    for fname in fnames:
        sid = fname.split('_')[0]
        if sid in filtered_sid:
            fnames_new.append(fname)
    print(len(fnames_new), '/', len(fnames))
    fnames = fnames_new

    if args.worker:
        pool = Pool(args.worker)
    else:
        pool = Pool()
    results = pool.map(stall_stats, [(fname, args) for fname in fnames])
    pool.close()
    pool.join()
    with open(os.path.join(args.result, args.filter, args.settings, 
              'stall_sessions_' + str(args.delay_thres) + '.log'), 'w') as f:
        for result in results:
            fname = result[0]
            out = str(result[1], encoding='utf-8')
            if out[-1] != '\n':
                out +='\n'
            f.write("%s %s" % (fname, out))
    endtime = datetime.datetime.now()
    print(f'{args.settings} TotalTime: {(endtime - starttime).total_seconds()/60:.2f} minutes')
