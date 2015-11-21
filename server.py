from tcp import TcpConnection

t = TcpConnection(src_ip='0.0.0.0', src_port=8888)

t.listen()