import tkinter as tk
from tkinter import ttk, messagebox
import requests
from concurrent.futures import ThreadPoolExecutor

# ==============================
# SERVERS CONFIG
# ==============================
SERVERS = [
    {"name": "Local_Account", "url": "http://127.0.0.1:8000", "token": "YOUR_SECRET_TOKEN"}
]

class TradeClient:
    def __init__(self, root):
        self.root = root
        self.root.title("Multi-Server Trade Pro")
        self.root.geometry("1000x900")
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.acc_widgets = {}

        self.create_widgets()
        self.refresh_all()

    def create_widgets(self):
        # --- [1] Account Dashboard (계정별 칸) ---
        self.dash_frame = tk.Frame(self.root)
        self.dash_frame.pack(fill="x", padx=10, pady=5)
        for s in SERVERS:
            f = tk.LabelFrame(self.dash_frame, text=s['name'], font=("Arial", 10, "bold"))
            f.pack(side="left", padx=5, fill="both", expand=True)
            l = tk.Label(f, text="Balance: 0.00\nEquity: 0.00\nProfit: 0.00", justify="left")
            l.pack(padx=5, pady=5)
            self.acc_widgets[s['name']] = l

        # --- [2] Order Panel (신규 주문) ---
        self.order_frame = tk.LabelFrame(self.root, text="New Order Control")
        self.order_frame.pack(fill="x", padx=10, pady=5)
        
        # Inputs
        tk.Label(self.order_frame, text="Symbol").grid(row=0, column=0)
        self.cmb_symbol = ttk.Combobox(self.order_frame, values=["XAUUSD", "EURUSD", "BTCUSD"], width=10)
        self.cmb_symbol.set("XAUUSD")
        self.cmb_symbol.grid(row=0, column=1)

        tk.Label(self.order_frame, text="Lot").grid(row=0, column=2)
        self.ent_lot = tk.Entry(self.order_frame, width=10); self.ent_lot.insert(0, "0.01")
        self.ent_lot.grid(row=0, column=3)

        tk.Label(self.order_frame, text="Price (Limit)").grid(row=1, column=0)
        self.ent_prc = tk.Entry(self.order_frame, width=10); self.ent_prc.insert(0, "0.0")
        self.ent_prc.grid(row=1, column=1)

        tk.Label(self.order_frame, text="SL/TP").grid(row=1, column=2)
        self.ent_sl = tk.Entry(self.order_frame, width=5); self.ent_sl.insert(0, "0")
        self.ent_tp = tk.Entry(self.order_frame, width=5); self.ent_tp.insert(0, "0")
        self.ent_sl.grid(row=1, column=3, sticky="w"); self.ent_tp.grid(row=1, column=3, sticky="e")

        # Buttons
        btn_f = tk.Frame(self.order_frame)
        btn_f.grid(row=0, column=4, rowspan=2, padx=10)
        tk.Button(btn_f, text="BUY", bg="green", fg="white", width=8, command=lambda: self.submit("BUY")).grid(row=0, column=0, padx=2)
        tk.Button(btn_f, text="SELL", bg="red", fg="white", width=8, command=lambda: self.submit("SELL")).grid(row=0, column=1, padx=2)
        tk.Button(btn_f, text="BUY LIMIT", bg="#2980b9", fg="white", width=10, command=lambda: self.submit("BUY_LIMIT")).grid(row=1, column=0, padx=2, pady=2)
        tk.Button(btn_f, text="SELL LIMIT", bg="#8e44ad", fg="white", width=10, command=lambda: self.submit("SELL_LIMIT")).grid(row=1, column=1, padx=2, pady=2)

        # --- [3] Global Control Buttons ---
        ctrl_f = tk.Frame(self.root)
        ctrl_f.pack(fill="x", padx=10)
        tk.Button(ctrl_f, text="Check Servers", command=self.check_health).pack(side="left", padx=5)
        tk.Button(ctrl_f, text="Refresh Data", bg="#f1c40f", command=self.refresh_all).pack(side="left", padx=5)

        # --- [4] Tables (Positions / Orders) ---
        self.tabs = ttk.Notebook(self.root)
        self.tabs.pack(fill="both", expand=True, padx=10, pady=5)

        self.tree_pos = ttk.Treeview(self.tabs, columns=("Svr", "ID", "Sym", "Type", "Lot", "Prc", "SL", "TP", "Profit"), show="headings")
        for c in self.tree_pos["columns"]: self.tree_pos.heading(c, text=c); self.tree_pos.column(c, width=80)
        self.tabs.add(self.tree_pos, text="Open Positions")

        self.tree_ord = ttk.Treeview(self.tabs, columns=("Svr", "ID", "Sym", "Type", "Lot", "Prc", "SL", "TP"), show="headings")
        for c in self.tree_ord["columns"]: self.tree_ord.heading(c, text=c); self.tree_ord.column(c, width=80)
        self.tabs.add(self.tree_ord, text="Pending Orders")

        # --- [5] Table Actions ---
        act_f = tk.Frame(self.root)
        act_f.pack(fill="x", padx=10)
        tk.Button(act_f, text="CLOSE SELECTED", bg="orange", command=self.close_selected).pack(side="left", padx=5)
        tk.Button(act_f, text="CANCEL ORDER", bg="gray", command=self.cancel_selected).pack(side="left", padx=5)
        tk.Button(act_f, text="MODIFY SL/TP", command=self.modify_selected).pack(side="left", padx=5)

        # Log
        self.log_box = tk.Text(self.root, height=10); self.log_box.pack(fill="both", padx=10, pady=5)

    def log(self, msg): self.log_box.insert("end", f"> {msg}\n"); self.log_box.see("end")

    def submit(self, order_type):
        payload = {
            "symbol": self.cmb_symbol.get(), "volume": float(self.ent_lot.get()), "type": order_type,
            "price": float(self.ent_prc.get()), "sl": float(self.ent_sl.get()), "tp": float(self.ent_tp.get())
        }
        for s in SERVERS: self.executor.submit(self.api_call, s, "/order", payload)

    def api_call(self, s, ep, payload=None):
        try:
            h = {"Authorization": s['token']}
            r = requests.post(f"{s['url']}{ep}", json=payload, headers=h) if payload else requests.get(f"{s['url']}{ep}", headers=h)
            self.log(f"[{s['name']}] {r.json()}")
            self.root.after(1000, self.refresh_all)
        except: self.log(f"[{s['name']}] Connection Failed")

    def refresh_all(self):
        self.tree_pos.delete(*self.tree_pos.get_children())
        self.tree_ord.delete(*self.tree_ord.get_children())
        for s in SERVERS:
            self.executor.submit(self.update_account, s)
            self.executor.submit(self.update_tables, s)

    def update_account(self, s):
        try:
            r = requests.get(f"{s['url']}/account", headers={"Authorization": s['token']}).json()
            self.acc_widgets[s['name']].config(text=f"Balance: {r['balance']:.2f}\nEquity: {r['equity']:.2f}\nProfit: {r['profit']:.2f}")
        except: pass

    def update_tables(self, s):
        try:
            h = {"Authorization": s['token']}
            pos = requests.get(f"{s['url']}/positions", headers=h).json()
            for p in pos: self.tree_pos.insert("", "end", values=(s['name'], p['ticket'], p['symbol'], p['type'], p['volume'], p['price'], p['sl'], p['tp'], p['profit']))
            ords = requests.get(f"{s['url']}/orders", headers=h).json()
            for o in ords: self.tree_ord.insert("", "end", values=(s['name'], o['ticket'], o['symbol'], o['type'], o['volume'], o['price'], o['sl'], o['tp']))
        except: pass

    def check_health(self):
        for s in SERVERS:
            try:
                r = requests.get(f"{s['url']}/health").json()
                self.log(f"[{s['name']}] Status: {r['status']}")
            except: self.log(f"[{s['name']}] Status: Offline")

    def close_selected(self):
        sel = self.tree_pos.selection()
        if not sel: return
        v = self.tree_pos.item(sel[0], "values")
        s = next(x for x in SERVERS if x['name'] == v[0])
        self.api_call(s, "/order", {"type": "CLOSE", "ticket": int(v[1]), "symbol": v[2], "volume": float(v[4])})

    def cancel_selected(self):
        sel = self.tree_ord.selection()
        if not sel: return
        v = self.tree_ord.item(sel[0], "values")
        s = next(x for x in SERVERS if x['name'] == v[0])
        self.api_call(s, "/order", {"type": "CANCEL", "ticket": int(v[1]), "symbol": v[2], "volume": float(v[4])})

    def modify_selected(self):
        sel = self.tree_pos.selection() or self.tree_ord.selection()
        if not sel: return
        v = self.tree_pos.item(sel[0], "values") if self.tree_pos.selection() else self.tree_ord.item(sel[0], "values")
        s = next(x for x in SERVERS if x['name'] == v[0])
        self.api_call(s, "/order", {"type": "MODIFY", "ticket": int(v[1]), "symbol": v[2], "sl": float(self.ent_sl.get()), "tp": float(self.ent_tp.get()), "volume": float(v[4])})

if __name__ == "__main__":
    root = tk.Tk()
    app = TradeClient(root)
    root.mainloop()