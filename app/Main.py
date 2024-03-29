import PySimpleGUI as sg
import os, sys
import threading
from datetime import datetime
from Database import DatabaseInputs
from MT5 import MT5
import time

# Variável de controle da thread
thread_running = False
thread_monitor = None

# to pyinstaller create .exe
def resource_path(relative_path):

    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path,relative_path)

# Função que será executada na thread
def monitor_num_positions(mt5, window, login, password, server, max_num_positions):
    
    global thread_running
    thread_running = True
    
    while thread_running:
        positions = mt5.get_num_positions(window, login, password, server)
        orders = mt5.get_num_orders(window, login, password, server)

        if positions:
            if orders > 0:
                if positions >= max_num_positions:
                    mt5.del_all_orders(
                        window=window,
                        login=int(login),
                        password= str(password),
                        server=str(server)
                    )
                    window['logs'].print(f"{current_timestamp_str()} -- delete all positions == {positions} ")
                    break
            else:
                window['logs'].print(f"{current_timestamp_str()} -- without orders ")
                break
        else:
            window['logs'].print(f"{current_timestamp_str()} -- without positions ")
            break

        window['logs'].print(f"{current_timestamp_str()} -- there are {positions} positions ")    
        time.sleep(10)

def current_timestamp_str():
    return datetime.now().strftime("%H:%M:%S")


def update_layers(window, db_input, values):

    use_capital_liquid_mt5 = values['use_capital_liquid_mt5']
    fixed_capital          = values['fixed_capital']
    risk_value             = values['risk']
    currency               = values['currency']
    login                  = values['login']
    password               = values['password']
    server                 = values['server']
    folder_path            = values['folder_path']
    max_positions          = int(values['max_positions'])
    
    if not use_capital_liquid_mt5:
        window['logs'].print('use_capital_liquid_mt5 is empty')
        return True

    if not fixed_capital:
        window['logs'].print('fixed_capital is empty')
        return True

    if not risk_value:
        window['logs'].print('risk_value is empty')
        return True

    if not currency:
        window['logs'].print('currency is empty')
        return True

    if not login:
        window['logs'].print('login is empty')
        return True

    if not password:
        window['logs'].print('password is empty')
        return True

    if not server:
        window['logs'].print('server is empty')
        return True

    if not folder_path:
        window['logs'].print('folder_path is empty')
        return True
        
    if not max_positions:
        window['logs'].print('max_positions is empty')
        return True

    db_input.truncate()

    db_input.insert_input({
        "USE_CAPITAL_LIQUID_MT5" : use_capital_liquid_mt5,
        "FIXED_CAPITAL"          : fixed_capital,
        'RISK'                   : risk_value,
        'CURRENCY'               : currency,
        'LOGIN'                  : login,
        'PASSWORD'               : password,
        'SERVER'                 : server,
        'FOLDER_PATH'            : folder_path,
        'MAX_POSITIONS'          : max_positions})
    
    return False

    


# carrega os inputs
# P:\Projetos\SenderOrdersMT5\app\db\my_database.json
db_input = DatabaseInputs(file_db = r'P:\Projetos\SenderOrdersMT5\app\db\my_database.json')
input = db_input.get_input()

mt5 = MT5()

if input is not None:

    use_capital_liquid_mt5 = input['USE_CAPITAL_LIQUID_MT5']
    fixed_capital          = input['FIXED_CAPITAL']
    input_risk             = input['RISK']
    input_currency         = input['CURRENCY']
    input_login            = input['LOGIN']
    input_password         = input['PASSWORD']
    input_server           = input['SERVER']
    input_folder_path      = input['FOLDER_PATH']
    max_positions          = input['MAX_POSITIONS']

else:

    use_capital_liquid_mt5 = ""
    fixed_capital          = ""
    input_risk             = ""
    input_currency         = ""
    input_login            = ""
    input_password         = ""
    input_server           = ""
    input_folder_path      = ""
    max_positions          = ""


# construi o layout

sg.theme('DarkGrey14')  

