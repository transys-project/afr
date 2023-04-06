import os

# variables define
QLEN_STEP = 1
QLEN_UPPER_BOUNT_MAX = 8
QWAIT_STEP = 4 # ms
QWAIT_UPPER_BOUNT_MAX = 64
TARGET_ARRIVAL_INTERVAL = [1.0/60, 1.0/48, 1.0/36, 1.0/24] 

IS_PAUSE = 1
NOT_PAUSE = 0

PAUSE_ACTIVATE_SLOWDOWN = -1
PAUSE_DEACTIVATE_SLOWDOWN = 1

class Algorithm:
    def __init__(self, args, fname):
        self.last_framerate = 60
        self.arrv_ewma = 1 / 60.0           # exponential weighted moving average of the interarrival time
        self.arrv_ewmv = 0                  # exponential weighted moving variance of the interarrival time
        self.arrv_ewm_factor = args.xi_arrv # ewm calculation factor of the arrival process
        self.serv_ewma = 0                  # exponential weighted moving average of the service time
        self.serv_ewmv = 0                  # exponential weighted moving variance of the service time
        self.serv_ewm_factor = args.xi_serv # ewm calculation factor of the service process

        self.W0 = args.wzero                # maintain the queue at wzero on average
        self.q_high = 1                     # q_high for qcn (deprecated) 
        self.q_low = [4, 2]                 # adaptive q_low for qcn (deprecated) 
        self.qwait_high = 16                # q_high for qwait_qcn (transient controller in AFR) 
        self.qwait_low = [64, 14]           # adaptive q_low for qwait_qcn (transient controller in AFR)
        self.rtt_th = [100]                 # rtt threshold to adjust the q_low
        self.outlier = 0.050                # outlier filter in preprocess
        self.net_rto = 0.050                # upper-bound the interarrival time

        self.args = args
        self.fout = open(os.path.join(args.action, args.settings, fname), 'w')

        self.frame_intvl = 0    # delayed frame rate increase
        self.effective_intvl = 1.0 / 60
        self.effective_flag = True
        self.pending_intvl = -1

        self.ms_in_s = 0.001
        self.min_intvl = 1.0 / 60   # 60fps is the maximum frame rate that games can offer
        self.max_intvl = 1.0 / 24

        self.init_flag = True

        # qlen/qwait baselines input to target_arriv mapping sequance
        self.qlen_target_map_seq = []
        self.qwait_target_map_seq = []

        # encoder pause baseline
        self.pause_dimension = args.pause_dimension
        self.pause_stop_threshold = args.pause_stop_threshold
        self.pause_activate_threshold = args.pause_activate_threshold
        # 0 means not pause and 1 means pause
        self.pause_state = NOT_PAUSE
        self.pause_slowdown_stash = 0

    # when new intervals fed to the algorithm, first update the network measurement
    def preprocess(self, arrv_intvl, serv_intvl):
        for intvl in arrv_intvl:
            intvl = intvl * self.ms_in_s
            self.frame_intvl += intvl
            # when an interarrival time is too large, upper bound it to avoid the bias
            intvl = min(intvl, self.net_rto)
            self.arrv_ewma += self.arrv_ewm_factor * (intvl - self.arrv_ewma)
            self.arrv_ewmv += self.arrv_ewm_factor * ((intvl - self.arrv_ewma)**2 - self.arrv_ewmv)

        for intvl in serv_intvl:
            # outlier neglection for the service time
            intvl = intvl * self.ms_in_s
            if intvl < self.outlier:
                self.serv_ewma += self.serv_ewm_factor * (intvl - self.serv_ewma)
                self.serv_ewmv += self.serv_ewm_factor * ((intvl - self.serv_ewma)**2 - self.serv_ewmv)
        
        if self.init_flag:
            self.target_arrv = self.game_bound(self.arrv_ewma)
            self.init_flag = False

    # Heavy-traffic analysis (the stationary controller of AFR)
    def hta(self):
        if self.arrv_ewma < self.ms_in_s:
            arrv_c2 = 0
        else:
            arrv_c2 = self.arrv_ewmv / (self.arrv_ewma**2)

        if self.serv_ewma < self.ms_in_s:
            serv_c2 = 0
        else:
            serv_c2 = self.serv_ewmv / (self.serv_ewma**2)

        t_dec = self.serv_ewma
        self.target_arrv = (((arrv_c2 + serv_c2) / 2) * (t_dec / self.W0) + 1) * t_dec

    # a deprecated baseline
    def qcn(self, qlen, rtt):
        q_low = self.q_low[-1]
        for idx in range(len(self.rtt_th)):
            if rtt <= self.rtt_th[idx]:
                q_low = self.q_low[idx]
                break
        if qlen > q_low:
            reduction = self.min_intvl / self.max_intvl
        elif qlen < self.q_high:
            reduction = 1
        else:
            reduction = ((qlen - self.q_high) * (self.min_intvl / self.max_intvl) + (q_low - qlen))/(q_low - self.q_high)
        self.target_arrv /= reduction

    # the transient controller of AFR
    def qwait_qcn(self, qwait, rtt):
        qwait_low = self.qwait_low[-1]
        for idx in range(len(self.rtt_th)):
            if rtt <= self.rtt_th[idx]:
                qwait_low = self.qwait_low[idx]
                break
        if qwait > qwait_low:
            reduction = self.min_intvl / self.max_intvl
        elif qwait < self.qwait_high:
            reduction = 1
        else:
            reduction = ((qwait - self.qwait_high) * (self.min_intvl / self.max_intvl) + (qwait_low - qwait))/(qwait_low - self.qwait_high)
        self.target_arrv /= reduction

    # mapping the queue length to target frame-rate (interarrival time)
    def qlen_baseline(self, qlen):
        qlen_idx = max(0, int(qlen / QLEN_STEP))
        # get the corresponding target arrival interval in mapping seq
        self.target_arrv = self.qlen_target_map_seq[min(len(self.qlen_target_map_seq)-1, qlen_idx)]
    
    # mapping the queuing delay to target frame-rate (interarrival time)
    def qwait_baseline(self, qwait):
        qwait_idx = max(0, int(qwait / QWAIT_STEP))
        # get the corresponding target arrival interval in mapping seq
        self.target_arrv = self.qwait_target_map_seq[min(len(self.qwait_target_map_seq)-1, qwait_idx)]
    
    # mapping the pause dimention to target pause comand (interarrival time)
    def pause_baseline(self, qlen, qwait):
        input_value = qwait if self.pause_dimension == 'wait' else qlen
        # Moore State Machine
        if input_value > self.pause_activate_threshold and self.pause_state == NOT_PAUSE:
            self.pause_state = IS_PAUSE
        elif input_value < self.pause_stop_threshold and self.pause_state == IS_PAUSE:
            self.pause_state = NOT_PAUSE
        else:
            pass


    # frame-rate should be bounded
    def game_bound(self, arrv):
        arrv = max(self.min_intvl, arrv)
        arrv = min(self.max_intvl, arrv)
        return arrv

    # frame-rate should be quantized to avoid frequent adjustments
    def quantize(self, target_arrv):
        if abs(self.last_framerate - 1 / self.target_arrv) > self.args.frame_rate_level:
            self.last_framerate = round((1 / target_arrv) / self.args.frame_rate_level) * self.args.frame_rate_level
        return 1.0 / self.last_framerate

    # if the frame-rate adjustment is too frequent, this will block those frequent adjustments
    # Specifically, after a frame-rate adjustment, the subsequent frame-adjustments within 
    # self.effective_intvl will be considered non-effective
    def delay_effective(self, target_arrv):
        if target_arrv > self.effective_intvl:  # rate decrease
            self.effective_flag = True
            self.frame_intvl = 0
            self.pending_intvl = -1
            self.effective_intvl = target_arrv
        else:
            if not self.effective_flag: # pending rate increase actions
                if self.frame_intvl > self.args.increase_delay * self.arrv_ewma:
                    self.effective_flag = True
                    self.frame_intvl = 0
                    if target_arrv < self.pending_intvl:    # new higher rate
                        self.effective_intvl = self.pending_intvl
                        self.pending_intvl = target_arrv
                        self.effective_flag = False
                    else:   # less higher rate
                        self.effective_intvl = target_arrv
                        self.pending_intvl = -1
                else:
                    if target_arrv > self.pending_intvl:    # new lower rate
                        self.pending_intvl = target_arrv
            else:
                self.effective_flag = False
                self.frame_intvl = 0
                self.pending_intvl = target_arrv
        return self.effective_intvl

    # the main callback function of algorithm.py
    def predict(self, qlen, qwait, arrv_intvl, serv_intvl, rtt):
        self.target_arrv = self.arrv_ewma   # set the default frame-rate as the 
        self.preprocess(arrv_intvl, serv_intvl)
        if self.args.algorithm == '60fps':
            self.target_arrv = self.min_intvl
        else:
            if self.args.algorithm == 'native':
                self.target_arrv = self.arrv_ewma
            elif self.args.algorithm == 'afr':
                self.hta()
                self.target_arrv = self.game_bound(self.target_arrv)
                self.qwait_qcn(qwait, rtt)
            elif self.args.algorithm == 'afrqcn':
                self.hta()
                self.target_arrv = self.game_bound(self.target_arrv)
                self.qcn(qlen, rtt)
            elif self.args.algorithm == 'hta':
                self.hta()
            elif self.args.algorithm == 'qlen':
                self.qlen_baseline(qlen)
            elif self.args.algorithm == 'qwait':
                self.qwait_baseline(qwait)
            elif self.args.algorithm == 'pause' and self.args.pause_dimension != 'hta':
                self.pause_baseline(qlen, qwait)
                self.target_arrv = self.min_intvl
            elif self.args.algorithm == 'pause' and self.args.pause_dimension == 'hta':
                self.hta()
            elif self.args.algorithm == 'bba':
                self.bba(qlen)
            elif self.args.algorithm == 'txrate':
                self.target_arrv = self.serv_ewma / self.args.rho
            else:
                raise NotImplementedError
            self.target_arrv = self.game_bound(self.target_arrv)
            self.target_arrv = self.quantize(self.target_arrv)
            self.target_arrv = self.delay_effective(self.target_arrv)
        if self.args.algorithm == 'pause' and self.args.pause_dimension != 'hta':
            # pause baselinesP
            if self.pause_state == IS_PAUSE:
                self.target_arrv = - self.target_arrv
            # elif self.pause_state == NOT_PAUSE:
            #     self.slowdown = PAUSE_DEACTIVATE_SLOWDOWN
        if self.args.algorithm == 'pause' and self.args.pause_dimension == 'hta':
            self.pause_slowdown_stash += self.arrv_ewma / self.target_arrv
            self.target_arrv = -self.min_intvl
            if self.pause_slowdown_stash >= 1:
                self.pause_slowdown_stash -= 1
                self.target_arrv = - self.target_arrv
        # print(self.target_arrv)
        self.fout.write("%d\n" % (1 / self.target_arrv))
        return self.target_arrv

    def __del__(self):
        self.fout.close()

