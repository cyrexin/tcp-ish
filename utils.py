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
    def is_valid_ipv6_address(address):
        try:
            inet_pton(AF_INET6, address)
        except error:  # not a valid address
            return False
        return True

    @staticmethod
    def create_udp_socket(is_ipv6=False):
        try:
            if not is_ipv6:
                s = socket(AF_INET, SOCK_DGRAM)
            else:
                s = socket(AF_INET6, SOCK_DGRAM)
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
            print 'Failed to receive data.'
            raise

    @staticmethod
    def udp_send(s, data, host, port):
        s.sendto(data, (host, port))


class RttUtils:
    def __init__(self, sample_rtt):
        self.sample_rtt = sample_rtt
        self.dev_rtt = 0
        self.timeout_interval = 0

    def update(self, estimated_rtt):
        estimated_rtt = 0.875 * estimated_rtt + 0.125 * self.sample_rtt
        self.dev_rtt = 0.75 * self.dev_rtt + 0.25 * abs(self.sample_rtt - estimated_rtt)
        self.timeout_interval = estimated_rtt + 4 * self.dev_rtt
        return self.timeout_interval, estimated_rtt


class SenderOutput:
    def __init__(self):
        self.total_bytes_sent = 0
        self.segments_sent = 0
        self.segments_retransmitted = 0

    def update_total_bytes_sent(self, length):
        self.total_bytes_sent += length

    def update_number_of_segments_sent(self):  # should include the number of retransmission
        self.segments_sent += 1

    def update_segments_retransmitted(self):
        self.segments_retransmitted += 1

    def write(self):
        print 'Delivery completed successfully.'
        print 'Total bytes sent = %s' % str(self.total_bytes_sent)
        print 'Segments sent = %s' % str(self.segments_sent)
        print 'Segments retransmitted = %s' % "{0:.0f}%".format(float(self.segments_retransmitted) / self.segments_sent * 100)

