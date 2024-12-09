import socket
import threading
import time

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
    'PAUSE': 0x07,
    'LIGHT_ON': 0x09,
    'LIGHT_OFF': 0x0B,
    'HORIZONTAL_QUERY': 0x51,
    'VERTICAL_QUERY': 0x53,
    'HORIZONTAL_POSITION': 0x4B,
    'VERTICAL_POSITION': 0x4D,
}

POSITIONS = {
    'HORIZONTAL_0': (0x00, 0x00),
    'HORIZONTAL_45': (0x11, 0x94),
    'HORIZONTAL_60': (0x17, 0x70),
    'HORIZONTAL_90': (0x23, 0x28),
    'HORIZONTAL_135': (0x34, 0xBC),
    'HORIZONTAL_180': (0x46, 0x50),
    'HORIZONTAL_270': (0x69, 0x78),
    'HORIZONTAL_315': (0x7B, 0x0C),
    'HORIZONTAL_360': (0x8C, 0xA0),
    'VERTICAL_0': (0x00, 0x00),
    'VERTICAL_45': (0x11, 0x94),
    'VERTICAL_60': (0x17, 0x70),
    'VERTICAL_90': (0x23, 0x28),
    'VERTICAL_135': (0x34, 0xBC),
    'VERTICAL_180': (0x46, 0x50),
}

class PELCO_Functions:
    def __init__(self, ip_address, port=4196, timeout=2):
        self.ip_address = ip_address
        self.port = port
        self.timeout = timeout

    def calculate_checksum(self, command):
        return sum(command) % 256

    def send_command(self, command):
        checksum = self.calculate_checksum(command[1:])  # Exclude the synchronization byte (FF)
        command.append(checksum)
        command_bytes = bytearray(command)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(self.timeout)
            try:
                s.connect((self.ip_address, self.port))
                s.sendall(command_bytes)
                response = s.recv(1024)
                return response, command_bytes
            except socket.timeout:
                return None, command_bytes
            except Exception as e:
                print(f"An error occurred: {e}")
                return None, command_bytes

    def construct_cmd(self, command_name, pan_speed=0x3F, tilt_speed=0x3F, address=0x00):
        if command_name not in COMMANDS:
            print(f"{command_name} not in COMMANDS")
            return False
        command = [0xFF, address, 0x00, COMMANDS[command_name], pan_speed, tilt_speed]
        return self.send_command(command)

    def pantilt_stop(self):
        return self.construct_cmd('STOP')

    def pantilt_move(self, direction, pan_speed=0x3F, tilt_speed=0x3F):
        return self.construct_cmd(direction, pan_speed, tilt_speed)

    def turn_on_light(self):
        return self.construct_cmd('LIGHT_ON', 0x00, 0x02)

    def turn_off_light(self):
        return self.construct_cmd('LIGHT_OFF', 0x00, 0x02)

    def query_horizontal_angle(self):
        response, _ = self.construct_cmd('HORIZONTAL_QUERY')
        if response:
            self.horizontal_angle = self.parse_angle(response[4], response[5])
        return self.horizontal_angle

    def query_vertical_angle(self):
        response, _ = self.construct_cmd('VERTICAL_QUERY')
        if response:
            self.vertical_angle = self.parse_angle(response[4], response[5])
        return self.vertical_angle

    def parse_angle(self, dataH, dataL):
        angle = ((dataH << 8) + dataL) / 100.0
        return angle

    def horizontal_positioning(self, position):
        if position not in POSITIONS:
            print(f"{position} not in POSITIONS")
            return False
        data1, data2 = POSITIONS[position]
        return self.construct_cmd('HORIZONTAL_POSITION')

if __name__ == "__main__":
    controller = PELCO_Functions(ip_address="192.168.137.99")
