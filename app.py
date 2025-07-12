import os
from flask import Flask, render_template, request, jsonify
import pandas as pd
import yfinance as yf
import openai

app = Flask(__name__)

# store latest open price data for chat context
latest_data = {}


@app.route("/", methods=["GET", "POST"])
def index():
    global latest_data
    data = None
    symbol = ""
    start = ""
    end = ""
    if request.method == "POST":
        symbol = request.form.get("symbol", "").strip()
        start = request.form.get("start", "").strip()
        end = request.form.get("end", "").strip()
        if symbol and start and end:
            ticker = yf.Ticker(symbol)
            df = ticker.history(start=start, end=end)
            df = df.reset_index()
            data = df[["Date", "Open"]].to_dict(orient="records")
            latest_data = {
                row["Date"].strftime("%Y-%m-%d"): row["Open"] for row in data
            }
    return render_template("index.html", data=data, symbol=symbol, start=start, end=end)


@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message", "")
    if not user_message:
        return jsonify({"reply": "請輸入訊息"}), 400

    # construct system prompt with open price data
    context_lines = [f"{date}: {price}" for date, price in latest_data.items()]
    system_prompt = (
        "你是一個股票助理，能夠根據以下開盤價回答問題或提供解釋：\n"
        + "\n".join(context_lines)
    )

    openai.api_key = os.getenv("OPENAI_API_KEY")
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
        )
        reply = response.choices[0].message["content"]
    except Exception as e:
        reply = f"Error: {e}"
    return jsonify({"reply": reply})


if __name__ == "__main__":
    app.run(debug=True)
