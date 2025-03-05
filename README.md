# Cryptocurrency Arbitrage Bot
Author: Jamie McKee

This Python script is a cryptocurrency arbitrage trading bot using the [CCXT library](https://github.com/ccxt/ccxt). It identifies and executes profitable trades across multiple exchanges and now includes enhanced monitoring, risk management, and logging features.

## Directory Structure

```plaintext
python-crypto-bot/
├── config.yaml                      # Main configuration file for exchanges, thresholds, and settings
├── crypto-arbitrage.py              # The main arbitrage bot script
├── README.md                        # Documentation and usage instructions
├── requirements.txt                 # Python dependencies
├── tree.log                         # Optional log of the project directory structure
├── etc/
│   ├── grafana/
│   │   └── dashboards/
│   │       └── crypto_arbitrage_dashboard.json  # Grafana dashboard for metrics
│   ├── kibana/
│   │   └── crypto_arbitrage_logs_dashboard.json  # Kibana dashboard for log monitoring
│   ├── logstash/
│   │   └── logstash.conf            # Logstash configuration for forwarding logs to Elasticsearch
│   └── prometheus/
│       └── prometheus.yml           # Prometheus configuration for scraping bot metrics
└── src/
    ├── main.py                      # Optional additional logic or entry point
    ├── trading_logic                # Placeholder for trading logic extensions
    └── exchanges/
        ├── binance.py               # Exchange-specific integration for Binance
        └── coinbase.py              # Exchange-specific integration for Coinbase
```

## Supported Pairs

- ICP/USDT
- SOL/USDT
- BASE/USDT
- NEAR/USDT

## New Features

- **EFK Integration**: Logs are shipped to Elasticsearch via Logstash and visualized in Kibana.
- **Prometheus + Grafana Monitoring**: Real-time metrics on cycle times, balances, and opportunities.
- **Order Book Depth Analysis**: Ensures liquidity before trades.
- **Transaction Cost Consideration**: Profit calculations include trading fees.
- **Portfolio & Risk Management**: Trades respect maximum exposure per symbol.
- **Parallel Price Fetching**: Faster, multi-threaded price collection.
- **Balance Caching**: Optimized balance updates to reduce API load.

---

## Prerequisites

1. Python 3.6+
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Running Prometheus and Grafana.
4. Running the EFK stack (Elasticsearch, Fluentd/Logstash, Kibana).

---

## Setup

1. **Clone the Repository**
   ```bash
   git clone https://github.com/jamie-codes/python-crypto-bot.git
   cd python-crypto-bot
   ```

2. **Configure API Keys & Credentials**
   Update your API keys inside your `.env` or `config.yaml` as needed.

3. **Configure `config.yaml`**
   Configure the config to your requirements.

4. **Run Prometheus**
   Use `prometheus.yml` to scrape metrics on port `8000`.

5. **Run Logstash**
   Configure `logstash.conf` to listen on port `5000` and forward logs to Elasticsearch.

6. **Import Grafana/Kibana Dashboards**
   Upload the provided JSON files to Grafana and Kibana to be able to visualise the metrics and logs.

7. **Start the Bot**
   ```bash
   python crypto-arbitrage.py
   ```

---

## Monitoring

- **Prometheus**: Metrics at `http://localhost:8000/metrics`.
- **Grafana**: Visual dashboards for cycle time, balances, and opportunities.
- **Kibana**: Live log streams and historical log analysis.

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

- Machine Learning Opportunity Filtering
- Portfolio Rebalancing
- Simulation/Test Mode
- Database Integration
- Advanced Latency and Slippage Analysis
- Social Sentiment Analysis (e.g., Twitter, IBKR feeds)
- Integration with other exchanges (e.g., Huobi, Binance Futures)
