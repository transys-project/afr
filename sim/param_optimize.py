import argparse
import os


def argument_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i',
                        '--interarrival_percentail',
                        type=int,
                        default='5000')
    parser.add_argument('-q', '--queuing_percentail', type=int, default='9900')
    parser.add_argument('-c', '--config', choices=['run', 'stat', 'all'], default='stat')
    args = parser.parse_args()
    return args


def pause_len_run(len_params, delete_log=True):
    for i, j in len_params:
        setting_name = f'pause_len_{i}_{j}'
        os.system(
            f'python main.py --trace ../online_data/cut --log ../online_data/log --action ../online_data/action --result ../online_data/result --algorithm pause --mode release --pause_dimension len --pause_stop_threshold {i} --pause_activate_threshold {j} --random_sample 2000'
        )
        os.system(
            f'python stat.py --log ../online_data/log --result ../online_data/result --filter w20w --queuing --interarrival --smooth --total --settings {setting_name} --flowinfo ../online_data/flowinfo.log'
        )
        if delete_log:
            os.system(
                f'rm -rf ../online_data/log/{setting_name} ../online_data/action/{setting_name}'
            )
    print('qlen done!')


def pause_wait_run(wait_params, delete_log=True):
    for i, j in wait_params:
        setting_name = f'pause_wait_{i}_{j}'
        os.system(
            f'python main.py --trace ../online_data/cut --log ../online_data/log --action ../online_data/action --result ../online_data/result --algorithm pause --mode release --pause_dimension wait --pause_stop_threshold {i} --pause_activate_threshold {j} --random_sample 2000'
        )
        os.system(
            f'python stat.py --log ../online_data/log --result ../online_data/result --filter w20w --queuing --interarrival --smooth --total --settings {setting_name} --flowinfo ../online_data/flowinfo.log'
        )
        if delete_log:
            os.system(
                f'rm -rf ../online_data/log/{setting_name} ../online_data/action/{setting_name}'
            )
    print('qwait done!')


def pause_len_stat(len_params,
                   interarrival_percentail=5000,
                   queuing_percentail=9900):
    for i, j in len_params:
        setting_name = f'pause_len_{i}_{j}'
        with open(
                os.path.join('../online_data/result/w20w', setting_name,
                             'interarrival_all.log')) as f:
            buf = f.readlines()
            interarrival = buf[interarrival_percentail - 1].replace(
                '\n', '').split(' ')[1]
        with open(
                os.path.join('../online_data/result/w20w', setting_name,
                             'queuing_all.log')) as f:
            buf = f.readlines()
            queuing = buf[queuing_percentail - 1].replace('\n',
                                                          '').split(' ')[1]
        yield i, j, interarrival, queuing


def pause_wait_stat(wait_params,
                    interarrival_percentail=5000,
                    queuing_percentail=9900):
    for i, j in wait_params:
        setting_name = f'pause_wait_{i}_{j}'
        with open(
                os.path.join('../online_data/result/w20w', setting_name,
                             'interarrival_all.log')) as f:
            buf = f.readlines()
            interarrival = buf[interarrival_percentail - 1].replace(
                '\n', '').split(' ')[1]
        with open(
                os.path.join('../online_data/result/w20w', setting_name,
                             'queuing_all.log')) as f:
            buf = f.readlines()
            queuing = buf[queuing_percentail - 1].replace('\n',
                                                          '').split(' ')[1]
        yield i, j, interarrival, queuing


if __name__ == '__main__':
    args = argument_parser()
    len_params = []
    for i in range(1, 9):
        for j in range(i, 9):
            len_params.append((i, j))

    wait_params = []
    for i in range(10, 120, 10):
        for j in range(i, 120, 10):
            wait_params.append((i, j))

    # Run
    if args.config == 'run' or args.config == 'all':
        print('pause len run')
        pause_len_run(len_params)
        print('pause wait run')
        pause_wait_run(wait_params)

    # Stat
    if args.config == 'stat' or args.config == 'all':
        print('pause len stat')
        for i, j, interarrival, queueing in pause_len_stat(
                len_params, args.interarrival_percentail, args.queuing_percentail):
            print(i, j, interarrival, queueing)
        print('pause wait stat')
        for i, j, interarrival, queueing in pause_wait_stat(
                wait_params, args.interarrival_percentail,
                args.queuing_percentail):
            print(i, j, interarrival, queueing)
