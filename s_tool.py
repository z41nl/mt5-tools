import MetaTrader5 as mt5
import tkinter as tk
from tkinter import messagebox

ACCOUNT = 11111111
PASSWORD = ""
SERVER = ""
TERMINAL_PATH = r"C:\Program Files\FTMO MetaTrader 5\terminal64.exe" #C:\Program Files\MetaTrader 5\terminal64.exe
SYMBOL = "AUDUSD"
LOT = 7.0

TP_TICKS = 50
SL_TICKS = 25

if not mt5.initialize(
    path=TERMINAL_PATH,
    login=ACCOUNT,
    password=PASSWORD,
    server=SERVER
):
    print("MT5 로그인 실패")
    print(mt5.last_error())
    quit()

print("MT5 로그인 성공")

symbol_info = mt5.symbol_info(SYMBOL)
if symbol_info is None:
    print("심볼 정보 없음")
    quit()

POINT = symbol_info.point

def send_order(order_type):
    if not mt5.symbol_select(SYMBOL, True):
        messagebox.showerror("에러", "심볼 선택 실패")
        return

    tick = mt5.symbol_info_tick(SYMBOL)
    if tick is None:
        messagebox.showerror("에러", "시세 정보 없음")
        return

    if order_type == mt5.ORDER_TYPE_BUY:
        price = tick.ask
        sl = price - SL_TICKS * POINT
        tp = price + TP_TICKS * POINT
        comment = "BUY 7 lot"
    else:
        price = tick.bid
        sl = price + SL_TICKS * POINT
        tp = price - TP_TICKS * POINT
        comment = "SELL 7 lot"

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": SYMBOL,
        "volume": LOT,
        "type": order_type,
        "price": price,
        "sl": sl,
        "tp": tp,
        "deviation": 10,
        "magic": 777,
        "comment": comment,
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    result = mt5.order_send(request)

    if result.retcode == mt5.TRADE_RETCODE_DONE:
        messagebox.showinfo(
            "주문 완료",
            f"{comment}\n진입가: {price:.5f}\nTP: {tp:.5f}\nSL: {sl:.5f}"
        )
    else:
        messagebox.showerror("주문 실패", f"retcode: {result.retcode}")

root = tk.Tk()
root.title("FTMO MT5 Ticks Order")
root.geometry("350x220")

btn_buy = tk.Button(
    root,
    text=f"{SYMBOL} BUY (7 lot, TP {TP_TICKS} ticks / SL {SL_TICKS} ticks)",
    font=("Arial", 12),
    bg="green",
    fg="white",
    command=lambda: send_order(mt5.ORDER_TYPE_BUY)
)
btn_buy.pack(fill="x", padx=10, pady=10)

btn_sell = tk.Button(
    root,
    text=f"{SYMBOL} SELL (7 lot, TP {TP_TICKS} ticks / SL {SL_TICKS} ticks)",
    font=("Arial", 12),
    bg="red",
    fg="white",
    command=lambda: send_order(mt5.ORDER_TYPE_SELL)
)
btn_sell.pack(fill="x", padx=10, pady=10)

root.mainloop()
mt5.shutdown() 
