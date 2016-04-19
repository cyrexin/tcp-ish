from packet import *
import socket

# packet = Packet(0, 0, 0, 0)
# print packet.create_packet()

# for i in range(0, 0):
#     print i

# print gethostbyname(gethostname())
print getaddrinfo('beijing.clic.cs.columbia.edu', None, AF_INET6)