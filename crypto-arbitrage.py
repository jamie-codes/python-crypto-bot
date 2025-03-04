import ccxt
import time
import logging
import yaml
from decimal import Decimal
from prometheus_client import start_http_server, Summary, Gauge
from logging import handlers
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_fixed
from rich.console import Console
from threading import Thread

# Load environment variables
load_dotenv()

# Initialize rich console
console = Console()

# Load configuration from config.yaml
with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)

# Configure logging
logger = logging.getLogger()
logger.setLevel(getattr(logging, config['logging']['level'].upper()))
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

logstash_handler = handlers.SysLogHandler(address=(config['efk']['logstash_host'], config['efk']['logstash_port']))
logstash_handler.setFormatter(formatter)
logger.addHandler(logstash_handler)

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

@retry(stop=stop_after_attempt(MAX_RETRIES), wait=wait_fixed(RETRY_DELAY))
def initialize_exchanges():
    for exchange_id in EXCHANGES:
        exchange = getattr(ccxt, exchange_id)()
        exchange.load_markets()
        exchanges[exchange_id] = exchange


@retry(stop=stop_after_attempt(MAX_RETRIES), wait=wait_fixed(RETRY_DELAY))
def update_balances():
    for exchange_id, exchange in exchanges.items():
        balance = exchange.fetch_balance()
        balances[exchange_id] = balance
        for currency, amount in balance['total'].items():
            BALANCE_AVAILABLE.labels(exchange=exchange_id, currency=currency).set(amount)


@retry(stop=stop_after_attempt(MAX_RETRIES), wait=wait_fixed(RETRY_DELAY))
def fetch_prices():
    prices = {}
    threads = []

    def fetch(exchange_id, exchange):
        for symbol in SYMBOLS:
            try:
                ticker = exchange.fetch_ticker(symbol)
                if ticker['ask'] is None or ticker['bid'] is None:
                    logger.warning(f"Incomplete ticker data for {symbol} on {exchange_id}")
                    continue
                if exchange_id not in prices:
                    prices[exchange_id] = {}
                prices[exchange_id][symbol] = ticker
            except Exception as e:
                logger.error(f"Error fetching ticker for {symbol} on {exchange_id}: {e}")

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
                console.log("[bold yellow]No opportunities found this cycle.[/bold yellow]")
            for opportunity in opportunities:
                symbol = opportunity['symbol']
                buy_exchange = exchanges[opportunity['buy_exchange']]
                sell_exchange = exchanges[opportunity['sell_exchange']]
                base_currency = symbol.split('/')[0]
                buy_balance = balances[opportunity['buy_exchange']].get(base_currency, {}).get('free', 0)

                if buy_balance == 0:
                    console.log(f"[bold red]Zero balance for {base_currency} on {opportunity['buy_exchange']}[/bold red]")
                    continue

                trade_amount = calculate_risk_adjusted_trade_amount(buy_balance, opportunity['buy_price'])

                if trade_amount <= 0:
                    console.log(f"[bold red]Insufficient trade amount for {symbol}[/bold red]")
                    continue

                buy_exchange.create_market_buy_order(symbol, trade_amount)
                sell_exchange.create_market_sell_order(symbol, trade_amount)
                console.log(f"[bold green]Executed arbitrage for {symbol} with net profit {opportunity['net_profit']}%[/bold green]")

            time.sleep(RETRY_DELAY)
        except Exception as e:
            logger.error(f"Error during arbitrage execution: {e}")
            time.sleep(RETRY_DELAY)


if __name__ == "__main__":
    start_http_server(8000)
    execute_arbitrage()
