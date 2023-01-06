from dataclasses import dataclass
from datetime import datetime
import csv
import os
from md import get_symbol_info

FOLDER = 'PL_files'

@dataclass
class PLInfo:
    broker: str
    account: str
    user: str
    exchange: str 
    exposure: float = 0
    quantity: int = 0
    n_trades: int = 0


class PLConsolidator:
    def __init__(self):
        self.buy_PL: dict[str, PLInfo] = {}
        self.sell_PL: dict[str, PLInfo] = {}
        self.md_info = {}

    def process_message(self, msg):
        # trades do dia
        date = datetime.strptime(msg['TradeDate'].split('T')[0], '%Y-%m-%d').date()
        if date < datetime.today().date() or msg['StrategyID'].startswith('bi'): 
            return

        # obtém info do papel
        if msg['Symbol'] not in self.md_info:
            self.md_info[msg['Symbol']] = get_symbol_info(msg['Symbol'])
        md = self.md_info[msg['Symbol']]
        
        # consolida e atualiza
        if msg['Side'] == 'BUY':
            if msg['User'] not in self.buy_PL:
                self.buy_PL[msg['User']] = {}
            self.buy_PL[msg['User']] = self.get_updated_data(self.buy_PL[msg['User']], msg, md)
        else:
            if msg['User'] not in self.sell_PL:
                self.sell_PL[msg['User']] = {}
            self.sell_PL[msg['User']] = self.get_updated_data(self.sell_PL[msg['User']], msg, md)

    def get_updated_data(self, pls, msg, md):
        symbol = msg['Symbol']
        if symbol not in pls:
            pls[symbol] = PLInfo(
                broker=msg['Broker'],
                account=msg['Account'],
                user=msg['User'],
                exchange=md['segment'])     
        
        pls[symbol].exposure += calculate_exposure(msg['Price'], msg['Quantity'], md['contractMultiplier'])
        pls[symbol].quantity += msg['Quantity']
        pls[symbol].n_trades += 1 

        return pls

    def export_PL(self):
        header = ['Date', 'Broker', 'Account', 'User', 'Exchange', 'Symbol', 'Side', 'Qty', 'Avg Price', 
            'Exposure', 'Nº Trades']
        dt = datetime.now()
        if len(self.buy_PL) > 0 or len(self.sell_PL) > 0:
            if not os.path.exists(FOLDER):
                os.makedirs(FOLDER)
            
            filename = f'{dt:%Y%m%d_%H%M%S}.csv'
            path = os.path.join(FOLDER, filename)
            with open(path, 'w', newline='') as file:
                writer = csv.writer(file) 
                writer.writerow(header)
                
                for user in self.buy_PL:
                    for symbol in self.buy_PL[user]:
                        pl = self.buy_PL[user][symbol]
                        writer.writerow(self.format_row(dt, symbol, 'buy', pl))

                for user in self.sell_PL:
                    for symbol in self.sell_PL[user]:
                        pl = self.sell_PL[user][symbol]
                        writer.writerow(self.format_row(dt, symbol, 'sell', pl))
            print(f"{dt:%H:%M:%S}: Dado exportado")
        else:
            print(f"{dt:%H:%M:%S}: Não foram encontrados dados de PL para exportação")

    def format_row(self, dt, symbol, side, pl_obj):
        avg_price = calculate_avg_price(pl_obj.exposure, pl_obj.quantity, 
            self.md_info[symbol]['contractMultiplier'])
        return [ 
            dt, \
            pl_obj.broker, \
            pl_obj.account, \
            pl_obj.user, \
            pl_obj.exchange, \
            symbol, \
            side, \
            pl_obj.quantity, \
            str(round(avg_price,4)).replace('.',','), \
            str(round(pl_obj.exposure,2)).replace('.',','), \
            pl_obj.n_trades]


def calculate_exposure(price, qty, cont_mult):
    return qty * price * cont_mult


def calculate_avg_price(fin, qty, cont_mult):
    if qty == 0 or fin == 0: return 0
    avg = fin/qty
    if cont_mult == 0: return avg
    return avg * cont_mult
