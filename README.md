# Cryptocurrency Arbitrage Bot
Author: Jamie McKee

This Python script is a cryptocurrency arbitrage trading bot using the [CCXT library](https://github.com/ccxt/ccxt). It identifies and executes profitable trades across multiple exchanges and now includes enhanced monitoring, risk management, and logging features.

## Directory Structure

```plaintext
python-crypto-bot/
├── config.yaml                      # Main configuration file for exchanges, thresholds, and settings
├── crypto-arbitrage.py              # The main arbitrage bot script
├── Dockerfile                       # Dockerfile for optionally containerizing the app
├── docker-compose.yml               # Docker compose file to bundle the monitoring tools together
├── README.md                        # Documentation and usage instructions
├── requirements.txt                 # Python dependencies
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

## New Libraries Included

- **python-dotenv**: Load environment variables from `.env` files.
- **tenacity**: Advanced retry mechanisms for API calls.
- **rich**: Enhanced console output with better formatting.

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


## Optional: Run on EC2 with Docker Compose
These optional steps will Dockerize the bot and run it on an AWS EC2 instance, along with bundling Prometheus, Grafana, and Logstash to run together.

1. Launch a **t2.micro** EC2 instance (Ubuntu 20.04 or Amazon Linux).
2. Install Docker:
   ```bash
   sudo apt update
   sudo apt install -y docker.io
   sudo systemctl start docker
   sudo systemctl enable docker
   sudo usermod -aG docker ubuntu
   ```
3. Install Docker Compose:
   ```bash
   sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
   sudo chmod +x /usr/local/bin/docker-compose
   ```
4. Clone the repository:
   ```bash
   git clone https://github.com/jamie-codes/python-crypto-bot.git
   cd python-crypto-bot
   ```
5. Add your **API keys** and configure `config.yaml`.
6. Build and run the full monitoring stack:
   ```bash
   docker-compose up --build -d
   ```
7. Access your monitoring tools:
   - Prometheus: `http://<EC2-IP>:9090`
   - Grafana: `http://<EC2-IP>:3000`
   - Kibana: `http://<EC2-IP>:5601`

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
