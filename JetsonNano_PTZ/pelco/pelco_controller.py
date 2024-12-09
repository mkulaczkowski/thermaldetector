import socket
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    DEFAULT_ADDRESS = 0x00
    DEFAULT_SPEED = 0x3F
    STOP_SPEED = 0x00
    RESPONSE_LENGTH = 7  # Typical Pelco-D response length

    def __init__(self, ip_address, port=4196, timeout=0.5):
        """
        Initialize the Pelco-D controller.

        :param ip_address: The IP address of the PTZ device.
        :param port: The TCP port for the PTZ device, default is 4196.
        :param timeout: Socket timeout in seconds.
        """
        self.ip_address = ip_address
        self.port = port
        self.timeout = timeout
        self.sock = None
        self.horizontal_angle = 0.0
        self.vertical_angle = 0.0

        self.connect()

    def connect(self):
        """Establish a TCP connection to the PTZ device."""
        self.close()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(self.timeout)
        try:
            self.sock.connect((self.ip_address, self.port))
            logger.info(f"Connected to PTZ device at {self.ip_address}:{self.port}")
        except socket.error as e:
            logger.error(f"Failed to connect to PTZ device: {e}")
            self.sock = None

    def close(self):
        """Close the TCP connection if open."""
        if self.sock:
            try:
                self.sock.close()
            except socket.error as e:
                logger.warning(f"Error closing socket: {e}")
            self.sock = None

    @staticmethod
    def calculate_checksum(command):
        """Calculate the Pelco-D checksum for a given command."""
        return sum(command) % 256

    def send_command(self, command):
        """
        Send a Pelco-D command without expecting a response.
        Automatically reconnects if needed.
        :param command: List of bytes representing the command (excluding checksum).
        """
        if self.sock is None:
            self.connect()
            if self.sock is None:
                logger.error("Cannot send command - no connection.")
                return

        checksum = self.calculate_checksum(command[1:])
        command.append(checksum)
        command_bytes = bytearray(command)

        try:
            self.sock.sendall(command_bytes)
            logger.debug(f"Sent command: {command_bytes}")
        except (socket.timeout, socket.error) as e:
            logger.error(f"Error sending command: {e}, attempting to reconnect...")
            self.connect()
            if self.sock:
                # Attempt once more after reconnect
                try:
                    self.sock.sendall(command_bytes)
                    logger.debug(f"Sent command after reconnect: {command_bytes}")
                except (socket.timeout, socket.error) as e2:
                    logger.error(f"Failed to send command after reconnect: {e2}")

    def send_command_with_response(self, command):
        """
        Send a Pelco-D command and attempt to read a response.
        :param command: List of bytes representing the command (excluding checksum).
        :return: response bytes or None if no response received.
        """
        self.send_command(command)
        if self.sock is None:
            return None

        try:
            response = self.sock.recv(1024)
            if len(response) >= self.RESPONSE_LENGTH:
                logger.debug(f"Received response: {response}")
                return response[:self.RESPONSE_LENGTH]
        except socket.timeout:
            logger.debug("No response (timeout).")
        except socket.error as e:
            logger.error(f"Error receiving response: {e}")
            self.connect()
        return None

    def construct_cmd(self, direction, pan_speed=DEFAULT_SPEED, tilt_speed=DEFAULT_SPEED, address=DEFAULT_ADDRESS):
        """
        Construct and send a Pelco-D command without expecting a response.
        :param direction: One of the keys in COMMANDS, or 'STOP' if invalid.
        :param pan_speed: Speed for pan movement.
        :param tilt_speed: Speed for tilt movement.
        :param address: Pelco-D address (default 0x00).
        """
        if direction not in COMMANDS:
            direction = 'STOP'

        cmd = [0xFF, address, 0x00, COMMANDS[direction], pan_speed, tilt_speed]
        self.send_command(cmd)

    def construct_cmd_with_response(self, direction, pan_speed=DEFAULT_SPEED, tilt_speed=DEFAULT_SPEED,
                                    address=DEFAULT_ADDRESS):
        """
        Construct and send a Pelco-D command expecting a response.
        :param direction: One of the keys in COMMANDS, or 'STOP' if invalid.
        :param pan_speed: Speed for pan movement.
        :param tilt_speed: Speed for tilt movement.
        :param address: Pelco-D address.
        :return: response bytes or None
        """
        if direction not in COMMANDS:
            direction = 'STOP'

        cmd = [0xFF, address, 0x00, COMMANDS[direction], pan_speed, tilt_speed]
        return self.send_command_with_response(cmd)

    def pantilt_stop(self):
        """Stop all pan/tilt movement."""
        self.construct_cmd('STOP', self.STOP_SPEED, self.STOP_SPEED)

    def pantilt_move(self, direction, pan_speed=DEFAULT_SPEED, tilt_speed=DEFAULT_SPEED):
        """
        Move the PTZ camera in the specified direction with given speeds.
        :param direction: 'UP', 'DOWN', 'LEFT', 'RIGHT', diagonals, or 'STOP'.
        :param pan_speed: speed in the range [0x05,0x3F] typically.
        :param tilt_speed: speed in the range [0x05,0x3F] typically.
        """
        self.construct_cmd(direction, pan_speed, tilt_speed)

    def turn_on_light(self):
        """Send command to turn on the light."""
        self.construct_cmd('LIGHT_ON', 0x00, 0x02)

    def turn_off_light(self):
        """Send command to turn off the light."""
        self.construct_cmd('LIGHT_OFF', 0x00, 0x02)

    def query_horizontal_angle(self):
        """
        Query the horizontal angle of the PTZ.
        Expecting response: FF Addr 00 59 DataH DataL Checksum.
        """
        response = self.construct_cmd_with_response('HORIZONTAL_QUERY', 0x00, 0x00)
        if response and len(response) == self.RESPONSE_LENGTH and response[3] == 0x59:
            dataH = response[4]
            dataL = response[5]
            self.horizontal_angle = self.parse_angle(dataH, dataL)
            return self.horizontal_angle
        return None

    def query_vertical_angle(self):
        """
        Query the vertical angle of the PTZ.
        Expecting response: FF Addr 00 5B DataH DataL Checksum.
        """
        response = self.construct_cmd_with_response('VERTICAL_QUERY', 0x00, 0x00)
        if response and len(response) == self.RESPONSE_LENGTH and response[3] == 0x5B:
            dataH = response[4]
            dataL = response[5]
            self.vertical_angle = self.parse_angle(dataH, dataL)
            return self.vertical_angle
        return None

    @staticmethod
    def parse_angle(dataH, dataL):
        """Parse angle from response data."""
        return ((dataH << 8) + dataL) / 100.0

    def horizontal_positioning(self, position):
        """
        Move the camera to a predefined horizontal position if supported.
        For example: 'HORIZONTAL_90', etc.
        """
        if position not in POSITIONS:
            logger.error(f"Position '{position}' not found in POSITIONS.")
            return False
        # The original code does not actually use data1, data2 from POSITIONS.
        # Add logic here if your device supports direct positioning using these values.
        # For now, just send the HORIZONTAL_POSITION command.
        self.construct_cmd('HORIZONTAL_POSITION')
        return True
