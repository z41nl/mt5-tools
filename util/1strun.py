##1st order always fail


import MetaTrader5 as mt5
import time

symbol = "AUDUSD"

# 1. Ensure the symbol is visible in Market Watch
if not mt5.symbol_select(symbol, True):
    print(f"Failed to select {symbol}. Check if the symbol name is correct for this broker.")
    # Handle error...

# 2. Force wait/sync for a valid price tick (Crucial for the 1st run)
retries = 10
tick = None
for _ in range(retries):
    tick = mt5.symbol_info_tick(symbol)
    if tick is not None and tick.ask > 0:
        break  # We have a valid live price!
    time.sleep(0.2)  # Wait 200ms before checking again

if tick is None or tick.ask == 0:
    print(f"Error: Could not fetch initial price for {symbol} in time.")
    # Do not proceed to send order if price is 0
else:
    print(f"Market synced. Current Ask for {symbol}: {tick.ask}")
  
