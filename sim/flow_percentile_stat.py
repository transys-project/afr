import argparse
import os

SAMPLING_TILE = 100 # in 0.01%

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--percentile')
    parser.add_argument('--filter', type=str)
    parser.add_argument('--result', type=str)

    args = parser.parse_args()

    with open(os.path.join(args.result, args.filter + '-' + str(args.percentile) + '.log'), 'w') as fout:
        for fname in os.listdir(args.result):
            if (args.filter + '.log') not in fname:
                continue
            with open(os.path.join(args.result, fname), 'r') as f:
                while True:
                    line = f.readline().split()
                    if not line:
                        break
                    if args.percentile == 'Avg':
                        if line[0] == args.percentile:
                            fout.write(fname + ' ' + line[1] + '\n')
                            break
                    else:
                        if int(line[0]) >= int(args.percentile) * SAMPLING_TILE:
                            fout.write(fname + ' ' + line[1] + '\n')
                            break
