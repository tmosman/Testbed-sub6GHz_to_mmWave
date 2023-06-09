import socket

def getip():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        ipaddr = sock.getsockname()[0]
        sock.close()
    except:
        ipaddr = socket.gethostbyname(socket.gethostname())
        sock.close()
    return ipaddr