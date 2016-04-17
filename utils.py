from socket import *

class Utils:

    @staticmethod
    def checksum(data):
        size = len(data)
        c_sum = 0
        # handle odd-sized case
        if size & 1:
            size -= 1
            c_sum = ord(data[size])
        else:
            c_sum = 0
        # accumulate checksum
        while size > 0:
            size -= 2
            c_sum += (ord(data[size + 1]) << 8) + ord(data[size])
        # wrap overflow around
        c_sum = (c_sum & 0xffff) + (c_sum >> 16)
        # one's complement
        c_sum = (~c_sum) & 0xffff
        # swap bytes
        c_sum = c_sum >> 8 | ((c_sum & 0xff) << 8)

        return c_sum


class Connection:

    @staticmethod
    def create_udp_socket():
        try:
            s = socket(AF_INET, SOCK_DGRAM)
            return s
        except Exception as e:
            print 'Failed to create the UDP connection: ' + e.message
            raise

    @staticmethod
    def udp_bind(s, host, port):
        try:
            s.bind((host, port))
        except Exception as e:
            print 'Failed to bind on port: ' + str(port)
            raise

    @staticmethod
    def receive(s):
        try:
            data = s.recvfrom(65535)[0]
            # print data
            return data
        except:
            print "Failed to receive data."
            raise

    @staticmethod
    def udp_send(s, data, host, port):
        s.sendto(data, (host, port))


class RttUtils:
    def __init__(self, sample_rtt):
        self.sample_rtt = sample_rtt
        self.dev_rtt = 0
        self.timeout_interval = 3 * sample_rtt  #TODO: a fixed value for initial experimentation

    def update(self, estimated_rtt):
        estimated_rtt = 0.875 * estimated_rtt + 0.125 * self.sample_rtt
        self.dev_rtt = 0.75 * self.dev_rtt + 0.25 * abs(self.sample_rtt - estimated_rtt)
        self.timeout_interval = estimated_rtt + 4 * self.dev_rtt
        return self.timeout_interval, estimated_rtt
