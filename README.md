# Cryptocurrency Arbitrage Bot
Author: Jamie McKee

This Python script is an automated cryptocurrency arbitrage trading bot that utilizes the [CCXT library](https://github.com/ccxt/ccxt) to identify and execute profitable trades across multiple exchanges, initially only on a test network. The bot is designed to trade the following cryptocurrency pairs:

- ICP/USDT
- SOL/USDT
- BASE/USDT
- NEAR/USDT

## Features

- **Multi-Exchange Support**: Monitors and trades on Binance, Kraken, and Coinbase Pro.
- **Arbitrage Detection**: Identifies price differences between exchanges and calculates potential profit percentages.
- **Automated Trading**: Executes buy and sell orders to capitalize on arbitrage opportunities.
- **Logging**: Provides detailed logs for operations, including detected opportunities and executed trades.
- **Customizable Settings**: Adjustable profit thresholds, trade amounts, and trading pairs.

---

## Prerequisites

1. Python 3.6+
2. The `ccxt` library installed:
   ```bash
   pip install ccxt
   ```
3. API keys for the supported exchanges (Binance, Kraken, Coinbase Pro).

---

## Setup

1. **Clone the Repository**
   ```bash
   git clone https://github.com/jamie-codes/python-crypto-bot.git
   cd python-crypto-bot
   ```

2. **Configure API Keys**
   Replace `YOUR_API_KEY`, `YOUR_SECRET_KEY`, and any other necessary credentials for each exchange in the script where the `ccxt` instances are initialized.

3. **Install Dependencies**
   Ensure you have all required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the Bot**
   Execute the script:
   ```bash
   python crypto-arbitrage.py
   ```

---

## Usage

The bot will:

1. Fetch the latest bid and ask prices for the configured trading pairs from all supported exchanges.
2. Identify arbitrage opportunities based on the configured profit threshold (default: 0.5%).
3. Automatically execute trades for profitable opportunities.

### Customization

You can adjust the following parameters in the script:

- `SYMBOLS`: Add or remove trading pairs.
- `ARBITRAGE_THRESHOLD`: Set the minimum profit percentage for trades.
- `TRADE_AMOUNT`: Change the amount of cryptocurrency to trade.

---

## Example Log Output

```plaintext
2025-01-23 12:00:00 - INFO - Starting arbitrage bot...
2025-01-23 12:00:05 - INFO - Connected to binance
2025-01-23 12:00:05 - INFO - Connected to kraken
2025-01-23 12:00:05 - INFO - Connected to coinbasepro
2025-01-23 12:00:10 - INFO - Arbitrage opportunity for ICP/USDT: Buy on binance at 4.50, sell on kraken at 4.55, profit: 1.11%
2025-01-23 12:00:10 - INFO - Placing buy order on binance at 4.50 for 1 ICP
2025-01-23 12:00:11 - INFO - Placing sell order on kraken at 4.55 for 1 ICP
2025-01-23 12:00:12 - INFO - Trade executed: Bought ICP/USDT on binance and sold on kraken. Profit: 1.11%
```

---

## Enhancements (Planned Features)

1. **Fee Awareness**: Incorporate trading fees in profit calculations.
2. **Dynamic Trade Amounts**: Adjust trade sizes based on available balances.
3. **Portfolio Rebalancing**: Automate fund transfers between exchanges.
4. **Simulation Mode**: Test the bot in a non-trading environment.
5. **Database Integration**: Store historical data for performance analysis.
6. **Error Handling and Resilience**: Implement retry logic with exponential backoff for failed API calls and handle network issues gracefully.
7. **Web or Command Line Dashboard**: Create a real-time dashboard to display arbitrage opportunities, account balances, and trade history.
8. **Email or SMS Alerts**: Notify users when significant arbitrage opportunities or errors occur.
9. **Latency and Slippage Mitigation**: Monitor latency between exchanges and account for slippage in profit calculations.
10. **Rate Limiting Compliance**: Respect exchange rate limits to avoid temporary bans.
11. **Machine Learning Optimization**: Use machine learning to predict and filter profitable opportunities.
12. **Twitter/Social Media sentiment analysis**: Look into IBKR for sentiment values from news wire that includes tweets that impact crypto stocks.
---


