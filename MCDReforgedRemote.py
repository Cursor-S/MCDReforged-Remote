import re
import hashlib
import socket
import threading
from ConfigAPI import Config
from mcdreforged.plugin.server_interface import ServerInterface
from mcdreforged.api.all import *
from mcdreforged.api.command import *

PLUGIN_METADATA = {
    'id': 'mcdr_remote',
    'version': '1.0.0',
    'name': 'MCDReforged-Remote',  # RText component is allowed
    # RText component is allowed
    'description': 'A plugin allowing other program to use MCDR features',
    'author': 'Cubik65536',
    'link': 'https://github.com/CuBitStudio/MCDReforged-Remote/tree/MCDReforgedPlugin',
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
    # authenticate the client
    if (hashlib.sha512(str(authKey).encode("utf-8")).hexdigest() == auth):
        # Survival Test
        if ("Ping" == info):
            # Response Code for Survival Test
            connection.send(str.encode('Pong!'))
        # Server Command
        # elif re.match(r"^\[execute,\s", info) and re.match(r"\]$", info):
        elif ("execute" == info):
            command = data[2]
            mcdr_server.logger.info(
                "Command received from client: %s", command)
            is_rcon_running = mcdr_server.is_rcon_running()
            mcdr_server.logger.info("is_rcon_running: %r", is_rcon_running)
            if is_rcon_running:
                rcon_info = mcdr_server.rcon_query(command)
                mcdr_server.logger.info(
                    "RCON Command Executed! Info: %s", rcon_info)
                connection.send(str.encode(rcon_info))
            else:
                mcdr_server.execute(command)
                connection.send(str.encode(
                    "命令已执行完毕！\n请启用rcon以获得更完善的提示系统！"))
        # list command
        elif ("list" == info):
            online_player_api = mcdr_server.get_plugin_instance(
                'online_player_api')
            player_list = online_player_api.get_player_list()
            player_list_str: str = ""
            for player in player_list:
                player_list_str = player_list_str + "- " + str(player) + "\n"
            list: str = "在线玩家: " + \
                str(len(player_list)) + "\n" + player_list_str
            connection.send(str.encode(list))
        # No Code Found for Action
        else:
            # Response Code for Connected Client
            connection.send(str.encode('1'))
    else:
        # Response code for authentication failed
        connection.send(str.encode('-1'))
    connection.close()
    mcdr_server.logger.info("Connection Closed")


@ new_thread
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
