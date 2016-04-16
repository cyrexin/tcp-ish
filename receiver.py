import sys
import os
from utils import *
from logger import *

class Receiver:
    def __init__(self, filename, listening_port, sender_ip, sender_port, log_filename):
        self.filename = open(filename, 'w+')
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
        self.logger = Logger(self.sender_port, self.listening_port, self.log_in_file)
        self.invoke()

    def invoke(self):
        # try:
            receiver_ip = gethostbyname(gethostname())
            receiver_socket = Connection.create_udp_socket()
            Connection.udp_bind(receiver_socket, '', self.listening_port)

            ack_socket = Connection.create_udp_socket()

            print 'Receiver has started on ' + receiver_ip + '...'

            while True:
                packet = Connection.receive(receiver_socket)
                # print 'packet: ' + str(packet)
                expected_checksum = packet['checksum']
                data = packet['data']
                checksum = Utils.checksum(data)

                print 'checksum: ' + str(checksum)
                if checksum != expected_checksum:
                    print "Failed to match the checksum"
                else:
                    print 'exp_seq_num: ' + str(self.exp_seq_num)
                    print 'packet.seq_num: ' + str(packet['seq_num'])
                    if self.exp_seq_num == packet['seq_num']:
                        self.filename.write(data)
                        self.exp_seq_num += len(data)

                        try:
                            Connection.udp_send(ack_socket, packet['seq_num'], self.sender_ip, self.sender_port)
                            if packet['fin'] == 1:
                                print "All the packets have been received successfully!"
                                self.filename.close()
                        except Exception as e:
                            print 'Failed to send the ack number: ' + e.message

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