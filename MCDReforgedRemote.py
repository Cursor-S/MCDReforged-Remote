import hashlib
import requests
from waitress import serve
from flask import Flask
from flask import request
from ConfigAPI import Config
from mcdreforged.plugin.server_interface import ServerInterface
from mcdreforged.api.all import *
from mcdreforged.api.command import *

PLUGIN_METADATA = {
    'id': 'mcdr_remote',
    'version': '2.0',
    'name': 'MCDReforged-Remote',
    'description': 'An MCDR plugin implementing the Flask framework. Allowing users to remotely control the Minecraft server or implement two-way chatbots through related APIs.',
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
authenticationKey = ""


# Flask Web App Routes
@app.route("/")
def hello_world():
    return """
           <h3>Welcome to MCDR-Remote!</h3>
           <p>If you see this page, the integrated Flask server of the plugin is running properly and the APIs provided are ready to use.</p>
           <br/>
           <p>MCDReforged-Remote 2.0 Alpha | Powered by <a href="https://www.craftstar.net">CraftStar Studio</a>.</p>
           """


@app.route("/auth", methods=["GET", "POST"])
def authenticate():
    authKey = request.args.get("authKey")
    status_code = 403
    message = "Authenticate Failed!"
    if hashlib.sha512(str(authKey).encode("utf-8")).hexdigest() == authenticationKey:
        status_code = 200
        message = "Authenticated!"
    return {
        "status_code": status_code,
        "message": message
    }


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
    global authenticationKey
    config = Config(PLUGIN_METADATA['name'], DEFAULT_CONFIG)
    # Get authenticationKey from config file and encrypt it
    authenticationKey = hashlib.sha512(
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
