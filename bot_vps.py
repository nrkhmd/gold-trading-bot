import MetaTrader5 as mt5
import pandas as pd
import requests
import time

# --- SETUP TELEGRAM ---
TOKEN = "8544691510:AAFZPm6QsANs6sGFhIrYpcuRvkdWcQgb3wc" # Ganti jika kamu sudah revoke
CHAT_ID = "8544691510"
SYMBOL = "XAUUSD.m" # Cek di Market Watch, pastikan namanya sama persis

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={msg}"
    requests.get(url)

# --- INITIALIZE MT5 ---
if not mt5.initialize():
    print("Gagal konek ke terminal MT5, pastikan MT5 sudah terbuka!")
    quit()

def get_live_data(tf, count=200):
    # Mengambil data langsung dari terminal
    rates = mt5.copy_rates_from_pos(SYMBOL, tf, 0, count)
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    
    # Indikator RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / (loss + 1e-9))))
    
    # Indikator MA & Volume
    df['MA20'] = df['close'].rolling(20).mean()
    df['VOL_AVG'] = df['tick_volume'].rolling(10).mean()
    return df

print("🚀 Bot VPS sudah RUNNING...")
send_telegram("✅ BOT EMAS AKTIF DI VPS\nStandby memantau H1 dan M15...")

while True:
    try:
        df_h1 = get_live_data(mt5.TIMEFRAME_H1)
        df_m15 = get_live_data(mt5.TIMEFRAME_M15)
        
        h1 = df_h1.iloc[-1]
        m15 = df_m15.iloc[-1]
        
        # LOGIKA KAMU: Volume Momentum + H1 RSI + M15 MA
        vol_ok = m15['tick_volume'] > m15['VOL_AVG']
        
        # BUY SIGNAL
        if vol_ok and h1['RSI'] < 35 and m15['close'] > m15['MA20']:
            price = m15['close']
            sl = price - 25  # SL sekitar 2.5 pips/poin
            tp = price + 50  # TP (Risk Reward 1:2)
            send_telegram(f"🟢 BUY XAUUSD\nPrice: {price}\nSL: {sl}\nTP: {tp}")
            time.sleep(900) # Sleep 15 menit biar gak spam sinyal sama

        # SELL SIGNAL
        elif vol_ok and h1['RSI'] > 65 and m15['close'] < m15['MA20']:
            price = m15['close']
            sl = price + 25
            tp = price - 50
            send_telegram(f"🔴 SELL XAUUSD\nPrice: {price}\nSL: {sl}\nTP: {tp}")
            time.sleep(900)

    except Exception as e:
        print(f"Error: {e}")
    
    time.sleep(15) # Cek market setiap 15 detik
