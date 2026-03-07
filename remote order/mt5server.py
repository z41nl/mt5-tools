from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
import MetaTrader5 as mt5
import time
from typing import Optional

app = FastAPI()

# ==============================
# ACCOUNT SETTINGS
# ==============================
ACCOUNT = 531189977
PASSWORD = "*K*qaZtQ$8L"
SERVER = "FTMO-Server3"
TERMINAL_PATH = r"C:\Program Files\FTMO MetaTrader 5\terminal64.exe"
SECRET_TOKEN = "YOUR_SECRET_TOKEN"

connected = False

class OrderRequest(BaseModel):
    symbol: str
    volume: float
    type: str  # BUY, SELL, BUY_LIMIT, SELL_LIMIT, CLOSE, CANCEL, MODIFY
    price: Optional[float] = 0
    sl: float = 0
    tp: float = 0
    ticket: Optional[int] = None

def connect_mt5():
    global connected
    if connected: return True
    if not mt5.initialize(path=TERMINAL_PATH, login=ACCOUNT, password=PASSWORD, server=SERVER):
        return False
    connected = True
    return True

@app.get("/health")
def health():
    return {"status": "online" if connect_mt5() else "offline"}

@app.get("/account")
def account_info(authorization: str = Header(None)):
    if authorization != SECRET_TOKEN or not connect_mt5():
        raise HTTPException(status_code=403)
    info = mt5.account_info()
    if info is None: return {"status": "error"}
    return {"balance": info.balance, "equity": info.equity, "profit": info.profit}

@app.get("/positions")
def get_positions(authorization: str = Header(None)):
    if authorization != SECRET_TOKEN or not connect_mt5(): raise HTTPException(status_code=403)
    positions = mt5.positions_get()
    return [{"ticket": p.ticket, "symbol": p.symbol, "type": "BUY" if p.type == 0 else "SELL", 
             "volume": p.volume, "price": p.price_open, "sl": p.sl, "tp": p.tp, "profit": p.profit} for p in positions] if positions else []

@app.get("/orders")
def get_orders(authorization: str = Header(None)):
    if authorization != SECRET_TOKEN or not connect_mt5(): raise HTTPException(status_code=403)
    orders = mt5.orders_get()
    return [{"ticket": o.ticket, "symbol": o.symbol, "volume": o.volume_initial, "price": o.price_open, 
             "sl": o.sl, "tp": o.tp, "type": "BUY_LIMIT" if o.type == 2 else "SELL_LIMIT"} for o in orders] if orders else []

@app.post("/order")
def handle_order(data: OrderRequest, authorization: str = Header(None)):
    if authorization != SECRET_TOKEN or not connect_mt5(): raise HTTPException(status_code=403)
    
    # 1. 포지션 시장가 청산
    if data.type == "CLOSE":
        pos = mt5.positions_get(ticket=data.ticket)
        if not pos: return {"status": "error", "msg": "No Position"}
        p = pos[0]
        tick = mt5.symbol_info_tick(p.symbol)
        request = {
            "action": mt5.TRADE_ACTION_DEAL, "symbol": p.symbol, "volume": p.volume,
            "type": mt5.ORDER_TYPE_SELL if p.type == 0 else mt5.ORDER_TYPE_BUY,
            "position": p.ticket, "price": tick.bid if p.type == 0 else tick.ask,
            "deviation": 20, "magic": 999, "comment": "Close Order",
            "type_time": mt5.ORDER_TIME_GTC, "type_filling": mt5.ORDER_FILLING_IOC,
        }
    
    # 2. SL/TP 수정
    elif data.type == "MODIFY":
        request = {
            "action": mt5.TRADE_ACTION_SLTP, "symbol": data.symbol,
            "sl": data.sl, "tp": data.tp, "position": data.ticket
        }

    # 3. 대기 주문 취소
    elif data.type == "CANCEL":
        request = {"action": mt5.TRADE_ACTION_REMOVE, "order": data.ticket}

    # 4. 신규 주문 (시장가/지정가)
    else:
        mt5.symbol_select(data.symbol, True)
        tick = mt5.symbol_info_tick(data.symbol)
        order_map = {"BUY": 0, "SELL": 1, "BUY_LIMIT": 2, "SELL_LIMIT": 3}
        price = data.price if "LIMIT" in data.type else (tick.ask if data.type == "BUY" else tick.bid)
        request = {
            "action": mt5.TRADE_ACTION_DEAL if "LIMIT" not in data.type else mt5.TRADE_ACTION_PENDING,
            "symbol": data.symbol, "volume": data.volume, "type": order_map[data.type],
            "price": price, "sl": data.sl, "tp": data.tp, "deviation": 20, "magic": 999,
            "type_time": mt5.ORDER_TIME_GTC, "type_filling": mt5.ORDER_FILLING_IOC,
        }

    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        return {"status": "error", "msg": result.comment}
    return {"status": "success", "ticket": result.order}