'''https://www.mql5.com/en/docs/python_metatrader5'''

import time
import math
import MetaTrader5 as mt5
from datetime import datetime
from TradingView import TradingView


class MT5():

    def __init__(self):
        pass


    def login(self,window,login,password,server):

        if not mt5.initialize():
            window['logs'].print(f"{self.current_timestamp_str()} -- Initialize Failed, error code = {mt5.last_error()}")

        authorized = mt5.login(login,password,server)

        time.sleep(1)

        if authorized:
            # display trading account data 'as is'
            window['logs'].print(f'{self.current_timestamp_str()} -- Connect Done #{login} #{server}')
            return True
        else:
            window['logs'].print(f"{self.current_timestamp_str()} -- Connect Failed #{login} #{server} Error code: {mt5.last_error()}")
            return False


    def turn_off(self,mt5):
        mt5.shutdown()

    def del_all_orders(self, 
            window,
            login,
            password,
            server
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
                    window['logs'].print(f"{self.current_timestamp_str()} -- Order remove failed -- [{order_rm}]")
                        
                else:
                    window['logs'].print(f"{self.current_timestamp_str()} -- Order remove done -- [{order_rm}]")

            self.turn_off(mt5)
        


    def send_orders(
            self,
            window,
            risk,
            folder_path,
            currency,
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
            currency = currency)

        
        if self.login(window,login,password,server):

            if use_capital_liquid_mt5 == 'YES':
                account_info = mt5.account_info()
                balance = account_info.balance
            else:
                balance = fixed_capital


            for order in orders:

                symbol = order.symbol
                symbol_ref = order.symbol_ref

                symbol_info = mt5.symbol_info(symbol)  # informacoes do ativo principal
                symbol_ref_info = mt5.symbol_info(symbol_ref) # informacoes do ativo referencia para calculo

                point               = symbol_info.point
                digits              = symbol_info.digits
                ask_ref             = round(symbol_ref_info.ask, symbol_ref_info.digits) # referencia ao par da moeda margem
                trade_contract_size = symbol_info.trade_contract_size

                side        = order.side
                entry       = round(order.entry,digits - 1)
                take_profit = round(order.take_profit,digits - 1)
                stop_loss   = round(order.stop_loss,digits - 1)

                try :
                    pip_value     = round((point*10/ask_ref)*trade_contract_size,2)
                    pip_stop_loss = round(round(abs(order.entry - order.stop_loss),5)*math.pow(10,digits - 1),1)
                    pip_take_profit = round(round(abs(order.entry - order.take_profit),5)*math.pow(10,digits - 1),1)
                    risk_return = round(pip_take_profit/pip_stop_loss,2)
                except ZeroDivisionError as zde:
                    window['logs'].print(f"{self.current_timestamp_str()} -- order send failed because without symbol ref ask price {symbol_ref} -- try again")
                    return None

                lot_size           = (balance * (risk/100))/(pip_stop_loss*pip_value)
                lot_size_rounded   = round(lot_size,2)


                if int(round(lot_size*100,0)) != 0:

                    type_order = mt5.ORDER_TYPE_BUY_LIMIT if side == 'Buy' else mt5.ORDER_TYPE_SELL_LIMIT

                    request = {
                        "action"       : mt5.TRADE_ACTION_PENDING,
                        "symbol"       : symbol,
                        "volume"       : lot_size_rounded,
                        "type"         : type_order,
                        "price"        : entry,
                        "sl"           : stop_loss,
                        "stoplimit"    : stop_loss,
                        "tp"           : take_profit,
                        "deviation"    : deviation,                             
                        "magic"        : 0,
                        "comment"      : f"[{risk_return} - {pip_stop_loss}]",
                        "type_time"    : mt5.ORDER_TIME_GTC,
                        "type_filling" : mt5.ORDER_FILLING_RETURN,
                    }


                    # send a trading request
                    result = mt5.order_send(request)


                    # check the execution result
                    if result.retcode != mt5.TRADE_RETCODE_DONE:
                        window['logs'].print(f"{self.current_timestamp_str()} -- order send failed  #{symbol} - e:{entry}")
                    else:
                        window['logs'].print(f"{self.current_timestamp_str()} -- order send done [{result.order}] #{symbol} - lot_size:{lot_size_rounded} - e:{entry} - rr:{risk_return}")

                else:
                        window['logs'].print(f"{self.current_timestamp_str()} -- order not send - position size it does not fit #{symbol}  #{entry}  #{lot_size}")

            self.turn_off(mt5)

    def current_timestamp_str(self):

        return datetime.now().strftime("%H:%M:%S")