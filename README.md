# Simple TCP-like transport layer protocol

### About the documentation
This document is written in Github format. If you prefer to the more readable version, please visit: https://github.com/cyrexin/tcp-ish

### Brif description
This program is developed by Python 2.7 mainly using the socket module. This simplified TCP-like transport layer protocol supports both IPv4 and IPv6. It provides reliable, in order delivery of a stream of bytes. It can recover from in-network packet loss, packet corruption, packet duplication and packet reordering and should is able to cope with dynamic network delays.


### How to run the code
- The TCP receiver should be invoked as follows:
```
python receiver.py <filename> <listening_port> <sender_IP> <sender_port> <log_filename>

// example
python receiver.py output.jpg 20000 warsaw.clic.cs.columbia.edu 20001 log_receiver.txt
```

- The data sender should be invoked as follows:
```
python sender.py <filename> <remote_IP> <remote_port> <ack_port_num> <log_filename> <window_size>

// example
python sender.py test2.jpg warsaw.clic.cs.columbia.edu 20000 20001 log_sender.txt
```


### The TCP segment structure used
All 20 bytes (that means the Options field is not included) of the standard TCP header are represented. Among them, the "Source port #", "Dest port #", "Sequence number", "Acknowledgement number", "FIN" and the "Internet checksum" fields are actually used. For the other unused fields, the value is set to 0. The pack() and unpack() functions in the struct module are used to construct the TCP segment. Each field is strictly constructed based on its required bits and position. The algorithm to compute the checksum in this program is based on the "checksum1()" function in this page: http://locklessinc.com/articles/tcp_checksum/.

  
### The states typically visited by a sender and receiver
- For sender:
At first, the send base is the sequence number of the first packet. The sender will sent packets back-to-back based on the window size. After each packet is sent, it will update the expected_ack_num = seq_num + len_of_packet (in the transmit() function in sender.py). Then it will go to the next state, waiting for the acknowledgement from the receiver, and the timer will start. In this state, the implementation is like the real TCP, the acknowledgement is cumulative. Therefore, once an acknowledgement is received, the sender knows that the packets with the sequence number prior to the ACK number have been received successfully and hence set the send_base = ack_num. 

If the sender receives an ACK number that is equal to the expected_ack_num, that means all the packets in the window have been received by the receiver. Then the sender can stop the timer and go back to the first state to continue sending packets back-to-back. If after the timeout interval and the sender still has not received an ACK number that is equal to the expected_ack_num, retransmission will be triggered. In the retransmission, only the packets that are in the window with the sequence number starting from the send base will be retransmitted. This state is very much GBN alike.

- For receiver:
Basically the receiver has one single state, that is waiting for the packet from the sender. Whenever a packet comes, it will first verify the checksum. If the checksum is not correct, and this packet will be dropped. Otherwise, it can continue to the followings. The receiver keeps a variable named "exp_seq_num" which is the expected sequence number for the next packet. So if the seq_num of the received packet is equal to the "exp_seq_num", the receiver will update the exp_seq_num = exp_seq_num + length of the packet data. After that, it will send an acknowledge packet back to the sender with the ACK number the same as the updated exp_seq_num. If the receiver receives a packet with FIN flag as 1, that means all the packets have been received and hence the process can stop.


### The loss recovery mechanism
It has the following situations:
- The checksum is not correct: In this case, the receiver will the drop the packet. Therefore, no ACK will be sent to the sender and the "exp_seq_num" is not updated. So if there are packets in the window received by the receiver, they will be dropped too. After timeout, the sender will resend these packets.
 
- The packet is lost: In this case, the receiver never receives this packet. If there are more packets in the window received, the sequence number will not match the "exp_seq_num" and hence they will be dropped. Therefore, after timeout, the sender will resend these packets.

- The packet is duplicated: In this case, the first correct packet will be received by the receiver and then the "exp_seq_num" will be updated. So the sequence number of the duplicate packet will not match that. It will simply be dropped by the receiver.
 
- The packets are out of order: Since the receiver keep track of the "exp_seq_num", the sequence number of the out-of-order packets will obviously not match the "exp_seq_num" and hence they will be dropped. Therefore, after timeout, the sender will resend these packets.


### Additional features
- The timeout interval is calculated as the way in the textbook. Details can be found in the RttUtils class in utils.py. It will never computes the SampleRTT for a segment that has been retransmitted. The starting EstimatedRTT and TimeoutInterval is set to 1.5 seconds and 1.8 seconds respectively, based on the observation that these numbers are way larger than the actual RTT so that unnecessary retransmission will not occur at the first place.
- Although the assignment assumes that the transmission from the receiver to the sender is reliable, the implementation of this program can actually handle the loss or out-of-order ACKs. Since the implementation support cumulative ACK, the loss of the in-between ACKs does not matter. For the other loss of ACK, after timeout, the sender will assume that the corresponding packets are not received by the receiver and will resend them. The send base of the sender only updates when the received ACK number is larger than that, which will handle the out-of-order situation. 


### Test files
It include one short and one long text files, as well as two image files.