import argparse
import os
import subprocess as sp
import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument('--filter', type=str, default='w2w1', 
    help='devType (UNKNOWN, DESKTOP, LAPTOP, PHONE, PAD, STB, TV), \n' + 
         'netType (NONE, MOBILE, ETHERNET, WIFI, OTHER), \n' + 
         'clientType (WinPC, IOS, MacPC, Android), \n' + 
         'decodeType (SOFTWARE, HARDWARE)')
parser.add_argument('--flowinfo', type=str, default='../online_data/flowinfo.log')
parser.add_argument('--flowlist', type=str)
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

if args.flowlist:
    fnames = np.loadtxt(args.flowlist, dtype=str).tolist()

fnames_new = []
for fname in fnames:
    sid = fname.split('_')[0]
    if sid in filtered_sid:
        fnames_new.append(fname)
print(len(fnames_new), '/', len(fnames))