'''https://www.mql5.com/en/docs/python_metatrader5'''

import time
import math
import MetaTrader5 as mt5
from datetime import datetime
from TradingView import TradingView


class MT5():

    def __init__(self):
        pass


    def login(self, 
            window, 
            login, 
            password, 
            server, 
            return_off = False):

        if not mt5.initialize():
            window['logs'].print(f"{self.current_timestamp_str()} -- Initialize Failed, error code = {mt5.last_error()}")

        authorized = mt5.login(login,password,server)

        time.sleep(1)

        if authorized:
            # display trading account data 'as is'
            if not return_off:
                window['logs'].print(f'{self.current_timestamp_str()} -- Connect Done #{login} #{server}')
            return True
        else:
            if not return_off:
                window['logs'].print(f"{self.current_timestamp_str()} -- Connect Failed #{login} #{server} Error code: {mt5.last_error()}")
            return False


    def turn_off(self,mt5):
        mt5.shutdown()


    def del_all_orders(self, 
            window,
            login,
            password,
            server,
            extra_message = ''
            ):

        if self.login(window,login,password,server):

            # verifica se já existe ordens posicionadas
            orders=mt5.orders_get()

            order_to_remove = []

            # pega as ordens que ja estão posicionadas e remove
            for order in orders:
                order_to_remove.append(order.ticket)

            for order_rm in order_to_remove:

                request = {
                    "action"       : mt5.TRADE_ACTION_REMOVE,
                    "order"        : int(order_rm)
                }

                # send a trading request
                result = mt5.order_send(request)

                # check the execution result
                if result.retcode != mt5.TRADE_RETCODE_DONE:
                    window['logs'].print(f"{self.current_timestamp_str()} -- Order remove failed -- [{order_rm}] {extra_message}")
                        
                else:
                    window['logs'].print(f"{self.current_timestamp_str()} -- Order remove done -- [{order_rm}] {extra_message}")

            self.turn_off(mt5)
        


    def send_orders(
            self,
            window,
            risk,
            folder_path,
            account_currency,
            login,
            password,
            server,
            use_capital_liquid_mt5,
            fixed_capital,
            deviation = 10):

        
        # pega ordens do arquivo exportado do Trading View
        tradingview = TradingView()
        orders = tradingview.get_orders(
            window = window,
            folder_path = folder_path,
            currency = account_currency)

        if self.login(window,login,password,server):

            list_of_symbols = [symbol.name for symbol in mt5.symbols_get()]

            if use_capital_liquid_mt5 == 'YES':
                account_info = mt5.account_info()
                balance = account_info.balance
            else:
                balance = fixed_capital

            for order in orders:

                symbol = order.symbol
                symbol_info = mt5.symbol_info(symbol)

                symbol_ref = order.symbol_ref

                point       = symbol_info.point * 10 # 0.00001 ===> 0.0001
                digits      = symbol_info.digits - 1 # 5 ===> 4 para olhar apenas para os pips

                side        = order.side
                entry       = round(order.entry,digits - 1)       # -1 :> arredonda para tirar os pipetes
                take_profit = round(order.take_profit,digits - 1) # -1 :> arredonda para tirar os pipetes
                stop_loss   = round(order.stop_loss,digits - 1)   # -1 :> arredonda para tirar os pipetes

                # verifica se existe o par no metatrader 5
                if symbol in list_of_symbols:
 
                    ## calculo
                    # https://www.earnforex.com/guides/pip-value-formula/


                    # micro-lotes -- a posicao vai ser montada a partir de micro lotes
                    # padrao - 100000
                    # mini   - 10000
                    # micro  - 1000
                    lot_size_default = 1000 

                    ## calculo do pip

                    # Scenario 1
                    if symbol.endswith(account_currency):  
                        pip_size = point
                        pip_value = round((lot_size_default * pip_size), 2)

                    # Scenario 2
                    elif symbol.startswith(account_currency):  
                        pip_size = point
                        ask_rate, bid_rate = self.get_ask_bid_rate(symbol, window, login, password, server)
                        if ask_rate:
                            pip_value =round( ((lot_size_default * pip_size) / ask_rate),2)
                        else:
                            window['logs']\
                                .print(f"{self.current_timestamp_str()} -- order not send  #{symbol} -- try")

                    # Scenario 3 
                    else:  
                        matching_pair = self.get_matching_pair(window, login, password, server, account_currency, base_currency = symbol[3:6])

                        # Scenario 3a
                        if matching_pair.endswith(account_currency): 
                            ask_rate, bid_rate = self.get_ask_bid_rate(matching_pair, window, login, password, server)
                            if bid_rate:
                                pip_value = round(((lot_size_default * point) * bid_rate),2)
                            else:
                                window['logs']\
                                    .print(f"{self.current_timestamp_str()} -- order not send  #{symbol} -- try")
                                
                        # Scenario 3b
                        elif matching_pair.startswith(account_currency): 
                            ask_rate, bid_rate = self.get_ask_bid_rate(matching_pair, window, login, password, server)
                            if ask_rate:
                                pip_value = round(((lot_size_default * point) / ask_rate), 2)
                            else:
                                window['logs']\
                                    .print(f"{self.current_timestamp_str()} -- order not send  #{symbol} -- try")


                    pip_stop_loss   = round(round(abs(order.entry - order.stop_loss),5)*math.pow(10,digits),1)
                    pip_take_profit = round(round(abs(order.entry - order.take_profit),5)*math.pow(10,digits),1)
                    risk_return     = round(pip_take_profit/pip_stop_loss,2)

                    lot_size        = round((balance * (risk/100))/(pip_stop_loss*pip_value*100), 2)  # multiplicar por 100 para voltar para o lote padrão do par


                    ## envio das ordens
                    if int(round(lot_size * 100,0)) != 0:

                        type_order = mt5.ORDER_TYPE_BUY_LIMIT if side == 'Buy' else mt5.ORDER_TYPE_SELL_LIMIT

                        request = {
                            "action"       : mt5.TRADE_ACTION_PENDING,
                            "symbol"       : symbol,
                            "volume"       : lot_size,
                            "type"         : type_order,
                            "price"        : entry,
                            "sl"           : stop_loss,
                            "stoplimit"    : stop_loss,
                            "tp"           : take_profit,
                            "deviation"    : deviation,                             
                            "magic"        : 0,
                            "comment"      : f"[{symbol_ref} - {risk_return}]",
                            "type_time"    : mt5.ORDER_TIME_GTC,
                            "type_filling" : mt5.ORDER_FILLING_RETURN,
                        }

                        # send a trading request
                        result = mt5.order_send(request)

                        # check the execution result
                        if result.retcode != mt5.TRADE_RETCODE_DONE:
                            window['logs'].print(f"{self.current_timestamp_str()} -- order send failed  #{symbol} - dont forget to allow algorithmic trading in mt5")
                            
                        else:
                            window['logs'].print(f"{self.current_timestamp_str()} -- order send done #{symbol}  [{result.order}] - lot_size:{lot_size} - e:{entry} - rr:{risk_return}")

                    else:
                        window['logs'].print(f"{self.current_timestamp_str()} -- order not send - position size it does not fit #{symbol}  #{entry}  #{lot_size}")

                else:
                    window['logs'].print(f"{self.current_timestamp_str()} -- {symbol} not found -- order send failed")

            self.turn_off(mt5)


    def list_orders(self, 
            window,
            login,
            password,
            server):
        
        if self.login(window,login,password,server, return_off= True):
            for order in mt5.orders_get():
                window['logs'].print(f"{self.current_timestamp_str()} -- order #{order.symbol}  [{order.ticket}] - lot_size:{order.volume_initial} - e:{(order.price_open)} - rr:{order.comment}")
            else:
                window['logs'].print(f"{self.current_timestamp_str()} -- without orders ")

        self.turn_off(mt5)


    def list_positions(self, 
            window,
            login,
            password,
            server):
        
        if self.login(window,login,password,server, return_off= True):
            for position in mt5.positions_get():
                window['logs'].print(f"{self.current_timestamp_str()} -- order #{position.symbol}  [{position.ticket}] - lot_size:{position.volume_initial} - e:{position.price_open} - rr:{position.comment}")

        self.turn_off(mt5)


    def get_num_positions(self, 
            window, 
            login, 
            password, 
            server):
        
        if self.login(window, login, password, server, return_off = True):
            positions = mt5.positions_total()
        else:
            positions =  None
        
        self.turn_off(mt5)

        return positions


    def get_num_orders(self, 
            window, 
            login, 
            password, 
            server):
        
        if self.login(window, login, password, server, return_off = True):
            orders = mt5.orders_total()
        else:
            orders =  None
        
        self.turn_off(mt5)

        return orders
    


    def get_ask_bid_rate(self, symbol, window, login, password, server):

        if self.login(window, login, password, server, return_off = True):

            list_of_symbols = [symbol.name for symbol in mt5.symbols_get()]

            # verifica se existe o par no metatrader 5
            if symbol in list_of_symbols:

                symbol_info = mt5.symbol_info(symbol) # informacoes do ativo referencia para calculo

                ask_rate = round(symbol_info.ask, symbol_info.digits)
                bid_rate = round(symbol_info.bid, symbol_info.digits)

                return ask_rate, bid_rate
                    
            else:
                    
                return None



    def get_matching_pair(self, window, login, password, server, account_currency, base_currency):

        if self.login(window, login, password, server, return_off = True):

            list_of_symbols = [symbol.name for symbol in mt5.symbols_get()]

            for symbol in list_of_symbols:

                if account_currency in symbol and base_currency in symbol:

                    return symbol
        
        return None


    def current_timestamp_str(self):
        return datetime.now().strftime("%H:%M:%S")
