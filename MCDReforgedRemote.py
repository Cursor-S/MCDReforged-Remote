import requests
import hashlib
import socket
import threading
from ConfigAPI import Config
from mcdreforged.plugin.server_interface import ServerInterface
from mcdreforged.api.all import *
from mcdreforged.api.command import *

PLUGIN_METADATA = {
    'id': 'mcdr_remote',
    'version': '1.0.1',
    'name': 'MCDReforged-Remote',
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
    'QQBot': {
        'group_id': ['123456789', '123456123'],
        'host': '127.0.0.1',
        'port': 65000,
    }
}


# Minecraft Server object
mcdr_server: ServerInterface
# Authentication Key
authKey = ""


# Client Process Thread
def threaded_client(connection):
    # Receive data from client
    bytes = connection.recv(2048)
    # Decote the data
    bytes = bytes.decode("utf8")
    # Split them into auth key and command data
    data = bytes.strip('][').split(', ')
    # AuthKey
    auth = data[0]
    # Command
    info = data[1]

    mcdr_server.logger.info("AuthKey received from client: %s", auth)
    mcdr_server.logger.info("Data received from client: %s", info)

    # authenticate the client
    if (hashlib.sha512(str(authKey).encode("utf-8")).hexdigest() == auth):
        # Survival Test
        if ("Ping" == info):
            # Return status code
            connection.send(str.encode('SUCCESS'))
            # Response Code for Survival Test
            connection.send(str.encode('Pong!'))

        # Server Commands
        # Say command
        elif ("say" == info):
            # Get message to send
            msg = data[2]
            # Send the message
            mcdr_server.say(msg)
            # Return status code
            connection.send(str.encode('SUCCESS'))

        # Execute any Minecraft commands
        elif ("execute" == info):
            # Get command
            command = data[2]
            mcdr_server.logger.info(
                "Command received from client: %s", command)

            # Check if MCDR Rcon is enabled
            is_rcon_running = mcdr_server.is_rcon_running()
            mcdr_server.logger.info("is_rcon_running: %r", is_rcon_running)

            # It is
            if is_rcon_running:
                # Execute command
                rcon_info = mcdr_server.rcon_query(command)
                # Have return value
                if not rcon_info:
                    # Return status code
                    connection.send(str.encode('SUCCESS'))
                    connection.send(str.encode('NO_RETURN'))
                else:
                    mcdr_server.logger.info(
                        "RCON Command Executed! Info: %s", rcon_info)
                    # Return status code
                    connection.send(str.encode('SUCCESS'))
                    # Return command return value
                    connection.send(str.encode(rcon_info))
            # It isn't
            else:
                # Execute command via MCDR
                mcdr_server.execute(command)
                # Return status code
                connection.send(str.encode('SUCCESS'))
                # Notification for enable rcon
                connection.send(str.encode(
                    "命令已执行完毕！\n请启用rcon以获得更完善的提示系统！"))

        # List command
        elif ("list" == info):
            # Get online_player_api instance
            online_player_api = mcdr_server.get_plugin_instance(
                'online_player_api')
            # Get player list
            player_list = online_player_api.get_player_list()
            # Create player list string
            player_list_str: str = ""
            # Build player list string
            for player in player_list:
                player_list_str = player_list_str + "- " + str(player) + "\n"
            list: str = "在线玩家: " + \
                str(len(player_list)) + "\n" + player_list_str
            # Return status code
            connection.send(str.encode('SUCCESS'))
            # Return player list
            connection.send(str.encode(list))

        # No Code Found for Action
        else:
            # Response Code for Connected Client
            connection.send(str.encode('NO_COMMAND'))
    else:
        # Response code for authentication failed
        connection.send(str.encode('AUTH_FAILED'))
    # Close client connection
    connection.close()
    mcdr_server.logger.info("Connection Closed")


# TCP Server thread
@ new_thread
def tcp_server(host: str, port: int):
    # Create Socket (TCP) Connection
    ServerSocket = socket.socket(
        family=socket.AF_INET, type=socket.SOCK_STREAM)
    ThreadCount = 0
    # bind host and port
    try:
        ServerSocket.bind((host, port))
    except socket.error as e:
        mcdr_server.logger.info(str(e))

    # Successfully binded
    mcdr_server.logger.info('[MCDReforgedRemote] Waiting for connection...')
    ServerSocket.listen(5)

    # Waiting for Client Connections
    while True:
        # Accept new connection
        Client, address = ServerSocket.accept()
        # Create a new process thread
        client_handler = threading.Thread(
            target=threaded_client,
            args=(Client,)
        )
        client_handler.start()
        ThreadCount += 1
        mcdr_server.logger.info('[MCDReforgedRemote] New Client Request')

    # Close Socket
    ServerSocket.close()


# Execute when the server is loading
def on_load(server: ServerInterface, old):
    config = Config(PLUGIN_METADATA['name'], DEFAULT_CONFIG)

    # !!qq command function
    def qq(src, ctx):
        # Check if the command executor is a player or the console
        player = src.player if src.is_player else 'Console'
        # Send the message to QQ Groups
        send_group_msg(f'[{player}] {ctx["message"]}')

    # Register help message for !!qq command
    server.register_help_message('!!qq <msg>', '向QQ群发送消息')
    # Register !!qq command
    server.register_command(
        # Set command
        Literal('!!qq').
        # Call command function
        then(
            GreedyText('message').runs(qq)
        )
    )


# Execute when the server is fully startup
def on_server_startup(server: ServerInterface):
    server.logger.info('Server has started')
    # Make Minecraft Server objet as a global object
    global mcdr_server
    mcdr_server = server
    # Declare global variables for authentication key
    global authKey
    config = Config(PLUGIN_METADATA['name'], DEFAULT_CONFIG)
    # Get authKey from config file
    authKey = config['tcp_server']['authKey']
    # Startup new TCP Server instance with host and port in config file
    tcp_server(config['tcp_server']['host'],
               config['tcp_server']['port'])


# Send message to QQ Group via HTTP Service.
def send_group_msg(msg):
    # Get HTTP Service ip and port from config file
    config = Config(PLUGIN_METADATA['name'], DEFAULT_CONFIG)
    host = config['QQBot']['host']
    port = config['QQBot']['port']
    # Iterate through the QQ Group IDs set in confg file
    for group in config['QQBot']['group_id']:
        # Send message to the group via POST
        response = requests.post(f'http://{host}:{port}/groupMessage', json={
            'group': group,
            'msg': msg
        })
    # Output response data from HTTP Service
    mcdr_server.logger.info(
        '[MCDReforgedRemote] send_group_msg received: %s', response.text)
