from threading import Thread
from client import WebSocketClient

# Start WebSocket Client
ws = WebSocketClient()

user = input('usuário: ')
password = input('senha: ')

# Thread process messages 
ws_thread = Thread(target=ws.run, args=(user, password,))
ws_thread.start()

# Thread save to file
export_thread = Thread(target=ws.export_PL)
export_thread.start()
