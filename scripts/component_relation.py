from math import sqrt
from multiprocessing import Pool
import numpy as np
import scipy.stats as sps
from sklearn.metrics import mutual_info_score
import argparse
import os
# from dtw import *
from fastdtw import fastdtw


def corr_single_trace(param):
    fname, args = param
    if args.mode == 'nd':
        variables = np.loadtxt(os.path.join(args.trace, fname), dtype=int, delimiter=' ', usecols=(5,4))
    elif args.mode == 'nq':
        variables = np.loadtxt(os.path.join(args.trace, fname), dtype=int, delimiter=' ', usecols=(5,3))
    elif args.mode == 'qd':
        variables = np.loadtxt(os.path.join(args.trace, fname), dtype=int, delimiter=' ', usecols=(3,4))
    elif args.mode == 'ds':
        variables = np.loadtxt(os.path.join(args.trace, fname), dtype=int, delimiter=' ', usecols=(4,7))
    total_num = len(variables)

    # pearson's correlation coefficient
    corr_coeff = np.corrcoef(variables[:, 0], variables[:, 1])[0, 1]
    if args.mode == 'ds':
        return [fname, corr_coeff]

    # # normalized cross correlation coefficient
    # ncc = np.correlate((variables[:, 0] - np.mean(variables[:, 0])) / np.std(variables[:, 0]), 
    #     (variables[:, 1] - np.mean(variables[:, 1])) / np.std(variables[:, 1]))
    # if np.abs(ncc.max()) > np.abs(ncc.min()):
    #     ncc_coeff = ncc.max()
    # else:
    #     ncc_coeff = ncc.min()

    # mutual information gain
    mi_coeff = mutual_info_score(variables[:, 0], variables[:, 1])

    # dynamic time warpping (DTW)
    # input amplitude normalization: https://datascience.stackexchange.com/questions/16034/dtw-dynamic-time-warping-requires-prior-normalization
    # fastdtw: https://cs.fit.edu/~pkc/papers/tdm04.pdf
    # fastdtw dist acceleration: https://github.com/slaypni/fastdtw/issues/35
    d, _ = fastdtw(sps.zscore(variables[:, 0]), sps.zscore(variables[:, 1]), dist=2)
    dtw_coeff = d / total_num

    # cramer's v (instead of chi-square test)
    cramer_v = np.zeros((len(args.x_list), len(args.y_list)))
    for x_idx in range(len(args.x_list)):
        for y_idx in range(len(args.y_list)):
            x = args.x_list[x_idx]
            y = args.y_list[y_idx]
            table = np.zeros((2, 2), dtype=int)
            table[0][0] = sum((variables[:, 0] <= x) * (variables[:, 1] <= y))
            table[0][1] = sum((variables[:, 0] <= x) * (variables[:, 1] > y))
            table[1][0] = sum((variables[:, 0] > x) * (variables[:, 1] <= y))
            table[1][1] = sum((variables[:, 0] > x) * (variables[:, 1] > y))
            
            # when the sample size is highly biased, ignore it
            if table.min() <= max(1e-4*total_num, 5):
                chi2_value = 0
            else:
                try:
                    chi2_value = sps.chi2_contingency(table)[0]
                except ValueError:
                    chi2_value = 0
            cramer_v[x_idx, y_idx] = sqrt(chi2_value / total_num)
    np.savetxt(os.path.join(args.result, args.filter, 'stat', 'corr_' + args.mode, 'cramer', fname), cramer_v, fmt='%.3f')
    return [fname, corr_coeff, mi_coeff, dtw_coeff]


def cramer_heatmap(args, cramer_thres):
    fnames = os.listdir(os.path.join(args.result, args.filter, 'stat', 'corr_' + args.mode, 'cramer'))
    count_matrix = np.zeros((len(args.x_list), len(args.y_list)))
    for fname in fnames:
        value_matrix = np.loadtxt(os.path.join(args.result, args.filter, 'stat', 'corr_' + args.mode, 'cramer', fname),
            dtype=float, delimiter=' ')
        count_matrix += value_matrix >= cramer_thres
    count_matrix = count_matrix / len(fnames)
    np.savetxt(os.path.join(args.result, args.filter, 'stat', 'corr_' + args.mode, 'cramer_' + str(cramer_thres) + '.log'), count_matrix, fmt='%.6f')


if __name__ == '__main__':
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--trace', type=str, default='../sim/test-trace')
    parser.add_argument('--result', type=str, default='../sim/test-result')
    parser.add_argument('--filter', type=str, default='wwww', 
        help='devType (UNKNOWN, DESKTOP, LAPTOP, PHONE, PAD, STB, TV), \n' + 
                'netType (NONE, MOBILE, ETHERNET, WIFI, OTHER), \n' + 
                'clientType (WinPC, IOS, MacPC, Android), \n' + 
                'decodeType (SOFTWARE, HARDWARE)')
    parser.add_argument('--flowinfo', type=str, default='../online_data/flowinfo.log')
    parser.add_argument('--mode', choices=['nd', 'nq', 'qd', 'ds'])
    parser.add_argument('--cramer-thres', type=float)
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

    if not os.path.exists(os.path.join(args.result, args.filter, 'stat', 'corr_' + args.mode, 'cramer')):
        os.makedirs(os.path.join(args.result, args.filter, 'stat', 'corr_' + args.mode, 'cramer'))

    fnames = os.listdir(args.trace)
    fnames_new = []
    for fname in fnames:
        sid = fname.split('_')[0]
        if sid in filtered_sid:
            fnames_new.append(fname)
    print(len(fnames_new), '/', len(fnames))
    fnames = fnames_new
    
    if args.mode == 'nd':
        args.x_list = [16, 24, 32, 48, 64, 96, 128, 192, 256]
        args.y_list = [4, 6, 8, 12, 16, 24, 32, 48, 64]
    elif args.mode == 'nq':
        args.x_list = [16, 24, 32, 48, 64, 96, 128, 192, 256]
        args.y_list = [4, 6, 8, 12, 16, 24, 32, 48, 64]
    elif args.mode == 'qd':
        args.x_list = [4, 6, 8, 12, 16, 24, 32, 48, 64]
        args.y_list = [4, 6, 8, 12, 16, 24, 32, 48, 64]

    if args.worker:
        pool = Pool(args.worker)
    else:
        pool = Pool()
    results = pool.map(corr_single_trace, [(fname, args) for fname in fnames])
    pool.close()
    pool.join()

    with open(os.path.join(args.result, args.filter, 'stat', 'corr_' + args.mode, 'corr_coeff.log'), 'w') as f:
        for result in results:
            fname = result[0]
            corr_coeff = result[1]
            if args.mode == 'ds':
                f.write("%s %.3f\n" % (fname, corr_coeff))
            else:
                mi_coeff = result[2]
                dtw_coeff = result[3]
                f.write("%s %.3f %.3f %.3f\n" % (fname, corr_coeff, mi_coeff, dtw_coeff))
    
    if args.mode != 'ds':
        if args.cramer_thres:
            cramer_heatmap(args, args.cramer_thres)
        else:
            for cramer_thres in [0.1, 0.3, 0.5]:
                cramer_heatmap(args, cramer_thres)