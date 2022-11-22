import json
import time
import requests
import websocket, msgpack
from PL import PLConsolidator

with open('settings.json', 'r') as f:
    config = json.load(f)


def get_token():
    response = requests.post(
        url=f"{config['base_url']}:{config['token_port'] }/connect/token", 
        data= {
            'grant_type': 'password',  # do not change
            'scope': 'externalapi',    # do not change
            'username': config['cred_atgapi']['username'],
            'password': config['cred_atgapi']['password'],
            'client_id': config['cred_atgapi']['client_id'],
            'client_secret': config['cred_atgapi']['client_secret']})
    response.raise_for_status()
    return response.json()['access_token']


class WebSocketClient:
    def __init__(self):
        self.PLConsolidator = PLConsolidator()

    def on_open(self, ws):
        token = get_token()
        ws.send(token)

    def on_message(self, ws, message):
        if message == b'\xff':
            ws.send(b'\xff')
            return
        messageDes = msgpack.unpackb(message)
        self.PLConsolidator.process_message(messageDes)

    def on_error(self, error):
        print(f"Error {error}")

    def run(self):
        print("Running...")
        wsUrl = f"{config['base_url']}:{config['atgapi_port']}/api".replace('http','ws')
        websocket.enableTrace(False)
        ws = websocket.WebSocketApp(f'{wsUrl}/ws/trades',
            on_open = lambda ws: self.on_open(ws),
            on_error = lambda ws,msg: self.on_error(msg),
            on_message = lambda ws,msg: self.on_message(ws, msg))
        ws.run_forever(ping_interval=240, ping_timeout=120)

    def export_PL(self):
        while True:
            time.sleep(config['export_interval_min']*60)
            self.PLConsolidator.export_PL()
    
    
    