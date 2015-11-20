from tcp import TcpConnection

t = TcpConnection(src_ip='192.168.0.88', src_port=43702, dst_ip='188.225.32.77', dst_port=8888)

t.connect()
t.send('test')
t.disconnect()