import MetaTrader5 as mt5

mt5.initialize()

symbols = mt5.symbols_get()

tradable = [s.name for s in symbols if s.trade_mode != mt5.SYMBOL_TRADE_MODE_DISABLED]

for s in tradable:
    print(s)

print("\nTotal tradable symbols:", len(tradable))

mt5.shutdown()