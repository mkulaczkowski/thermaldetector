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
        return self.send_command('00')

    def ch1_pull_in(self):
        return self.send_command('11')

    def ch1_release(self):
        return self.send_command('21')

    def ch2_pull_in(self):
        return self.send_command('12')

    def ch2_release(self):
        return self.send_command('22')

    def delay_command(self, command, delay_seconds):
        return self.send_command(f"{command}:{delay_seconds}")


if __name__ == "__main__":
    controller = RelayModuleController()

    print("Initial Relay Status:", controller.get_relay_status())

    # Example of pulling in CH1 and CH2
    print("CH1 Pull In:", controller.ch1_pull_in())
    print("Relay Status after Pull In:", controller.get_relay_status())
    print("CH2 Pull In:", controller.ch2_pull_in())

    # Get status after pulling in relays
    print("Relay Status after Pull In:", controller.get_relay_status())

    # Example of releasing CH1 and CH2
    print("CH1 Release:", controller.ch1_release())
    print("CH2 Release:", controller.ch2_release())

    # Get status after releasing relays
    print("Relay Status after Release:", controller.get_relay_status())

    # Example of delaying CH1 pull in by 30 seconds
    print("CH1 Pull In with 30s delay:", controller.delay_command('11', 30))

    # Example of delaying CH2 release by 30 seconds
    print("CH2 Release with 30s delay:", controller.delay_command('22', 30))
    # Example of releasing CH1 and CH2
    print("CH1 Release:", controller.ch1_release())
    print("CH2 Release:", controller.ch2_release())