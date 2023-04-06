import os
import datetime
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--logdir', type=str, default='../online_data/cut')
parser.add_argument('--filter', type=str, default='wwww', 
    help='devType (UNKNOWN, DESKTOP, LAPTOP, PHONE, PAD, STB, TV), \n' + 
            'netType (NONE, MOBILE, ETHERNET, WIFI, OTHER), \n' + 
            'clientType (WinPC, IOS, MacPC, Android), \n' + 
            'decodeType (SOFTWARE, HARDWARE)')
parser.add_argument('--flowinfo', type=str, default='../online_data/flowinfo.log')
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

fnames = os.listdir(args.logdir)
fnames_new = []
for fname in fnames:
    sid = fname.split('_')[0]
    if sid in filtered_sid:
        fnames_new.append(fname)
print(len(fnames_new), '/', len(fnames))
fnames = fnames_new

playtime = datetime.timedelta(0)
for fname in fnames:
    with open(os.path.join(args.logdir, fname), 'rb') as f:
        first_line = f.readline()
        off = -50
        while True:
            f.seek(off, 2) 
            lines = f.readlines() 
            if len(lines) >= 2:
                last_line = lines[-1] 
                break
            off *= 2
    
    try:
        start_time = datetime.datetime.strptime(first_line.split()[0].decode() + ' ' + first_line.split()[1].decode(), "%Y/%m/%d %H:%M:%S:%f")
        end_time = datetime.datetime.strptime(last_line.split()[0].decode() + ' ' + last_line.split()[1].decode(), "%Y/%m/%d %H:%M:%S:%f")
        playtime += end_time - start_time
    except ValueError as e:
        print(fname, e)
print(playtime)
