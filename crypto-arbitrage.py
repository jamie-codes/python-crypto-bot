import ccxt
import time
import logging
import yaml
from decimal import Decimal
import smtplib
from email.mime.text import MIMEText
import requests
from functools import wraps
from threading import Thread
from prometheus_client import start_http_server, Summary, Gauge

# Load configuration from config.yaml
with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)

# Configure logging
logging.basicConfig(level=getattr(logging, config['logging']['level'].upper()), format='%(asctime)s - %(levelname)s - %(message)s')

# Prometheus metrics
CYCLE_TIME = Summary('arbitrage_cycle_time_seconds', 'Time taken for each arbitrage cycle')
OPPORTUNITIES_FOUND = Gauge('arbitrage_opportunities_found', 'Number of arbitrage opportunities found per cycle')
BALANCE_AVAILABLE = Gauge('arbitrage_balance_available', 'Available balance per exchange and currency', ['exchange', 'currency'])

# Extract configurations
EXCHANGES = config['exchanges']
SYMBOLS = config['arbitrage']['symbols']
ARBITRAGE_THRESHOLD = Decimal(str(config['arbitrage']['threshold']))
TRADE_AMOUNT = Decimal(str(config['arbitrage']['trade_amount']))
EMAIL_CONFIG = config['email']
TELEGRAM_CONFIG = config['telegram']
MAX_RETRIES = config['retry']['max_retries']
RETRY_DELAY = config['retry']['delay']
ORDER_BOOK_DEPTH = config['order_book']['depth']
TAKER_FEES = Decimal(str(config['fees']['taker_fee']))
MAX_RISK_PERCENTAGE = Decimal(str(config['risk_management']['max_risk_percentage']))
RISK_PER_SYMBOL = config['risk_management'].get('per_symbol', True)

exchanges = {}
balances = {}


def initialize_exchanges():
    for exchange_id in EXCHANGES:
        exchange = getattr(ccxt, exchange_id)()
        exchange.load_markets()
        exchanges[exchange_id] = exchange


def update_balances():
    for exchange_id, exchange in exchanges.items():
        balance = exchange.fetch_balance()
        balances[exchange_id] = balance
        for currency, amount in balance['total'].items():
            BALANCE_AVAILABLE.labels(exchange=exchange_id, currency=currency).set(amount)


@CYCLE_TIME.time()
def execute_arbitrage():
    initialize_exchanges()
    while True:
        try:
            update_balances()
            prices = fetch_prices()
            opportunities = find_arbitrage_opportunities(prices)
            OPPORTUNITIES_FOUND.set(len(opportunities))
            if not opportunities:
                logging.info("No opportunities found this cycle.")
            for opportunity in opportunities:
                symbol = opportunity['symbol']
                buy_exchange = exchanges[opportunity['buy_exchange']]
                sell_exchange = exchanges[opportunity['sell_exchange']]
                base_currency = symbol.split('/')[0]
                buy_balance = balances[opportunity['buy_exchange']][base_currency]['free']
                trade_amount = calculate_risk_adjusted_trade_amount(buy_balance, opportunity['buy_price'])

                if trade_amount <= 0:
                    logging.warning(f"Insufficient balance for {symbol}")
                    continue

                buy_exchange.create_market_buy_order(symbol, trade_amount)
                sell_exchange.create_market_sell_order(symbol, trade_amount)
                logging.info(f"Executed arbitrage for {symbol} with net profit {opportunity['net_profit']}%")

            time.sleep(1)
        except Exception as e:
            logging.error(f"Error during arbitrage execution: {e}")
            time.sleep(RETRY_DELAY)


if __name__ == "__main__":
    start_http_server(8000)
    execute_arbitrage()