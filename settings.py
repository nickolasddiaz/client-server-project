import configparser
import ipaddress


class Settings:
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config.read('config.ini')
        self.CLIENT_IP : str = self.config.get('DEFAULT', 'CLIENT_IP', fallback='localhost')

        self.SERVER_IP: str = self.config.get('DEFAULT', 'SERVER_IP', fallback='0.0.0.0')

        self.PORT: int = self.config.getint('DEFAULT', 'PORT', fallback=4453)

        self.USERNAME : str = self.config.get('DEFAULT', 'USERNAME', fallback='admin')
        self.PASSWORD : str = ""

        self.COMPRESS_LVL: int = self.config.getint('DEFAULT', 'COMPRESS_LEVEL', fallback=5) # can only be from 0-7

        self.SERVER_ADDR: tuple[str, int] = (self.SERVER_IP, self.PORT)
        self.CLIENT_ADDR: tuple[str, int] = (self.CLIENT_IP, self.PORT)


    def save_changes(self):
        self.config['DEFAULT'] = {'CLIENT_IP'   : self.CLIENT_IP,
                                  'PORT'        : self.PORT,
                                  'SERVER_IP'   : self.SERVER_IP,
                                  'USERNAME'    : self.USERNAME,
                                  'COMPRESS_LVL': self.COMPRESS_LVL
                                  }
        with open('config.ini', 'w') as configfile:
            self.config.write(configfile)


    def set_client_addr(self, client_ip: str, client_port: int) -> bool:
        if not (self.is_valid_ipv4(client_ip) and self.is_valid_port(client_port)):
            return False

        self.CLIENT_IP = client_ip
        self.PORT = client_port
        self.CLIENT_ADDR = (client_ip, client_port)

        return True

    def set_server_addr(self, server_ip: str, server_port: int) -> bool:
        if not (self.is_valid_ipv4(server_ip) and self.is_valid_port(server_port)):
            return False

        self.SERVER_IP = server_ip
        self.PORT = server_port
        self.SERVER_ADDR = (server_ip, server_port)

        return True



    @staticmethod
    def is_valid_ipv4(ip_string: str) -> bool:
        """
        Checks if a given string represents a valid IPv4 address.
        """
        if ip_string.lower() == "localhost":
            return True

        try:
            ipaddress.IPv4Address(ip_string)
            return True
        except ipaddress.AddressValueError:
            return False
        except ValueError:
            return False

    @staticmethod
    def is_valid_compress_lvl(level: int) -> bool:
        """Checks if the compress level is in the valid range."""
        return isinstance(level, int) and 0 <= level <= 7

    @staticmethod
    def is_valid_port(port: int) -> bool:
        """Checks if a given port is in the valid range."""
        return isinstance(port, int) and 0 < port <= 65535