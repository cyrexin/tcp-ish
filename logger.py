import time

class Logger:
    def __init__(self, source, destination, log_in_file, log_rtt=False):
        self.source = source
        self.destination = destination
        self.log_in_file = log_in_file
        self.log_rtt = log_rtt

    def set_seq_num(self, seq_num):
        self.seq_num = seq_num

    def set_ack_num(self, ack_num):
        self.ack_num = ack_num

    def set_rtt(self, rtt):
        self.rtt = rtt

    def log(self, file_name=None):
        timestamp = time.time()
        line = str(timestamp) + ' ' + self.source + ' ' + self.destination + ' ' + str(self.seq_num) + ' ' + str(self.ack_num)  #TODO: flags
        if self.log_rtt:
            line += ' ' + str(self.rtt)

        if self.log_in_file:
            file_name.writeln(line)