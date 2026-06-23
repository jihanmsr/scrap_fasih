import socket

for port in [9223, 9222]:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1.0)
            res = s.connect_ex(('127.0.0.1', port))
            if res == 0:
                print(f"Port {port} is OPEN!")
            else:
                print(f"Port {port} is CLOSED (code: {res})")
    except Exception as e:
        print(f"Error on port {port}: {e}")
