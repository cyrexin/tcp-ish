import sys
import os
import math
import time
import select
from utils import *
from packet import *


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

            self.mss = 576  # set the maximum segment size as 576 bytes TODO: window_size
            self.fin = 0
            self.next_seq_num = 0
            self.expected_ack_num = 0
            self.send_base = self.next_seq_num


            self.sender_socket = Connection.create_udp_socket()

            # sender_ip = gethostbyname(gethostname())
            self.ack_socket = Connection.create_udp_socket()
            Connection.udp_bind(self.ack_socket, '', self.ack_port_num)

            self.file_size = os.stat(filename).st_size
            self.num_packets = math.ceil(float(self.file_size) / self.mss)

            self.reliable_send()
        # except Exception as e:
        #     print "Failed to initiate sender: " + e.message
        #     sys.exit(1)

    def reliable_send(self):
        num_packets = 0
        print 'self.next_seq_num: ' + str(self.next_seq_num)
        print 'self.file_size: ' + str(self.file_size)
        print 'self.num_packets: ' + str(self.num_packets)
        print ''

        while self.next_seq_num < self.file_size:  #TODO: <= or < ?
            for i in range(0, self.window_size):  # back to back send packets
                num_packets += 1
                print 'num_packets: ' + str(num_packets)
                print 'sequence number: ' + str(self.next_seq_num)
                if num_packets == self.num_packets:  # the last packet
                    self.fin = 1

                self.transmit(self.next_seq_num)

            while True:
                ready_to_read, ready_to_write, in_error = \
                select.select(
                    [self.ack_socket],
                    [],
                    [],
                    3)  #TODO: timeout

                if ready_to_read:
                    try:
                        ack_packet = Connection.receive(self.ack_socket)
                        source_port, destination_port, seq_num, ack_num, data_offset, flags, receive_window, checksum, urgent_data_pointer = unpack('HHLLBBHHH', ack_packet[:20])
                        print 'ack from receiver: ' + str(ack_num)

                        self.send_base = ack_num
                        if ack_num == self.expected_ack_num:
                            # self.next_seq_num = ack_num
                            # sample_rtt = time.time() - send_time
                            print 'All the packets from the window have been received correctly!'
                            break
                    except Exception as e:
                        print 'Failed to receive ack from the receiver: ' + e.message
                else:
                    print 'Timeout!!!'
                    self.retransmit(self.send_base, self.next_seq_num)

            print ''

    def create_packet(self, seq_num):
        self.filename.seek(seq_num)
        data = self.filename.read(self.mss)
        packet = Packet(self.ack_port_num, self.remote_port, seq_num, data, self.fin)
        packet = packet.create_packet()
        return packet, len(data)

    def transmit(self, seq_num):
        send_packet, len_of_packet = self.create_packet(seq_num)
        self.expected_ack_num = self.next_seq_num + len_of_packet  # increase the expected sequence number
        self.next_seq_num += len_of_packet  # increase the next sequence number
        print 'len_of_packet: ' + str(len_of_packet)
        print 'expected_ack_num: ' + str(self.expected_ack_num)
        print 'next_seq_num: ' + str(self.next_seq_num)
        # print 'packet:' + str(send_packet)
        send_time = time.time()
        Connection.udp_send(self.sender_socket, send_packet, self.remote_ip, self.remote_port)

        return send_packet, len_of_packet

    def retransmit(self, from_seq, to_seq):
        seq_num = from_seq
        while seq_num <= to_seq:
            send_packet, len_of_packet = self.transmit(seq_num)
            seq_num += len_of_packet


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
