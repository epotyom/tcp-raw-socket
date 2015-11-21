# python TCP module on raw sockets
import socket, sys
from struct import *


class TcpConnection():
    """
    Basic implementation of tcp connection using raw_sockets
    """
    # ip header fields
    def __init__(self, src_ip=None, src_port=None, dst_ip=None, dst_port=None, is_server=False):
        self.src_ip = src_ip
        self.src_port = src_port
        self.dst_ip = dst_ip
        self.dst_port = dst_port
        self.is_server = is_server

        self.tcp_seq = 0
        self.tcp_ack_seq = 0


    @property
    def ip_saddr(self):
        return socket.inet_aton(self.src_ip)

    @property
    def ip_daddr(self):
        return socket.inet_aton(self.dst_ip)

    @property
    def ip_header(self):
        ip_ihl = 5
        ip_ver = 4
        ip_tos = 0
        ip_tot_len = 0  # kernel will fill the correct total length
        ip_id = 54321   #Id of this packet
        ip_frag_off = 0
        ip_ttl = 255
        ip_proto = socket.IPPROTO_TCP
        ip_check = 0    # kernel will fill the correct checksum
        ip_ihl_ver = (ip_ver << 4) + ip_ihl
        return pack('!BBHHHBBH4s4s' , ip_ihl_ver, ip_tos, ip_tot_len, ip_id, ip_frag_off, ip_ttl, ip_proto, ip_check, self.ip_saddr, self.ip_daddr)

    @property
    def tcp_flags(self):
        return self.tcp_fin + (self.tcp_syn << 1) + (self.tcp_rst << 2) + (self.tcp_psh <<3) + (self.tcp_ack << 4) + (self.tcp_urg << 5)

    def tcp_header(self, data='', syn=False, ack=False, psh = False, fin = False):
        # tcp header
        tcp_doff = 5    
        #tcp flags
        tcp_fin = int(fin)
        tcp_syn = int(syn)
        tcp_rst = 0
        tcp_psh = int(psh)
        tcp_ack = int(ack)
        tcp_urg = 0
        tcp_window = socket.htons (2048)   
        tcp_check = 0
        tcp_urg_ptr = 0

        tcp_offset_res = (tcp_doff << 4) + 0
        tcp_flags = tcp_fin + (tcp_syn << 1) + (tcp_rst << 2) + (tcp_psh <<3) + (tcp_ack << 4) + (tcp_urg << 5)

        tcp_header = pack('!HHLLBBHHH' , self.src_port, self.dst_port, self.tcp_seq, self.tcp_ack_seq, tcp_offset_res, tcp_flags,  tcp_window, tcp_check, tcp_urg_ptr)

        source_address = socket.inet_aton( self.src_ip )
        dest_address = socket.inet_aton(self.dst_ip)
        placeholder = 0
        protocol = socket.IPPROTO_TCP
        tcp_length = len(tcp_header) + len(data)

        psh = pack('!4s4sBBH' , source_address , dest_address , placeholder , protocol , tcp_length);
        psh = psh + tcp_header + data;

        tcp_check = self.checksum(psh)

        return pack('!HHLLBBH' , self.src_port, self.dst_port, self.tcp_seq, self.tcp_ack_seq, tcp_offset_res, tcp_flags,  tcp_window) + pack('H' , tcp_check) + pack('!H' , tcp_urg_ptr)

    def connect(self):
        """ install tcp connection """
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)
        except socket.error , msg:
            print 'Socket could not be created. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
            sys.exit()
        # bind socket
        #print self.socket.bind((self.src_ip, self.src_port))
        # send syn
        packet = self.ip_header + self.tcp_header(syn=True)
        self.socket.sendto(packet, (self.dst_ip, 0 ))
        #sys.exit()
        # receive syn ack
        print "lets rcv"
        response, addr = self.socket.recv(1)
        print "rcved"
        self.calcNextSeqNums(response)
        packet = self.ip_header + self.tcp_header(ack=True)
        self.socket.sendto(packet, (self.dst_ip, 0))

    def listen(self):
        """ bind socket and listen for incoming connection """
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)
        except socket.error , msg:
            print 'Socket could not be created. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
            sys.exit()
        # bind socket
        print self.socket.bind((self.src_ip, self.src_port))
        while True:
            print self.socket.recvfrom(65535)

    def disconnect(self):
        """ close tcp connection """
        # send fin
        packet = self.ip_header + self.tcp_header(fin=True)
        self.socket.sendto(packet, (self.dst_ip, 0))

    def send(self, data):
        """ send data over established connection """
        packet = self.ip_header + self.tcp_header(ack=True, psh=True, data=data) + data
        self.socket.sendto(packet, (self.dst_ip, 0))
        # recieve ack
        response, addr = self.socket.recvfrom(65535)
        self.calcNextSeqNums(response)

    def recv(self):
        """ recieve data from socket """
        # receive ack
        response, addr = self.socket.recvfrom(65535)
        # TODO send ACK
        self.calcNextSeqNums(response)
        packet = self.ip_header + self.tcp_header(ack=True)
        self.socket.sendto(packet, (self.dst_ip, 0))

    def checksum(self, msg):
        s = 0
        for i in range(0, len(msg), 2):
            w = ord(msg[i]) + (ord(msg[i+1]) << 8 )
            s = s + w
        s = (s>>16) + (s & 0xffff);
        s = s + (s >> 16);
        s = ~s & 0xffff
        return s

    def calcNextSeqNums(self, rcvddata):
        print rcvddata
        #rcvd_ack = struct.unpack('!H', response[4:6])
        #print "rcvd ack = %s " % rcvd_ack
        #self.tcp_seq = rcvd_ack
        #self.tcp_ack_seq = rcvd_seq + rcvd_len

