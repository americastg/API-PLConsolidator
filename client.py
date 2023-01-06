from datetime import datetime
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
        self.incomingMsgs = []

    def on_open(self, ws):
        token = get_token()
        ws.send(token)

    def on_message(self, ws, message):
        if message == b'\xff':
            ws.send(b'1')
            return
        messageDes = msgpack.unpackb(message)
        self.PLConsolidator.process_message(messageDes)

    def on_error(self, error):
       print(f'{datetime.now():%H:%M:%S}: Error {error}')

    def on_close(self, status, msg):
        print(f'{datetime.now():%H:%M:%S}: connection close -> status: {status} / msg: {msg}')

    def run(self):
        print(f'{datetime.now():%H:%M:%S}: Running...')
        wsUrl = f"{config['base_url']}:{config['atgapi_port']}/api".replace('http','ws')
        websocket.enableTrace(False)
        ws = websocket.WebSocketApp(f'{wsUrl}/ws/trades',
            on_open = lambda ws: self.on_open(ws),
            on_error = lambda ws,msg: self.on_error(msg),
            on_message = lambda ws,msg: self.on_message(ws, msg),
            on_close = lambda ws,status,msg: self.on_close(status,msg))
        ws.run_forever()

    def export_PL(self):
        while True:
            time.sleep(config['export_interval_min']*60)
            self.PLConsolidator.export_PL()
    
    
    