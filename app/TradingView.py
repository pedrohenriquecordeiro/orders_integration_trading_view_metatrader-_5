from datetime import datetime
import os
import pandas as pd
from Order import Order

class TradingView():

    def __init__(self):
        pass


    def get_orders(
            self,
            window,
            folder_path,
            currency
        ):

        # pega o arquivo exportado mais atual

        file_list = []

        for file_name in os.listdir(folder_path):
            if 'paper-trading-orders' in file_name:
                full_path = os.path.join(folder_path, file_name)
                if os.path.isfile(full_path):
                    mod_time = os.stat(full_path).st_mtime
                    file_list.append((full_path, file_name, mod_time))

        try:
            sorted_files = sorted(file_list, key=lambda x: x[2], reverse=True)
            sorted_files = [[file[0], file[1], datetime.fromtimestamp(file[2]).strftime('%Y-%m-%d %H:%M:%S')] for file in sorted_files]
            last_file = sorted_files[0][0]

        except Exception as exp:
            window['logs'].print(f'{self.current_timestamp_str()}-- {str(exp)}')
            return None


        # le o arquivo exportado para criar as ordens
        orders_list = []

        # Read CSV file and use first row as column headers
        orders_df = pd.read_csv(last_file, header=0)

        # Loop through each row of the DataFrame
        for index, row in orders_df.iterrows():

            try: # file of all orders
                if row['Type'] == 'Limit' and row['Status'] == 'Working':

                    orders_list.append([
                        row['Symbol'], 
                        row['Side'], 
                        row['Type'],
                        row['Price'],
                        row['Take Profit'],
                        row['Stop Loss']
                    ])
            except:
                try: # file of working orders
                    if row['Type'] == 'Limit':

                        orders_list.append([
                            row['Symbol'], 
                            row['Side'], 
                            row['Type'],
                            row['Price'],
                            row['Take Profit'],
                            row['Stop Loss']
                        ])
                except Exception as excp:
                    window['logs'].print(f'{self.current_timestamp_str()}-- {str(excp)}')


        # remove order duplicadas no arquivo

        my_set = set(tuple(x) for x in orders_list)
        my_orders_list = [list(x) for x in my_set]

        orders_list = []

        # cria os objetos de ordens
        for symbol, side, type, entry, take_profit, stop_loss in my_orders_list:

            symbol = symbol.split(":")[1]
            symbol_ref = currency + symbol[3:]

            if currency == symbol[3:]:
                symbol_ref = symbol

            try:
                order = Order(
                    symbol      = symbol, 
                    symbol_ref  = symbol_ref,
                    currency    = currency,
                    side        = side, 
                    type        = type,
                    entry       = float(entry), 
                    take_profit = float(take_profit), 
                    stop_loss   = float(stop_loss)        
                )

                orders_list.append(order)

            except Exception as exp:
                window['logs'].print(f'{self.current_timestamp_str()}-- {str(exp)}')

        orders_list = sorted(orders_list, key=lambda x: x.symbol)
        return orders_list
    



    def current_timestamp_str(self):

        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")