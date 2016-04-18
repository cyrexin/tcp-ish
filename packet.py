from utils import *
from struct import *

class Packet:

    def __init__(self, source_port, destination_port, seq_num, data, fin=0, ack_num=0):
        self.source_port = source_port  # 16-bit source port
        self.destination_port = destination_port  # 16-bit destination port
        self.seq_num = seq_num  # 32-bit sequence number
        self.fin = fin  # 1-bit fin
        self.data = data
        self.checksum = 0  # 16-bit checksum, should be set as 0 at the first place
        self.ack_num = ack_num  # 32-bit acknowledgement number

        self.data_offset = 0  # 4-bit

        self.receive_window = 0  # 16-bit, not used
        self.urgent_data_pointer = 0  # 16-bit urgent data pointer, not used
        self.urg = 0
        self.ack = 0
        self.psh = 0
        self.rst = 0
        self.syn = 0
        self.reserved = 0  # 6-bit

        self.flags = 0

    def create_packet(self):
        # packet = {}
        #
        # packet['source_port'] = self.source_port
        # packet['destination_port'] = self.destination_port
        # packet['seq_num'] = self.seq_num
        # packet['fin'] = self.fin
        # packet['data'] = self.data
        # packet['checksum'] = self.checksum
        # packet['header_length'] = self.header_length
        # packet['receive_window'] = self.receive_window
        # packet['urgent_data_pointer'] = self.urgent_data_pointer
        # packet['ack_num'] = self.ack_num
        #
        # return packet

        self.flags = self.fin + (self.syn << 1) + (self.rst << 2) + (self.psh << 3) + (self.ack << 4) + (self.urg << 5) + (self.reserved << 6)
        bit_header = pack( '!HHLLBBHHH', self.source_port, self.destination_port, self.seq_num, self.ack_num, self.data_offset, self.flags, self.receive_window, self.checksum, self.urgent_data_pointer)
        # print 'bit_header: ' + str(bit_header)
        self.checksum = Utils.checksum(bit_header + self.data)
        bit_header = pack( '!HHLLBBHHH', self.source_port, self.destination_port, self.seq_num, self.ack_num, self.data_offset, self.flags, self.receive_window, self.checksum, self.urgent_data_pointer)
        packet = bit_header + self.data

        return packet

    @staticmethod
    def get_header(packet):
        source_port, destination_port, seq_num, ack_num, data_offset, flags, receive_window, checksum, urgent_data_pointer = unpack('!HHLLBBHHH', packet[:20])

        return source_port, destination_port, seq_num, ack_num, data_offset, flags, receive_window, checksum, urgent_data_pointer

    @staticmethod
    def get_data(packet):
        return packet[20:]

    @staticmethod
    def verify_checksum(packet):
        source_port, destination_port, seq_num, ack_num, data_offset, flags, receive_window, checksum, urgent_data_pointer = Packet.get_header(packet)
        print 'expected_checksum: ' + str(checksum)
        rcv_checksum = checksum
        checksum = 0  # set this to 0 because now we need to compute the checksum on the receiver side
        bit_header = pack('!HHLLBBHHH', source_port, destination_port, seq_num, ack_num, data_offset, flags, receive_window, checksum, urgent_data_pointer)
        data = Packet.get_data(packet)
        checksum = Utils.checksum(bit_header+data)
        print 'computed checksum: ' + str(checksum)

        return checksum == rcv_checksum