layout = [
    [
        sg.Text('Use Liquid Capital? (MT5)'), 
        sg.Combo(["YES","NO"], key='use_capital_liquid_mt5', default_value=use_capital_liquid_mt5),
        sg.Text('Select a currency:'),
        sg.Combo(['GBP', 'USD', 'EUR', 'CHF', 'BRL'], key='currency', default_value=input_currency),
        sg.Text('Max Positions:'),
        sg.InputText(key='max_positions', size=(5, 5), default_text =max_positions)
    ],
    [
        sg.Text('Fixed Capital:'),
        sg.InputText(key='fixed_capital', size=(20, 5) ,  default_text = fixed_capital),
        sg.Text('Enter the risk value (%):'),
        sg.InputText(key='risk', size=(5, 5) ,  default_text = input_risk)
    ],
    [sg.Text('Enter your login:'), sg.InputText(key='login', size=(20, 5), default_text = input_login)],
    [sg.Text('Enter your password:'), sg.InputText(key='password', size=(20, 5), default_text = input_password)],
    [sg.Text('Enter the server name:'), sg.InputText(key='server', size=(20, 5), default_text = input_server)],
    [sg.Text('Enter the folder path:'),sg.InputText(key='folder_path', default_text = input_folder_path)],
    [sg.Button('Send Orders'), sg.Button('Delete All Orders'), sg.Button('List Orders'), sg.Button('List Positions'), sg.Button('Clear Terminal'),  sg.Button('Quit')],
    [sg.Button('Monitor - ON'), sg.Button('Monitor - OFF')],
    [sg.Multiline(size=(100, 20), key='logs')],
]

window = sg.Window('TradingView -> MT5', layout)

while True:
    event, values = window.read()

    if event in (sg.WIN_CLOSED, 'Quit'):

        if thread_monitor:
            thread_running = False
            thread_monitor.join()

        break

    
    elif event == 'Send Orders':

        return_db_layers = update_layers(window,db_input,values)

        if return_db_layers:
            continue
        else:
            use_capital_liquid_mt5 = values['use_capital_liquid_mt5']
            fixed_capital          = values['fixed_capital']
            risk_value             = values['risk']
            currency               = values['currency']
            login                  = values['login']
            password               = values['password']
            server                 = values['server']
            folder_path            = values['folder_path']
            max_positions          = int(values['max_positions'])
        
        mt5.del_all_orders(
            window=window,
            login=int(login),
            password= str(password),
            server=str(server))
        
        time.sleep(1)
        
        mt5.send_orders(
            window = window,
            risk = float(risk_value),
            folder_path = str(folder_path),
            account_currency = str(currency),
            login = int(login),
            password = str(password),
            server = str(server),
            use_capital_liquid_mt5 = str(use_capital_liquid_mt5),
            fixed_capital = float(fixed_capital))


    elif event ==  'Delete All Orders':

        return_db_layers = update_layers(window,db_input,values)

        if return_db_layers:
            continue
        else:
            use_capital_liquid_mt5 = values['use_capital_liquid_mt5']
            fixed_capital          = values['fixed_capital']
            risk_value             = values['risk']
            currency               = values['currency']
            login                  = values['login']
            password               = values['password']
            server                 = values['server']
            folder_path            = values['folder_path']
            max_positions          = int(values['max_positions'])


        mt5.del_all_orders(
            window = window,
            login = int(login),
            password = str(password),
            server = str(server))
        
    elif event == 'List Orders':

        return_db_layers = update_layers(window,db_input,values)

        if return_db_layers:
            continue
        else:
            use_capital_liquid_mt5 = values['use_capital_liquid_mt5']
            fixed_capital          = values['fixed_capital']
            risk_value             = values['risk']
            currency               = values['currency']
            login                  = values['login']
            password               = values['password']
            server                 = values['server']
            folder_path            = values['folder_path']
            max_positions          = int(values['max_positions'])


        mt5.list_orders(
            window = window,
            login = int(login),
            password = str(password),
            server = str(server))


    elif event == 'Monitor - ON':

        window['logs'].print(f"{current_timestamp_str()} Monitor is starting ..")

        return_db_layers = update_layers(window,db_input,values)

        if return_db_layers:
            continue
        else:
            use_capital_liquid_mt5 = values['use_capital_liquid_mt5']
            fixed_capital          = values['fixed_capital']
            risk_value             = values['risk']
            currency               = values['currency']
            login                  = values['login']
            password               = values['password']
            server                 = values['server']
            folder_path            = values['folder_path']
            max_positions          = int(values['max_positions'])

        if not thread_running:
            thread_monitor = threading.Thread(
                target = monitor_num_positions, 
                args = (mt5, window, int(login), str(password), str(server), int(max_positions)) 
            )
            
            thread_monitor.start()

        window['logs'].print(f"{current_timestamp_str()} Monitor is running ..")


    elif event == 'Monitor - OFF':    
        thread_running = False
        thread_monitor.join()

        window['logs'].print(f"{current_timestamp_str()} Monitor stopped! ")
        
    
    elif event == 'Clear Terminal':
        window['logs'].update('')


window.close()
