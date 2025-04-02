from fastapi import FastAPI
import requests
import pandas as pd
import ta

app = FastAPI()

symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT", "ADAUSDT", "DOGEUSDT", "AVAXUSDT"]

def get_ohlc(symbol="BTCUSDT", interval="1h", limit=100):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    response = requests.get(url)
    data = response.json()
    df = pd.DataFrame(data, columns=["timestamp", "open", "high", "low", "close", "volume", "_", "_", "_", "_", "_"])
    df["close"] = df["close"].astype(float)
    return df

def generate_signal(df):
    if df.shape[0] < 15:
        return {"error": "Not enough data to generate RSI"}
    rsi = ta.momentum.RSIIndicator(close=df["close"], window=14)
    df["RSI"] = rsi.rsi()
    if df["RSI"].isnull().all():
        return {"error": "RSI calculation failed"}
    last_rsi = df["RSI"].dropna().iloc[-1]
    if last_rsi < 30:
        return {"signal": "Buy", "rsi": round(last_rsi, 2)}
    elif last_rsi > 70:
        return {"signal": "Sell", "rsi": round(last_rsi, 2)}
    else:
        return {"signal": "Hold", "rsi": round(last_rsi, 2)}

@app.get("/")
def read_root():
    return {"message": "Crypto Signal API is running!"}

@app.get("/signal/{symbol}")
def get_signal(symbol: str = "BTCUSDT"):
    try:
        df = get_ohlc(symbol.upper())
        result = generate_signal(df)
        if "error" in result:
            return {"error": result["error"]}
        return {
            "symbol": symbol.upper(),
            "signal": result["signal"],
            "rsi": result["rsi"]
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/signal/all")
def get_all_signals():
    results = []
    for sym in symbols:
        try:
            df = get_ohlc(sym)
            result = generate_signal(df)
            if "error" not in result:
                results.append({
                    "symbol": sym,
                    "signal": result["signal"],
                    "rsi": result["rsi"]
                })
        except:
            results.append({
                "symbol": sym,
                "error": "Failed to fetch data"
            })
    return results
