import yfinance as yf
import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator, MACD
from ta.volatility import BollingerBands
import asyncio
from telegram import Bot
import schedule
import time
from datetime import datetime

# ================================
# CONFIGURAZIONE — MODIFICA QUI
# ================================
TELEGRAM_TOKEN = "8974017579:AAEU-ZSxhdcono0qgBYQhEPPeMMs2hRELf4"
CHAT_ID = "520150144"

TITOLI = {
    "Tech / Nasdaq": [
        "NVDA", "AAPL", "MSFT", "META", "AMD", "GOOGL", "AMZN", "TSLA",
        "SMCI", "PLTR", "INTC", "QCOM", "AVGO", "NFLX", "PYPL",
        "ADBE", "CRM", "NOW", "PANW", "SPCX"
    ],
    "Energia": [
        "XOM", "CVX", "SLB", "EOG", "COP"
    ],
    "Salute / Pharma": [
        "JNJ", "PFE", "MRK", "ABBV", "LLY", "UNH", "AMGN"
    ],
    "Italia (FTSE MIB)": [
        "ENI.MI", "ENEL.MI", "ISP.MI", "UCG.MI", "RACE.MI",
        "MB.MI", "TIT.MI", "G.MI", "PRY.MI"
    ]
}
# ================================

async def manda_messaggio(testo):
    bot = Bot(token=TELEGRAM_TOKEN)
    await bot.send_message(chat_id=CHAT_ID, text=testo)

def analizza(ticker, completo=False):
    try:
        dati = yf.download(ticker, period="6mo", interval="1d", progress=False)
        if dati.empty or len(dati) < 26:
            return None

        close = dati["Close"].squeeze()
        prezzo = close.iloc[-1]

        # RSI
        rsi = RSIIndicator(close).rsi().iloc[-1]

        # EMA
        ema50 = EMAIndicator(close, window=50).ema_indicator().iloc[-1] if len(dati) >= 50 else None
        ema200 = EMAIndicator(close, window=200).ema_indicator().iloc[-1] if len(dati) >= 200 else None

        # MACD
        macd_obj = MACD(close)
        macd_diff = macd_obj.macd_diff().iloc[-1]  # positivo = rialzista

        # Bande di Bollinger
        bb = BollingerBands(close)
        bb_high = bb.bollinger_hband().iloc[-1]
        bb_low = bb.bollinger_lband().iloc[-1]
        bb_segnale = ""
        if prezzo < bb_low:
            bb_segnale = "⬇️ Sotto banda bassa"
        elif prezzo > bb_high:
            bb_segnale = "⬆️ Sopra banda alta"

        # Trend EMA
        if ema50 and ema200:
            trend = "✅ Rialzista" if ema50 > ema200 else "❌ Ribassista"
        else:
            trend = "⏳ Dati insufficienti"

        # Riepilogo completo (per messaggio serale)
        if completo:
            return (
                f"📊 {ticker}\n"
                f"Prezzo: ${prezzo:.2f}\n"
                f"RSI: {rsi:.1f} | MACD: {'🟢' if macd_diff > 0 else '🔴'}\n"
                f"Trend: {trend}\n"
                f"Bollinger: {bb_segnale if bb_segnale else '➡️ Nella banda'}"
            )

        # Logica segnali
        segnale = None
        if rsi < 30 and macd_diff > 0 and (ema50 and ema200 and ema50 > ema200):
            segnale = "📈 SEGNALE BUY"
        elif rsi > 70 and macd_diff < 0 and (ema50 and ema200 and ema50 < ema200):
            segnale = "📉 SEGNALE SELL"
        elif prezzo < bb_low and rsi < 35:
            segnale = "📈 SEGNALE BUY (Bollinger)"
        elif prezzo > bb_high and rsi > 65:
            segnale = "📉 SEGNALE SELL (Bollinger)"

        if segnale:
            return (
                f"{segnale} — {ticker}\n"
                f"Prezzo: ${prezzo:.2f}\n"
                f"RSI: {rsi:.1f} | MACD: {'🟢' if macd_diff > 0 else '🔴'}\n"
                f"Trend EMA: {trend}\n"
                f"Bollinger: {bb_segnale if bb_segnale else '➡️ Nella banda'}"
            )

    except Exception:
        pass
    return None

def controlla_mercato():
    ora = datetime.now().strftime("%H:%M")
    print(f"Controllo mercato in corso alle {ora}...")
    messaggi = []

    for settore, tickers in TITOLI.items():
        segnali_settore = []
        for ticker in tickers:
            risultato = analizza(ticker)
            if risultato:
                segnali_settore.append(risultato)
        if segnali_settore:
            blocco = f"── {settore} ──\n" + "\n\n".join(segnali_settore)
            messaggi.append(blocco)

    if messaggi:
        testo = f"🤖 SEGNALI TRADING — {ora}\n\n" + "\n\n".join(messaggi)
    else:
        testo = f"🤖 Nessun segnale rilevante — {ora}"

    asyncio.run(manda_messaggio(testo))
    print("Messaggio inviato!")

def riepilogo_serale():
    ora = datetime.now().strftime("%H:%M")
    print(f"Riepilogo serale in corso alle {ora}...")
    righe = [f"📋 RIEPILOGO SERALE — {ora}\n"]

    for settore, tickers in TITOLI.items():
        righe.append(f"\n── {settore} ──")
        for ticker in tickers:
            risultato = analizza(ticker, completo=True)
            if risultato:
                righe.append(risultato)
            else:
                righe.append(f"⏳ {ticker} — dati non disponibili")

    testo = "\n\n".join(righe)

    # Telegram ha un limite di 4096 caratteri, dividiamo se necessario
    if len(testo) > 4000:
        meta = len(testo) // 2
        asyncio.run(manda_messaggio(testo[:meta]))
        asyncio.run(manda_messaggio(testo[meta:]))
    else:
        asyncio.run(manda_messaggio(testo))

    print("Riepilogo serale inviato!")

# Orari di controllo (ora italiana)
schedule.every().day.at("15:30").do(controlla_mercato)
schedule.every().day.at("17:30").do(controlla_mercato)
schedule.every().day.at("19:30").do(controlla_mercato)
schedule.every().day.at("21:30").do(controlla_mercato)
schedule.every().day.at("22:00").do(riepilogo_serale)

print("Bot avviato! Controlli alle 15:30 / 17:30 / 19:30 / 21:30 + riepilogo alle 22:00")
controlla_mercato()  # Test immediato all'avvio

while True:
    schedule.run_pending()
    time.sleep(60)