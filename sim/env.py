import os
import traceloader
import numpy as np

class Environment:
    def __init__(self, args, fname):
        self.time = 0
        self.queue = []
        self.maxsize = args.max_queue_length  # max pre-decoder queue length
        self.decoder_release = 0
        self.timeslicing_release = 0
        # self.arrival_interval_stash = 0
        self.fout = open(os.path.join(args.log, args.settings, fname), 'w')
        self.floss = open(os.path.join(args.result, args.settings, 'frameloss.log'), 'a')
        self.fname = fname

    def step(self, line):
        # if self.time > 1350:
        #     print('debug')
        self.arrival_interval = []
        self.service_interval = []

        # line = [arrival timestamp, decoding time, netts, timeslicing time]
        next_timestamp = line[0]
        qwait = 0
        # Those pause cmds within same encoding cycle (16.6ms in 60fps) will only activate the latest one. \
        # So we just need to activate the latest pause cmd within original encoding cycle.
        # if line[1] == traceloader.PAUSE_FLAG:
        #     self.arrival_interval_stash += next_timestamp - self.time
        # else:
        #     self.arrival_interval.append(next_timestamp - self.time + self.arrival_interval_stash)
        #     self.arrival_interval_stash = 0
        self.arrival_interval.append(next_timestamp - self.time)

        # dequeue
        while len(self.queue) > 0 and self.time + self.decoder_release <= next_timestamp:
            self.time += self.decoder_release
            self.decoder_release = 0
            if self.time + self.timeslicing_release <= next_timestamp: # wait for timeslicing
                self.time += self.timeslicing_release
                dequeue_line = self.queue.pop(0)
                self.decoder_release = dequeue_line[1]
                self.service_interval.append(self.decoder_release)
                if len(self.queue) > 0:
                    self.timeslicing_release = self.queue[0][3]
                else:
                    self.timeslicing_release = 0
                
                self.fout.write(
                    "%.2f" % (dequeue_line[0]) + '\t' +               # arrival timestamp
                    "%.2f" % (dequeue_line[2]) + '\t' +               # net transfer time
                    "%.2f" % (self.time - dequeue_line[0]) +'\t' +    # queuing time
                    "%.2f" % (dequeue_line[1]) + '\t' +               # decoding time
                    "%.2f" % (dequeue_line[2] + self.time - dequeue_line[0] + dequeue_line[1]) + '\n'
                )
                qwait = self.time - dequeue_line[0]
            else:   # store timeslicing intervals
                break
        if self.decoder_release <= next_timestamp - self.time:
            self.timeslicing_release -= min(next_timestamp - self.time - self.decoder_release, self.timeslicing_release)
            self.decoder_release = 0 
        else:
            self.decoder_release -= next_timestamp - self.time

        qlen = len(self.queue)
        qwait = max(qwait, next_timestamp - self.queue[0][0] if len(self.queue) > 0 else 0)
        # check if we need to enqueue
        if line[1] == traceloader.PAUSE_FLAG:
            # self.fout.write(
            #     "%s" %("This frames is under pause, should not be enqueued! ") +
            #     "%.2f" % (line[0]) + '\t' +   # arrival timestamp
            #     "%.2f" % (line[2]) + '\t' +   # net transfer time
            #     "%.2f" % (line[3]) + '\t' +   # queuing time
            #     "%.2f" % (line[1]) + '\t' +   # decoding time
            #     "%.2f" % (line[2] + line[1]) + '\n'
            # )
            pass
        elif len(self.queue) == 0 and self.decoder_release == 0 and line[3] == 0:
            # queue is empty and decoder is available --> no need to queue
            self.decoder_release = line[1]
            self.service_interval.append(self.decoder_release)
            self.fout.write(
                "%.2f" % (line[0]) + '\t' +   # arrival timestamp
                "%.2f" % (line[2]) + '\t' +   # net transfer time
                "%.2f" % (line[3]) + '\t' +   # queuing time
                "%.2f" % (line[1]) + '\t' +   # decoding time
                "%.2f" % (line[2] + line[1]) + '\n'
            )
            qwait = line[3]
        else:
            # enqueue
            if len(self.queue) == 0:
                self.timeslicing_release = line[3]

            if len(self.queue) < self.maxsize:
                self.queue.append(line)
            else:
                # queue overflows, frame loss happens
                self.floss.write(
                    self.fname + '\t' +
                    "%.2f" % (line[0]) + '\t' +   # arrival timestamp
                    "%.2f" % (line[2]) + '\t' +   # net transfer time
                    "%.2f" % (line[1]) + '\t' +   # decoding time
                    "%.2f" % (line[2] + line[1]) + '\n'
                )

        assert(self.timeslicing_release >= 0)
        self.time = next_timestamp
        return qlen, qwait, self.arrival_interval, self.service_interval, line[2]

    def set_ewm_factor(self, new_ewm_factor):
        self.ewm_factor = new_ewm_factor

    def __del__(self):
        self.fout.close()
        self.floss.close()
