import socket
class RelayModuleController:
    def __init__(self, ip_address='192.168.20.100', tcp_port=6722):
        self.ip_address = ip_address
        self.tcp_port = tcp_port

    def send_command(self, command):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((self.ip_address, self.tcp_port))
                s.sendall(command.encode('utf-8'))
                response = s.recv(1024).decode('utf-8')
                return response
        except Exception as e:
            print(f"Error: {e}")
            return None

    def get_relay_status(self):
        status_response = self.send_command('00')
        return self.parse_status_response(status_response)

    def parse_status_response(self, status_response):
        if not status_response or len(status_response) != 8:
            return "Invalid status response"

        status = {}
        for i in range(8):
            channel_status = True if status_response[i] == '1' else False
            status[f'CH{i + 1}'] = channel_status

        return status

    def get_channel_status(self, channel):
        status = self.get_relay_status()
        if isinstance(status, dict):
            return status.get(f'CH{channel}', 'Invalid channel number')
        return status

    def ch1_activate(self):
        return self.send_command('11')

    def ch1_deactivate(self):
        return self.send_command('21')

    def ch2_activate(self):
        return self.send_command('12')

    def ch2_deactivate(self):
        return self.send_command('22')

    def delay_command(self, command, delay_seconds):
        return self.send_command(f"{command}:{delay_seconds}")


if __name__ == "__main__":
    controller = RelayModuleController()

    print("Initial Relay Status:", controller.get_relay_status())

    # Example of activating CH1 and CH2
    print("CH1 Activate:", controller.ch1_activate())
    print("CH2 Activate:", controller.ch2_activate())

    # Get status after activating relays
    print("Relay Status after Activation:", controller.get_relay_status())

    # Example of deactivating CH1 and CH2
    print("CH1 Deactivate:", controller.ch1_deactivate())
    print("CH2 Deactivate:", controller.ch2_deactivate())

    # Get status after deactivating relays
    print("Relay Status after Deactivation:", controller.get_relay_status())

    # Example of delaying CH1 activation by 30 seconds
    print("CH1 Activate with 30s delay:", controller.delay_command('11', 30))

    # Example of delaying CH2 deactivation by 30 seconds
    print("CH2 Deactivate with 30s delay:", controller.delay_command('22', 30))

    # Individual channel status check
    print("CH1 Status:", controller.get_channel_status(1))
    print("CH2 Status:", controller.get_channel_status(2))