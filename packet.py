from utils import *

class Packet:

    def __init__(self, source_port, destination_port, seq_num, data, fin=0):
        self.source_port = source_port  # 16-bit source port
        self.destination_port = destination_port  # 16-bit destination port
        self.seq_num = seq_num  # 32-bit sequence number
        self.fin = fin  # 1-bit fin
        self.data = data
        self.checksum = Utils.checksum(data)  #TODO: 16-bit checksum

        self.header_length = 0  #TODO: 4-bit header length

        self.receive_window = 0  # 16-bit, not used
        self.urgent_data_pointer = 0  # 16-bit urgent data pointer, not used
        self.ack_num = 0  # 32-bit acknowledgement number, not used

    def create_packet(self):
        packet = {}

        packet['source_port'] = self.source_port
        packet['destination_port'] = self.destination_port
        packet['seq_num'] = self.seq_num
        packet['fin'] = self.fin
        packet['data'] = self.data
        packet['checksum'] = self.checksum
        packet['header_length'] = self.header_length
        packet['receive_window'] = self.receive_window
        packet['urgent_data_pointer'] = self.urgent_data_pointer
        packet['ack_num'] = self.ack_num

        return packet