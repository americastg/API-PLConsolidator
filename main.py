from threading import Thread
from client import WebSocketClient

# Start WebSocket Client
ws = WebSocketClient()

# Thread process messages 
ws_thread = Thread(target=ws.run)
ws_thread.start()

# Thread save to file
export_thread = Thread(target=ws.export_PL)
export_thread.start()
