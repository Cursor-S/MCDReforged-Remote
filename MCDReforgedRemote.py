import hashlib
import socket
import threading
from ConfigAPI import Config
from mcdreforged.plugin.server_interface import ServerInterface
from mcdreforged.api.all import *
from mcdreforged.api.command import *

PLUGIN_METADATA = {
    'id': 'MCDReforgedRemote',
    'version': '1.0.0',
    'name': 'MCDReforged-Remote',  # RText component is allowed
    # RText component is allowed
    'description': 'A plugin allowing other program to use MCDR features',
    'author': 'Cubik65536',
    'link': 'https://git.cubik65536.top/CuBitStudio/MCDReforged-Remote',
    'dependencies': {
        'mcdreforged': '>=1.0.0',
        'online_player_api': '*',
        'config_api': '*',
        'json_data_api': '*'
    }
}

DEFAULT_CONFIG = {
    'tcp_server': {
        'host': '127.0.0.1',
        'port': 64000,
        'authKey': 'password'
    },
    'tcp_remote': {
        'remote_ip': ['127.0.0.1'],
        'remote_port': [65000]
    }
}


mcdr_server: ServerInterface


authKey = ""


def threaded_client(connection):
    # Receive data from client
    bytes = connection.recv(2048)
    # Decote the data
    bytes = bytes.decode("utf8")
    # Split them into auth key and command data
    data = bytes.strip('][').split(', ')
    auth = data[0]
    info = data[1]
    mcdr_server.logger.info("AuthKey received from client: %s", auth)
    mcdr_server.logger.info("Data received from client: %s", info)
    # Just authenticate
    if ("authenticate" == info):
        if (hashlib.sha512(str(authKey).encode("utf-8")).hexdigest() == auth):
            # Response Code for Connected Client
            connection.send(str.encode('1'))
        else:
            # Response code for login failed
            connection.send(str.encode('-1'))
    else:
        connection.send(str.encode('authenticated'))
    connection.close()
    mcdr_server.logger.info("Connection Closed")


@new_thread
def tcp_server(host: str, port: int):
    # Create Socket (TCP) Connection
    ServerSocket = socket.socket(
        family=socket.AF_INET, type=socket.SOCK_STREAM)
    ThreadCount = 0
    try:
        ServerSocket.bind((host, port))
    except socket.error as e:
        mcdr_server.logger.info(str(e))

    mcdr_server.logger.info('[MCDReforgedRemote] Waiting for connection...')
    ServerSocket.listen(5)

    while True:
        Client, address = ServerSocket.accept()
        client_handler = threading.Thread(
            target=threaded_client,
            args=(Client,)
        )
        client_handler.start()
        ThreadCount += 1
        mcdr_server.logger.info('[MCDReforgedRemote] New Client Request')

    ServerSocket.close()


def on_server_startup(server: ServerInterface):
    config = Config(PLUGIN_METADATA['name'], DEFAULT_CONFIG)
    """
    When the server is fully startup
    """
    global mcdr_server
    mcdr_server = server
    global authKey
    authKey = config['tcp_server']['authKey']
    server.logger.info('Server has started')
    tcp_server(config['tcp_server']['host'],
               config['tcp_server']['port'])
