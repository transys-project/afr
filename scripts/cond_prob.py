import os
import numpy as np
import argparse
from multiprocessing import Pool

total_k_list = [2, 3, 4, 6, 8, 12, 16]
n_k_list = [2, 3, 4, 6, 8, 12, 16]                  # network
d_k_list = [2, 3, 4, 6, 8, 12, 16, 24, 32]          # decode
q_k_list = [2, 3, 4, 6, 8, 12, 16, 24, 32, 48, 64]  # queue
n_pos = 5
d_pos = 4
q_pos = 3

def cond_single_trace(param):
    fname, args = param

    with open(os.path.join(args.trace, fname), 'r') as f:
        if args.value:
            results = np.zeros((3, 3))
        else:
            n_results = np.zeros((len(total_k_list) + 1, len(n_k_list) + 1), dtype=int)
            d_results = np.zeros((len(total_k_list) + 1, len(d_k_list) + 1), dtype=int)
            q_results = np.zeros((len(total_k_list) + 1, len(q_k_list) + 1), dtype=int)

        for strline in f.readlines():
            numline = strline.split()
            total_cur = int(numline[5]) + int(numline[4]) + int(numline[3])
            n_cur = int(numline[n_pos])
            d_cur = int(numline[d_pos])
            q_cur = int(numline[q_pos])

            if args.value:
                total_val = 100
                com_val = 50
                results += np.array([[n_cur > com_val and total_cur > total_val, n_cur > com_val, total_cur > total_val],
                    [d_cur > com_val and total_cur > total_val, d_cur > com_val, total_cur > total_val],
                    [q_cur > com_val and total_cur > total_val, q_cur > com_val, total_cur > total_val]])

            else:
                total_avg = 22.72
                n_avg = 15.48
                d_avg = 2.83
                q_avg = 0.96

                for total_k_idx in range(len(total_k_list)):
                    total_k = total_k_list[total_k_idx]
                    if total_cur > total_k * total_avg:
                        n_results[total_k_idx, -1] += 1
                        d_results[total_k_idx, -1] += 1
                        q_results[total_k_idx, -1] += 1

                for n_k_idx in range(len(n_k_list)):
                    n_k = n_k_list[n_k_idx]
                    if n_cur > n_k * n_avg:
                        n_results[-1, n_k_idx] += 1
                for d_k_idx in range(len(d_k_list)):
                    d_k = d_k_list[d_k_idx]
                    if d_cur > d_k * d_avg:
                        d_results[-1, d_k_idx] += 1
                for q_k_idx in range(len(q_k_list)):
                    q_k = q_k_list[q_k_idx]
                    if q_cur > q_k * q_avg:
                        q_results[-1, q_k_idx] += 1

                for total_k_idx in range(len(total_k_list)):
                    total_k = total_k_list[total_k_idx]
                    for n_k_idx in range(len(n_k_list)):
                        n_k = n_k_list[n_k_idx]
                        if total_cur > total_k * total_avg and n_cur > n_k * n_avg:
                            n_results[total_k_idx, n_k_idx] += 1
                    for d_k_idx in range(len(d_k_list)):
                        d_k = d_k_list[d_k_idx]
                        if total_cur > total_k * total_avg and d_cur > d_k * d_avg:
                            d_results[total_k_idx, d_k_idx] += 1
                    for q_k_idx in range(len(q_k_list)):
                        q_k = q_k_list[q_k_idx]
                        if total_cur > total_k * total_avg and q_cur > q_k * q_avg:
                            q_results[total_k_idx, q_k_idx] += 1
    if args.value:
        return results
    else:
        return n_results, d_results, q_results
    

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--trace', type=str, default='../sim/test-trace')
    parser.add_argument('--result', type=str, default='../sim/test-result')
    parser.add_argument('--filter', type=str, default='wwww', 
        help='devType (UNKNOWN, DESKTOP, LAPTOP, PHONE, PAD, STB, TV), \n' + 
                'netType (NONE, MOBILE, ETHERNET, WIFI, OTHER), \n' + 
                'clientType (WinPC, IOS, MacPC, Android), \n' + 
                'decodeType (SOFTWARE, HARDWARE)')
    parser.add_argument('--value', action='store_true')
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

    if not os.path.exists(os.path.join(args.result, args.filter, 'stat')):
        os.makedirs(os.path.join(args.result, args.filter, 'stat'))

    fnames = os.listdir(args.trace)
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
    results = pool.map(cond_single_trace, [(fname, args) for fname in fnames])
    pool.close()
    pool.join()

    if args.value:
        np.savetxt(os.path.join(args.result, args.filter, 'stat', 'cond_prob_value_50_100.log'), sum(results), fmt="%d")
    else:
        n_result = sum(n_results for n_results, _, _ in results)
        d_result = sum(d_results for _, d_results, _ in results)
        q_result = sum(q_results for _, _, q_results in results)
        np.savetxt(os.path.join(args.result, args.filter, 'stat', 'cond_prob_n.log'), n_result, fmt="%d")
        np.savetxt(os.path.join(args.result, args.filter, 'stat', 'cond_prob_d.log'), d_result, fmt="%d")
        np.savetxt(os.path.join(args.result, args.filter, 'stat', 'cond_prob_q.log'), q_result, fmt="%d")
