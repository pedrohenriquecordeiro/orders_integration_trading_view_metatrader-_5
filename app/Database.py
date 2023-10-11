from tinydb import TinyDB
import os


class DatabaseInputs:
    
    def __init__(self,file_db):
        self.file = file_db 

        if not os.path.exists(self.file):
            # cria o arquivo senao existir
            open(self.file, 'w') 

    def get_input(self):

        db = TinyDB(self.file)
        table = db.table('INPUT')
        if not table:
            result = None
        else:
            result = table.all()[0]
        db.close()

        return result
    
    def insert_input(self, input_now):

        db = TinyDB(self.file)
        table = db.table('INPUT')

        table.insert({
            "USE_CAPITAL_LIQUID_MT5" : input_now['USE_CAPITAL_LIQUID_MT5'],
            "FIXED_CAPITAL"          : input_now['FIXED_CAPITAL'],
            "RISK"                   : input_now['RISK'], 
            "CURRENCY"               : input_now['CURRENCY'], 
            "LOGIN"                  : input_now['LOGIN'], 
            "PASSWORD"               : input_now['PASSWORD'], 
            "SERVER"                 : input_now['SERVER'], 
            "FOLDER_PATH"            : input_now['FOLDER_PATH'],
            "MAX_POSITIONS"          : input_now['MAX_POSITIONS']
        })

        db.close()


    def truncate(self):
    
        db = TinyDB(self.file)
        table = db.table('INPUT')
        table.truncate()
        db.close()


