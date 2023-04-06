import os
import argparse
import datetime
import subprocess as sp
from multiprocessing import Pool

def frchange_stat(params):
    fname, args = params
    awk_proc = sp.Popen("awk '{if($1!=last){idx++;last=$1}} END{print NR/idx}' " + 
        os.path.join(args.action, args.settings, fname), shell=True, stdout=sp.PIPE)
    out, err = awk_proc.communicate()
    awk_proc.wait()
    out = float(str(out, encoding='utf-8').split()[0])
    return [fname, out]

    # fname, args = params
    # with open(os.path.join(args.action, args.settings, fname), 'r') as f:
    #     last_line = int(f.readline().split()[0])
    #     cnt = 0
    #     cnt_sum = 0
    #     cnt_idx = 0
    #     while True:
    #         cur_line = f.readline()
    #         if not cur_line:
    #             break
    #         cur_line = int(cur_line.split()[0])
    #         if last_line = cur_line:
    #             cnt += 1
    #         else:
    #             cnt_sum += cnt
    #             cnt_idx += 1
    #             cnt = 0
    #         last_line = cur_line
    # return [fname, cnt_sum / cnt_idx]


if __name__ == '__main__':
    starttime = datetime.datetime.now()
    parser = argparse.ArgumentParser()
    parser.add_argument('--action', type=str, default='../online_data/actions')
    parser.add_argument('--result', type=str, default='../online_data/results')
    parser.add_argument('--settings', type=str)
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

    fnames = os.listdir(os.path.join(args.action, args.settings))
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
    results = pool.map(frchange_stat, [(fname, args) for fname in fnames])
    pool.close()
    pool.join()
    with open(os.path.join(args.result, args.filter, args.settings, 
              'frchange.log'), 'w') as f:
        for result in results:
            f.write("%s %d\n" % (result[0], result[1]))
    endtime = datetime.datetime.now()
    print(f'{args.settings} TotalTime: {(endtime - starttime).total_seconds()/60:.2f} minutes')