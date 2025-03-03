import ccxt
import time
import logging
import yaml
from decimal import Decimal
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


def fetch_prices():
    prices = {}
    threads = []

    def fetch(exchange_id, exchange):
        for symbol in SYMBOLS:
            ticker = exchange.fetch_ticker(symbol)
            if exchange_id not in prices:
                prices[exchange_id] = {}
            prices[exchange_id][symbol] = ticker

    for exchange_id, exchange in exchanges.items():
        thread = Thread(target=fetch, args=(exchange_id, exchange))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    return prices


def calculate_risk_adjusted_trade_amount(balance, price):
    risk_amount = (balance * MAX_RISK_PERCENTAGE) / 100
    return min(risk_amount / price, TRADE_AMOUNT)


def find_arbitrage_opportunities(prices):
    opportunities = []
    for symbol in SYMBOLS:
        for buy_exchange_id, buy_data in prices.items():
            for sell_exchange_id, sell_data in prices.items():
                if buy_exchange_id == sell_exchange_id:
                    continue
                buy_price = buy_data[symbol]['ask']
                sell_price = sell_data[symbol]['bid']
                profit = ((sell_price - buy_price) / buy_price) * 100 - (TAKER_FEES * 2)
                if profit >= ARBITRAGE_THRESHOLD:
                    opportunities.append({
                        'symbol': symbol,
                        'buy_exchange': buy_exchange_id,
                        'sell_exchange': sell_exchange_id,
                        'buy_price': buy_price,
                        'sell_price': sell_price,
                        'net_profit': profit
                    })
    return opportunities


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
                buy_balance = balances[opportunity['buy_exchange']].get(base_currency, {}).get('free', 0)
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
