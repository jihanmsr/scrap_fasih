import socket

def check_port_open(port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            return s.connect_ex(('127.0.0.1', port)) == 0
    except:
        return False

def main():
    print("Checking ports 9220 to 9230...")
    for port in range(9220, 9231):
        if check_port_open(port):
            print(f" -> Port {port} is OPEN!")
        else:
            print(f" -> Port {port} is closed.")

if __name__ == "__main__":
    main()
