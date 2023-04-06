import numpy as np
import algorithm

PAUSE_FLAG = -1

class TraceLoader:
    def __init__(self, trace_path, min_trace_length):
        self.f = open(trace_path, 'r')
        self.trace_path = trace_path
        self.line_queue = []
        self.queue_max = min_trace_length
        self.arrv_ewma = 0
        self.net_rto = 0.050
       
        self.lastrawline = ['inf' for _ in range(10)]
        while len(self.line_queue) < self.queue_max:
            rawline = self.f.readline().split()
            if not rawline:
                raise Exception("File too short")
            self.line_queue.append(np.array([float(rawline[6]), float(rawline[4]), float(rawline[5]), 0]))
            # arrival timestamp, decoding time, rtt, timeslicing waiting time

            # multiple frames inside the decoder
            dequeue_ts_diff = (float(rawline[6]) + float(rawline[3])) - (float(self.lastrawline[6]) + float(self.lastrawline[3]))
            if self.lastrawline[0] != 'inf' and dequeue_ts_diff < float(self.lastrawline[4]):
                self.line_queue[-2][1] -= (float(self.lastrawline[4]) - dequeue_ts_diff)

            if self.lastrawline[0] != 'inf':
                self.arrv_ewma += min((int(rawline[6]) - int(self.lastrawline[6])) / 1000, self.net_rto)

            # CPU time slicing delay counted in decoding delay
            timeslice_diff = float(rawline[6]) + float(rawline[3]) - \
                    max(int(rawline[6]), float(self.lastrawline[6]) + float(self.lastrawline[3]) + float(self.lastrawline[4]))
            if timeslice_diff > 0:
                self.line_queue[-1][3] = timeslice_diff

            self.lastrawline = rawline
        
        self.arrv_ewma /= (self.queue_max - 1)
        self.arrv_ewma = max(1 / 60, self.arrv_ewma)

        self.timebase = self.line_queue[0][0]   # the timeline in the traceloader
        for line in self.line_queue:
            line[0] -= self.timebase
        self.ptr = -1
        self.trace_end = 0
        self.target_arrv = 1 / 60
        self.arrv_staged = []
        self.lastline = [0, 0, 0, 0]
        
    def load_line(self, target_arrv):
        # first pop up a slowdown value from those staged values.
        # the slowdown_staged stores the list of [slowdown value, effective time (by network delay)]
        # the most recent effective slowdown factor will be used
        if len(self.arrv_staged) > 0:
            update_idx = -1
            for idx in range(len(self.arrv_staged)):
                # check if its effective time is earlier than the current time
                if self.line_queue[1][0] >= self.arrv_staged[idx][1]:
                    update_idx = idx
            if update_idx >= 0:
                for _ in range(update_idx + 1):
                    self.target_arrv = self.arrv_staged[0][0]
                    self.arrv_staged.pop(0)

        # calculate the interpolation position between frames
        # the line_queue maintain several frames for slowdown
        # let self.slowdown == -1 to indicate if we should pause
        try:
            self.ptr += abs(self.target_arrv) / self.arrv_ewma
        except ZeroDivisionError:  # sometimes logs parsed from servers have format issues, print it out
            print("ZeroDivisionError", self.trace_path)
            line = self.lastline
            self.trace_end = True
            return line, self.trace_end

        self.ptr = max(0, min(self.ptr, len(self.line_queue) - 2))
        idx_low = int(np.floor(self.ptr))
        idx_high = idx_low + 1
        ratio_low = idx_high - self.ptr
        ratio_high = self.ptr - idx_low
        line = ratio_low * self.line_queue[idx_low] + ratio_high * self.line_queue[idx_high]

        # if we pause, then we change decode_time to -1 to inform env.step() that this is a pause-frame
        if self.target_arrv < 0:
            line[1] = PAUSE_FLAG  # putting a flag to mark this image will not be encoded, so it won't enqueue to the subsequent buffers.
                
        # ptr adjustment and new line read in
        while self.ptr >= 1:
            self.line_queue.pop(0)
            self.ptr -= 1

        try:
            while len(self.line_queue) < self.queue_max:
                rawline = self.f.readline().split()
                if not rawline:
                    self.trace_end = 1
                    break   
                             
                if int(rawline[6]) < int(self.lastrawline[6]):
                    continue

                self.line_queue.append(np.array([float(rawline[6]) - self.timebase, float(rawline[4]), float(rawline[5]), 0]))
                # arrival timestamp, decoding time, rtt, timeslicing waiting time

                # multiple frames inside the decoder
                dequeue_ts_diff = (float(rawline[6]) + float(rawline[3])) - (float(self.lastrawline[6]) + float(self.lastrawline[3]))
                if dequeue_ts_diff < float(self.lastrawline[4]):
                    self.line_queue[-2][1] -= (float(self.lastrawline[4]) - dequeue_ts_diff)

                # CPU time slicing delay counted in decoding delay
                timeslice_diff = float(rawline[6]) + float(rawline[3]) - \
                        max(int(rawline[6]), float(self.lastrawline[6]) + float(self.lastrawline[3]) + float(self.lastrawline[4]))
                if timeslice_diff > 0:
                    self.line_queue[-1][3] = timeslice_diff

                self.arrv_ewma += 0.033 * (min(self.net_rto, (float(rawline[6]) - float(self.lastrawline[6])) / 1000) - self.arrv_ewma)

                self.lastrawline = rawline
            
            # Attn: the slowdown must be enqueued at last. 
            # This is because the frame-rate adaption would not be effective until the encoder encodes the next frame
            # the frame-rates from both the gaming application and the encoder need to be adjusted, approximately need one frame to take into effect.
            self.arrv_staged.append([target_arrv, self.lastline[0] + self.lastline[2]])  # should be averaged to approximate uplink delay (stalled downlink no influence on uplink)
            self.lastline = line
        except ValueError:  # sometimes logs parsed from servers have format issues, print it out
            print(self.trace_path)
            line = self.lastline
            self.trace_end = True
        return line, self.trace_end
    
    def __del__(self):
        self.f.close()
