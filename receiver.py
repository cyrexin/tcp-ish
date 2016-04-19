import sys
import os
from utils import *
from logger import *
from packet import *
from struct import *

class Receiver:
    def __init__(self, filename, listening_port, sender_ip, sender_port, log_filename):
        self.filename = open(filename, 'wb+')
        self.listening_port = listening_port
        self.sender_ip = sender_ip
        self.sender_port = sender_port
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

        self.exp_seq_num = 0
        self.my_seq_num = 0  # the sequence number of the receiver
        # self.buffer = []

        receiver_ip = gethostbyname(gethostname())
        self.logger_sent = Logger(receiver_ip, self.sender_ip, self.log_in_file)
        self.logger_received = Logger(self.sender_ip, receiver_ip, self.log_in_file)

        self.invoke()

    def invoke(self):
        # try:
            receiver_ip = gethostbyname(gethostname())
            receiver_socket = Connection.create_udp_socket(Connection.is_valid_ipv6_address(self.sender_ip))
            Connection.udp_bind(receiver_socket, '', self.listening_port)

            ack_socket = Connection.create_udp_socket(Connection.is_valid_ipv6_address(self.sender_ip))

            print 'Receiver has started on ' + receiver_ip + '...'

            while True:
                rcv_packet = Connection.receive(receiver_socket)
                source_port, destination_port, seq_num, ack_num, data_offset, flags, receive_window, checksum, urgent_data_pointer = Packet.get_header(rcv_packet)
                data = Packet.get_data(rcv_packet)

                self.logger_received.set_seq_num(ack_num)
                self.logger_received.set_ack_num(0)
                self.logger_received.set_fin(flags)
                self.logger_received.log(self.log_filename)

                print 'exp_seq_num: ' + str(self.exp_seq_num)
                print 'packet.seq_num: ' + str(seq_num)
                print 'fin: ' + str(flags)

                if not Packet.verify_checksum(rcv_packet):  # drop the packet and send nothing back to the sender
                    print "Failed to match the checksum. This packet will be dropped."
                else:
                    if self.exp_seq_num == seq_num:
                        self.filename.write(data)
                        self.exp_seq_num += len(data)  # after successfully receive a packet, update the expected sequence number for the next one

                        ack_packet = Packet(self.listening_port, self.sender_port, self.my_seq_num, '0', flags, self.exp_seq_num)
                        ack_packet = ack_packet.create_packet()

                        try:
                            Connection.udp_send(ack_socket, ack_packet, self.sender_ip, self.sender_port)

                            self.my_seq_num += 1  # update the receiver sequence number after the ack packet is sent

                            # update the log
                            self.logger_sent.set_seq_num(0)
                            self.logger_sent.set_ack_num(self.my_seq_num)
                            self.logger_sent.set_fin(flags)
                            self.logger_sent.log(self.log_filename)

                            if flags == 1:
                                print ''
                                print 'Delivery completed successfully!'
                                self.filename.close()
                                sys.exit()

                        except Exception as e:
                            print 'Failed to send the ack number: ' + e.message
                    else:
                        print 'Not the expected sequence number. This packet will be dropped.'


                print ''

        # except Exception as e:
        #     print 'There are some errors: ' + e.message


def main():
    try:
        if len(sys.argv) == 6:
            filename = str(sys.argv[1])
            listening_port = int(sys.argv[2])
            sender_ip = sys.argv[3]
            sender_port = int(sys.argv[4])
            log_filename = str(sys.argv[5])

            Receiver(filename, listening_port, sender_ip, sender_port, log_filename)
        else:
            print """The command is invalid. Usage python receiver.py <filename> <listening_port> <sender_IP> <sender_port> <log_filename>"""
    except KeyboardInterrupt:
        print 'Thanks for using the receiver. It is going to exit now.'
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)

if __name__ == "__main__":
    main()