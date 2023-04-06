import argparse
import os
import subprocess as sp
import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument('--log', type=str)
parser.add_argument('--result', type=str)
parser.add_argument('--settings', type=str)
parser.add_argument('--filter', type=str, default='w2w1', 
    help='devType (UNKNOWN, DESKTOP, LAPTOP, PHONE, PAD, STB, TV), \n' + 
         'netType (NONE, MOBILE, ETHERNET, WIFI, OTHER), \n' + 
         'clientType (WinPC, IOS, MacPC, Android), \n' + 
         'decodeType (SOFTWARE, HARDWARE)')
parser.add_argument('--condition', type=str)
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

with open('stat.tmp', 'w') as f:
    for fname in fnames:
        f.write(os.path.join(args.log, args.settings, fname) + '\n')

if not os.path.exists(prefix):
    os.makedirs(prefix)

sp_stat = sp.Popen("cat stat.tmp | xargs awk \'{if($" + args.condition[0] + 
    ">" + args.condition[1:] + "){print FILENAME,$0}}\' > " + 
    os.path.join(prefix, args.condition + "-frames.log"), shell=True)
sp_stat.wait()

sp_clean = sp.Popen('rm stat.tmp', shell=True)
sp_clean.wait()