'''
map input values to target_arri_interval
return list, each item in the list will be a mapping seqence idx array
'''
def map_seq_idx_array_producer(seq_len):
    result_array = []
    if seq_len < len(TARGET_ARRIVAL_INTERVAL): # can't map seq Surjective onto target_arriv
        return []

    # get every  valid combination  (monotone increase)
    map_seq_partition_comb_list = [0 for _ in range(len(TARGET_ARRIVAL_INTERVAL) - 1)] 
    # -1: n items need (n-1) parting line

    # init
    map_seq_partition_comb_list[-1] = (seq_len-1) -1 # final parting line is set, because [0,(N item),max,max] is equal to [0,(N item),MAX]
    for idx in range(len(map_seq_partition_comb_list)):
        map_seq_partition_comb_list[-1 - idx] = map_seq_partition_comb_list[-1] - idx # start from [0,.., MAX-1, MAX]

    defalt_map_seq_partition_comb_list = [item for item in map_seq_partition_comb_list]
    # get every combination
    while(map_seq_partition_comb_list[0] >= 0):
        seq_idx_array = [0 for _ in range(seq_len)]
        comb_list_idx = 0
        target_arriv_idx = 0
        for idx in range(len(seq_idx_array)): # seq_idx_array[0] = 0
            if idx > map_seq_partition_comb_list[comb_list_idx]:
                comb_list_idx = min(comb_list_idx+1, len(map_seq_partition_comb_list)-1)
                target_arriv_idx = min(target_arriv_idx+1, len(TARGET_ARRIVAL_INTERVAL)-1)
            seq_idx_array[idx] = target_arriv_idx
        result_array.append([item for item in seq_idx_array]) # deep copy

        # next combination
        is_continue = True
        comb_list_moving_offset = len(map_seq_partition_comb_list)-1 - 1
        while(is_continue):
            is_continue = False
            map_seq_partition_comb_list[comb_list_moving_offset] -= 1
            if comb_list_moving_offset == 0:
                if map_seq_partition_comb_list[comb_list_moving_offset] < 0:
                    break
            else:
                if map_seq_partition_comb_list[comb_list_moving_offset] <= map_seq_partition_comb_list[comb_list_moving_offset - 1]: # can't partition in same location
                    map_seq_partition_comb_list[comb_list_moving_offset] = defalt_map_seq_partition_comb_list[comb_list_moving_offset]
                    comb_list_moving_offset -= 1
                    is_continue = True

    return result_array

