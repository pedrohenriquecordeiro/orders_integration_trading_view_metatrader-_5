class Order:
    def __init__(self, symbol, symbol_ref, currency, side, type, entry, take_profit, stop_loss):
        
        self.symbol = symbol
        self.symbol_ref = symbol_ref
        self.currency  = currency
        self.side = side
        self.type = type
        self.entry = entry
        self.take_profit = take_profit
        self.stop_loss = stop_loss