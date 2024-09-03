# Listen for requests to port 9000 and forward to https://restservice-neon.niwa.co.nz
import socket
import _thread
import time
import ssl
def do_connect():
    import network
    wlan = network.WLAN(network.STA_IF)
    wlan.ifconfig(('192.168.1.130', '255.255.255.0', '192.168.1.1', '192.168.1.1'))
    wlan.active(True)
    if not wlan.isconnected():
        print('connecting to network...')
        #wlan.connect('Casa de Lima', 'turtle00')
        wlan.connect('Whare de Lima', 'SuperSneaky')
        while not wlan.isconnected():
            pass
    print('network config:', wlan.ifconfig())

do_connect()

bind_ip = '0.0.0.0'
bind_port = 9000

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((bind_ip, bind_port))
server.listen(5)  # max backlog of connections

print("Server listening on port %d" % bind_port)

forward_host = "restservice-neon.niwa.co.nz"
#forward_host = "irrigation.niwa.co.nz"
local_proxy = "localhost:9000"

def handle_client_connection(client_socket):
    neon = None
    start = time.time()
    neon = get_neon_connection()
    print("handle_client_connect() neon="+str(neon))
    client_socket.settimeout(0.1)
    while True:
        try:
            data = client_socket.recv(1024)
            if len(data) > 0:
                print("RECV CLIENT %s" % data)
                # Change host
                datastr = data.decode("utf8")
                relay_data = datastr.replace('Host: ' + local_proxy, 'Host: ' + forward_host)
                neon.write(bytes(relay_data,"utf8"))
                start = time.time()
            else:
                print("RECV CLIENT %s" % data)
        except OSError as e:
            #print("Client Socket timeout")
            pass

        try:
            data = neon.read()
            if len(data) > 0:
                print("RECV NEON  %s" % data)
                datastr = data.decode("utf8")
                relay_data = datastr.replace('Host: ' + forward_host, 'Host: ' + local_proxy)
                client_socket.write(relay_data)
            else:
                client_socket.write("\r\n")
        except OSError as e:
            #print("Neon Socket timeout")
            pass

        if time.time() > start + 30:
            print("Loop activity timeout")
            break

    # Clean up
    try:
        if neon is not None:
            neon.close()
            print("Neon socket closed")
        if client_socket is not None:
            client_socket.close()
            print("Client socket closed")
    except Exception as e:
        print(str(e))


def get_neon_connection():
    try:
        sock = socket.socket()
        sockaddr = socket.getaddrinfo('restservice-neon.niwa.co.nz', 443)[0][-1]
        print("get_neon_connection() sockaddr=" + str(sockaddr))
        sock.connect(sockaddr)
        sock.settimeout(1)
        sock = ssl.wrap_socket(sock, server_hostname="restservice-neon.niwa.co.nz")
        sock.setblocking(True)
        print('Connected to Neon')
        return sock
    except Exception as e:
        import sys
        sys.print_exception(e)


while True:
    client_sock, address = server.accept()
    print('Accepted connection from {}:{}'.format(address[0], address[1]))
    _thread.start_new_thread(handle_client_connection,(client_sock,))
