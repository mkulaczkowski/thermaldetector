import socket

COMMANDS = {
    'STOP': 0x00,
    'UP': 0x08,
    'DOWN': 0x10,
    'LEFT': 0x04,
    'RIGHT': 0x02,
    'UP-RIGHT': 0x0A,
    'UP-LEFT': 0x0C,
    'DOWN-RIGHT': 0x12,
    'DOWN-LEFT': 0x14,
}

class PELCO_Functions:
    def __init__(self, ip_address, port=4196, timeout=0.5):
        self.ip_address = ip_address
        self.port = port
        self.timeout = timeout

    def calculate_checksum(self, command):
        return sum(command) % 256

    def send_command(self, command):
        checksum = self.calculate_checksum(command[1:])  # exclude 0xFF
        command.append(checksum)
        command_bytes = bytearray(command)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(self.timeout)
            try:
                s.connect((self.ip_address, self.port))
                s.sendall(command_bytes)
                # Pelco-D might not always respond, often one-way commands
                # But if it does, we could read response:
                response = s.recv(1024)
            except socket.timeout:
                pass
            except Exception as e:
                print(f"Pelco command error: {e}")

    def construct_cmd(self, direction, pan_speed=0x3F, tilt_speed=0x3F, address=0x00):
        if direction not in COMMANDS:
            direction = 'STOP'
        cmd = [0xFF, address, 0x00, COMMANDS[direction], pan_speed, tilt_speed]
        self.send_command(cmd)

    def pantilt_stop(self):
        print('STOP')
        self.construct_cmd('STOP', 0x00, 0x00)

    def pantilt_move(self, direction, pan_speed=0x3F, tilt_speed=0x3F):
        print(f'{direction}, {pan_speed}, {tilt_speed}')
        self.construct_cmd(direction, pan_speed, tilt_speed)
