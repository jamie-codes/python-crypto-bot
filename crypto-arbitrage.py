import ccxt
import time
import logging
import yaml
from decimal import Decimal
import smtplib
from email.mime.text import MIMEText
import requests
from functools import wraps

# Load configuration from config.yaml
with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)

# Configure logging
logging.basicConfig(
    level=getattr(logging, config['logging']['level']),
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Extract configurations
EXCHANGES = config['exchanges']
SYMBOLS = config['arbitrage']['symbols']
ARBITRAGE_THRESHOLD = Decimal(str(config['arbitrage']['threshold']))
TRADE_AMOUNT = Decimal(str(config['arbitrage']['trade_amount']))

EMAIL_ENABLED = config['email']['enabled']
SMTP_SERVER = config['email']['smtp_server']
SMTP_PORT = config['email']['smtp_port']
EMAIL_USERNAME = config['email']['username']
EMAIL_PASSWORD = config['email']['password']
NOTIFICATION_RECIPIENT = config['email']['recipient']

TELEGRAM_ENABLED = config['telegram']['enabled']
BOT_TOKEN = config['telegram']['bot_token']
CHAT_ID = config['telegram']['chat_id']

MAX_RETRIES = config['retry']['max_retries']
RETRY_DELAY = config['retry']['delay']

# Retry decorator
def retry(max_retries=MAX_RETRIES, delay=RETRY_DELAY):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    retries += 1
                    logging.warning(f"Attempt {retries} failed: {e}")
                    time.sleep(delay * retries)
            raise Exception(f"Max retries ({max_retries}) exceeded for {func.__name__}")
        return wrapper
    return decorator

# Initialize exchanges
exchanges = {}
for exchange_id in EXCHANGES:
    try:
        exchange = getattr(ccxt, exchange_id)()
        exchange.load_markets()
        exchanges[exchange_id] = exchange
        logging.info(f"Connected to {exchange_id}")
    except Exception as e:
        logging.error(f"Failed to connect to {exchange_id}: {e}")

def send_telegram_notification(message):
    if TELEGRAM_ENABLED:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {'chat_id': CHAT_ID, 'text': message}
        requests.post(url, json=payload)

@retry()
def fetch_prices():
    prices = {}
    for exchange_id, exchange in exchanges.items():
        for symbol in SYMBOLS:
            try:
                ticker = exchange.fetch_ticker(symbol)
                if exchange_id not in prices:
                    prices[exchange_id] = {}
                prices[exchange_id][symbol] = {
                    'bid': Decimal(str(ticker['bid'])),
                    'ask': Decimal(str(ticker['ask']))
                }
            except Exception as e:
                logging.warning(f"Error fetching ticker for {symbol} on {exchange_id}: {e}")
    return prices

def find_arbitrage(prices):
    opportunities = []
    for symbol in SYMBOLS:
        for buy_exchange_id, buy_prices in prices.items():
            for sell_exchange_id, sell_prices in prices.items():
                if buy_exchange_id != sell_exchange_id and symbol in buy_prices and symbol in sell_prices:
                    buy_price = buy_prices[symbol]['ask']
                    sell_price = sell_prices[symbol]['bid']
                    profit_percent = ((sell_price - buy_price) / buy_price) * 100
                    if profit_percent >= ARBITRAGE_THRESHOLD:
                        opportunities.append({
                            'symbol': symbol,
                            'buy_exchange': buy_exchange_id,
                            'sell_exchange': sell_exchange_id,
                            'buy_price': buy_price,
                            'sell_price': sell_price,
                            'profit_percent': profit_percent
                        })
    return opportunities

def execute_trade(opportunity):
    buy_exchange = exchanges[opportunity['buy_exchange']]
    sell_exchange = exchanges[opportunity['sell_exchange']]
    symbol = opportunity['symbol']
    try:
        base_currency, quote_currency = symbol.split('/')
        buy_balance = buy_exchange.fetch_balance()[quote_currency]['free']
        sell_balance = sell_exchange.fetch_balance()[base_currency]['free']
        trade_amount = min(TRADE_AMOUNT, sell_balance, buy_balance / opportunity['buy_price'])
        if trade_amount <= 0:
            logging.warning(f"Insufficient balance for trading {symbol}. Skipping.")
            return
        buy_exchange.create_order(symbol, 'market', 'buy', float(trade_amount))
        sell_exchange.create_order(symbol, 'market', 'sell', float(trade_amount))
        logging.info(f"Trade executed: Bought {symbol} on {opportunity['buy_exchange']} and sold on {opportunity['sell_exchange']}. Profit: {opportunity['profit_percent']:.2f}%")
        if EMAIL_ENABLED:
            send_email_notification(opportunity, trade_amount)
        if TELEGRAM_ENABLED:
            send_telegram_notification(f"Arbitrage trade executed: {opportunity}")
    except Exception as e:
        logging.error(f"Failed to execute trade: {e}")

def send_email_notification(opportunity, trade_amount):
    try:
        msg = MIMEText(f"Arbitrage Trade Executed:\n\nSymbol: {opportunity['symbol']}\nBuy Exchange: {opportunity['buy_exchange']}\nSell Exchange: {opportunity['sell_exchange']}\nBuy Price: {opportunity['buy_price']}\nSell Price: {opportunity['sell_price']}\nTrade Amount: {trade_amount}\nProfit: {opportunity['profit_percent']:.2f}%")
        msg['Subject'] = "Arbitrage Trade Notification"
        msg['From'] = EMAIL_USERNAME
        msg['To'] = NOTIFICATION_RECIPIENT
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
            server.send_message(msg)
        logging.info("Email notification sent.")
    except Exception as e:
        logging.error(f"Failed to send email notification: {e}")

if __name__ == '__main__':
    logging.info("Starting arbitrage bot...")
    while True:
        try:
            prices = fetch_prices()
            opportunities = find_arbitrage(prices)
            if opportunities:
                for opportunity in opportunities:
                    execute_trade(opportunity)
            else:
                logging.info("No arbitrage opportunities found.")
            time.sleep(5)
        except KeyboardInterrupt:
            logging.info("Arbitrage bot stopped by user.")
            break
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
