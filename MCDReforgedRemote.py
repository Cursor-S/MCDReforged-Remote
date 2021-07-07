import hashlib
import requests
from waitress import serve
from flask import Flask
from ConfigAPI import Config
from mcdreforged.plugin.server_interface import ServerInterface
from mcdreforged.api.all import *
from mcdreforged.api.command import *

PLUGIN_METADATA = {
    'id': 'mcdr_remote',
    'version': '2.0',
    'name': 'MCDReforged-Remote',
    'description': 'A plugin allowing other program to use MCDR features',
    'author': 'Cubik65536',
    'link': 'https://github.com/CraftStarStudio/MCDReforged-Remote',
    'dependencies': {
        'mcdreforged': '>=1.0.0',
        'online_player_api': '*',
        'config_api': '*',
        'json_data_api': '*'
    }
}

DEFAULT_CONFIG = {
    'flask': {
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


# Flask Server App
app = Flask(__name__)
# Minecraft Server object
mcdr_server: ServerInterface
# Authentication Key
authKey = ""


# Flask Web App Routes
@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"


# Flask Server Thread
@ new_thread
def flask(host: str, port: int):
    # Start the Flask Server
    mcdr_server.logger.info("Starting Flask Server...")
    serve(app, host=host, port=port)


# Execute when the server is fully startup
def on_server_startup(server: ServerInterface):
    server.logger.info('Server has started')
    # Make Minecraft Server objet as a global object
    global mcdr_server
    mcdr_server = server
    # Declare global variables for authentication key
    global authKey
    config = Config(PLUGIN_METADATA['name'], DEFAULT_CONFIG)
    # Get authKey from config file and encrypt it
    authKey = hashlib.sha512(
        str(config['flask']['authKey']).encode("utf-8")).hexdigest()
    # Startup the Flask Web App Server
    flask(config['flask']['host'],
          config['flask']['port'])


# Execute when the server is loading
def on_load(server: ServerInterface, old):
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
