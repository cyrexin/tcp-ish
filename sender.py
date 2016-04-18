import sys
import os
import math
import datetime
import select
from utils import *
from packet import *
from logger import *


class Sender:
    def __init__(self, filename, remote_ip, remote_port, ack_port_num, log_filename, window_size=1):
        # try:
            self.filename = open(filename, 'rb')
            self.remote_ip = remote_ip
            self.remote_port = remote_port
            self.ack_port_num = ack_port_num
            self.window_size = window_size
            if log_filename != 'stdout':
                try:
                    self.log_filename = open(log_filename, 'w+')
                except Exception as e:
                    print "unable to create file: " + e.message
                    sys.exit(1)
                self.log_in_file = True
            else:
                self.log_filename = None
                self.log_in_file = False

            self.mss = 576  # set the maximum segment size as 576 bytes
            self.fin = 0
            self.next_seq_num = 0
            self.expected_ack_num = 0
            self.send_base = self.next_seq_num
            self.last_successfully_received_packet_num = 0

            self.sender_socket = Connection.create_udp_socket()

            sender_ip = gethostbyname(gethostname())
            self.ack_socket = Connection.create_udp_socket()
            Connection.udp_bind(self.ack_socket, '', self.ack_port_num)

            self.file_size = os.stat(filename).st_size
            self.num_packets = math.ceil(float(self.file_size) / self.mss)

            self.rtt = {}
            self.estimated_rtt = 1
            self.timeout_interval = 1.5
            self.retransmission_occurred = False

            self.logger_sent = Logger(sender_ip, self.remote_ip, self.log_in_file, True)
            self.logger_received = Logger(self.remote_ip, sender_ip, self.log_in_file)
            self.sender_output = SenderOutput()

            self.reliable_data_transfer()

        # except Exception as e:
        #     print "Failed to initiate sender: " + e.message
        #     sys.exit(1)

    def reliable_data_transfer(self):
        packet_num = 0
        print 'self.next_seq_num: ' + str(self.next_seq_num)
        print 'self.file_size: ' + str(self.file_size)
        print 'self.num_packets: ' + str(self.num_packets)
        print ''

        while self.next_seq_num < self.file_size:
            for i in range(0, self.window_size):  # back to back send packets
                if self.next_seq_num >= self.file_size:
                    pass
                else:
                    # print 'sequence number: ' + str(self.next_seq_num)

                    # if num_packets == self.num_packets:  # the last packet
                    #     self.fin = 1

                    self.transmit(self.next_seq_num, packet_num)

                    packet_num += 1

            while True:
                ready_to_read, ready_to_write, in_error = \
                select.select(
                    [self.ack_socket],
                    [],
                    [],
                    self.timeout_interval)

                if ready_to_read:
                    try:
                        ack_packet = Connection.receive(self.ack_socket)
                        source_port, destination_port, seq_num, ack_num, data_offset, flags, receive_window, checksum, urgent_data_pointer = unpack('!HHLLBBHHH', ack_packet[:20])
                        print 'ack from receiver: ' + str(ack_num)

                        if not self.retransmission_occurred:
                            sample_rtt = (datetime.datetime.now() - self.rtt[seq_num]).total_seconds()
                            print 'sample_rtt: ' + str(sample_rtt)
                            if self.estimated_rtt == 1:
                                self.estimated_rtt = sample_rtt
                            rtt_utils = RttUtils(sample_rtt)
                            self.timeout_interval, self.estimated_rtt = rtt_utils.update(self.estimated_rtt)
                            print 'estimated_rtt: ' + str(self.estimated_rtt)
                            print 'timeout_interval: ' + str(self.timeout_interval)

                        # log ACK packet
                        self.logger_received.set_seq_num(0)  # for received packets, the seq_num should be 0
                        self.logger_received.set_ack_num(seq_num)  # the ack_num should be in terms of the number of packet
                        # self.logger.set_rtt(send_time)
                        self.logger_received.set_fin(flags)
                        self.logger_received.log(self.log_filename)

                        self.send_base = ack_num
                        self.last_successfully_received_packet_num = seq_num
                        if ack_num == self.expected_ack_num:
                            # self.next_seq_num = ack_num
                            # sample_rtt = time.time() - send_time
                            print 'All the packets from the window have been received correctly!'
                            self.retransmission_occurred = False

                            if flags == 1:  # the receiver has received all the packets
                                print ''
                                self.sender_output.write()

                            break
                    except Exception as e:
                        print 'Failed to receive ack from the receiver: ' + e.message
                else:
                    print ''
                    print 'Timeout!!!'
                    print 'send base: ' + str(self.send_base)
                    print 'last successfully received packet number: ' + str(self.last_successfully_received_packet_num)
                    print 'next_seq_num: ' + str(self.next_seq_num)
                    self.retransmission_occurred = True
                    self.retransmit(self.send_base, self.next_seq_num)

            print ''

    def create_packet(self, seq_num, packet_num):
        self.filename.seek(seq_num)
        data = self.filename.read(self.mss)

        if seq_num + len(data) == self.file_size:
            self.fin = 1
        else:
            self.fin = 0

        packet = Packet(self.ack_port_num, self.remote_port, seq_num, data, self.fin, packet_num)
        packet = packet.create_packet()
        return packet, len(data)

    def transmit(self, seq_num, packet_num, is_retransmission=False):
        print 'packet_num: ' + str(packet_num)

        send_packet, len_of_packet = self.create_packet(seq_num, packet_num)

        send_time = datetime.datetime.now()

        if not is_retransmission:
            self.rtt[packet_num] = send_time  # the sample RTT should only be calculated for the original transmission
            self.expected_ack_num = self.next_seq_num + len_of_packet  # increase the expected sequence number
            self.next_seq_num += len_of_packet  # increase the next sequence number

        # making log
        self.logger_sent.set_seq_num(packet_num)  # seq_num should be in terms of the number of packet
        self.logger_sent.set_ack_num(0)  # for sent packets, the ack_num should always be 0
        self.logger_sent.set_rtt(self.estimated_rtt)
        self.logger_sent.set_fin(self.fin)
        self.logger_sent.log(self.log_filename)

        print 'len_of_packet: ' + str(len_of_packet)
        print 'expected_ack_num: ' + str(self.expected_ack_num)
        print 'seq_num: ' + str(seq_num)
        # print 'packet:' + str(send_packet)

        Connection.udp_send(self.sender_socket, send_packet, self.remote_ip, self.remote_port)

        # update the stats
        self.sender_output.update_number_of_segments_sent()
        self.sender_output.update_total_bytes_sent(len(send_packet))

        return send_packet, len_of_packet

    def retransmit(self, from_seq, to_seq):
        seq_num = from_seq
        resent_packet_num = self.last_successfully_received_packet_num + 1
        while seq_num < to_seq:
            send_packet, len_of_packet = self.transmit(seq_num, resent_packet_num, True)

            self.sender_output.update_segments_retransmitted()

            seq_num += len_of_packet
            resent_packet_num += 1


def main():
    try:
        if len(sys.argv) == 6 or len(sys.argv) == 7:  # window_size is optional
            filename = str(sys.argv[1])
            remote_ip = sys.argv[2]
            remote_port = int(sys.argv[3])
            ack_port_num = int(sys.argv[4])
            log_filename = str(sys.argv[5])

            window_size = 1
            if len(sys.argv) == 7:
                window_size = int(sys.argv[6])

            Sender(filename, remote_ip, remote_port, ack_port_num, log_filename, window_size)
        else:
            print """The command is invalid. Usage: python sender.py <filename> <remote_IP> <remote_port> <ack_port_num> <log_filename> <window_size>"""
        sys.exit(1)
    except KeyboardInterrupt:
        print 'Thanks for using the sender. Now it is going to exit now.'
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)

if __name__ == "__main__":
    main()
