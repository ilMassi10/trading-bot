import yfinance as yf
import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator
import asyncio
from telegram import Bot
import schedule
import time
from datetime import datetime

# ================================
# CONFIGURAZIONE — MODIFICA QUI
# ================================
TELEGRAM_TOKEN = "8974017579:AAHJ-tyIjPrd6Haf9-Pe62QWlS5PUc6IGVI"
CHAT_ID = "520150144"

TITOLI = {
    "Tech / Nasdaq": [
        "NVDA", "AAPL", "MSFT", "META", "AMD", "GOOGL", "AMZN", "TSLA",
        "SMCI", "PLTR", "INTC", "QCOM", "AVGO", "NFLX", "PYPL",
        "ADBE", "CRM", "NOW", "PANW"
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

def analizza(ticker):
    try:
        dati = yf.download(ticker, period="6mo", interval="1d", progress=False)
        if dati.empty or len(dati) < 50:
            return None

        close = dati["Close"].squeeze()

        rsi = RSIIndicator(close).rsi().iloc[-1]
        ema50 = EMAIndicator(close, window=50).ema_indicator().iloc[-1]
        ema200 = EMAIndicator(close, window=200).ema_indicator().iloc[-1]
        prezzo = close.iloc[-1]

        segnale = None
        if rsi < 30 and ema50 > ema200:
            segnale = "📈 SEGNALE BUY"
        elif rsi > 70 and ema50 < ema200:
            segnale = "📉 SEGNALE SELL"

        if segnale:
            trend = "✅ Rialzista" if ema50 > ema200 else "❌ Ribassista"
            return (
                f"{segnale} — {ticker}\n"
                f"Prezzo: ${prezzo:.2f}\n"
                f"RSI(14): {rsi:.1f}\n"
                f"Trend EMA50/200: {trend}"
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

# Orari di controllo (ora italiana, durante borsa USA)
schedule.every().day.at("15:30").do(controlla_mercato)
schedule.every().day.at("17:30").do(controlla_mercato)
schedule.every().day.at("19:30").do(controlla_mercato)
schedule.every().day.at("21:30").do(controlla_mercato)

print("Bot avviato! Controlli alle 15:30 / 17:30 / 19:30 / 21:30 (ora italiana)")
controlla_mercato()  # Test immediato all'avvio

while True:
    schedule.run_pending()
    time.sleep(60)