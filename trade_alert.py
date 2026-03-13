import MetaTrader5 as mt5
import time
import requests

ACCOUNT = 11111111
PASSWORD = ""
SERVER = "" #brokerserver
TERMINAL_PATH = r"C:\Program Files\FTMO MetaTrader 5\terminal64.exe"

WEBHOOK_URL = ""

CHECK_INTERVAL = 2

def send(msg):
    requests.post(WEBHOOK_URL, json={"content": msg})

if not mt5.initialize(path=TERMINAL_PATH, login=ACCOUNT, password=PASSWORD, server=SERVER):
    quit()

positions_state = {}

while True:

    positions = mt5.positions_get()

    if positions is None:
        time.sleep(CHECK_INTERVAL)
        continue

    current = {}

    for p in positions:

        ticket = p.ticket

        current[ticket] = {
            "symbol": p.symbol,
            "volume": p.volume,
            "type": p.type,
            "sl": p.sl,
            "tp": p.tp
        }

        if ticket not in positions_state:

            msg = "📈 NEW TRADE\n"
            msg += f"Symbol: {p.symbol}\n"
            msg += f"Volume: {p.volume}\n"

            if p.type == 0:
                msg += "Type: BUY\n"
            else:
                msg += "Type: SELL\n"

            if p.sl != 0:
                msg += f"SL: {p.sl}\n"

            if p.tp != 0:
                msg += f"TP: {p.tp}\n"

            send(msg)

        else:

            old = positions_state[ticket]

            if p.sl != old["sl"]:
                send(
                    f"⚠️ SL Changed\n"
                    f"{p.symbol}\n"
                    f"{old['sl']} → {p.sl}"
                )

            if p.tp != old["tp"]:
                send(
                    f"⚠️ TP Changed\n"
                    f"{p.symbol}\n"
                    f"{old['tp']} → {p.tp}"
                )

    positions_state = current

    time.sleep(CHECK_INTERVAL)
