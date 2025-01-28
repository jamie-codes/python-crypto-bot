import ccxt
import time
import logging
import yaml
from decimal import Decimal
import smtplib
from email.mime.text import MIMEText
import requests
import time
from functools import wraps

# Load configuration from config.yaml
with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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



def retry(max_retries=3, delay=1):
    ''' Retry decorator for when network issues or API rate limits can cause temporary failures'''
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

@retry(max_retries=5, delay=0.5)
def send_telegram_notification(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': CHAT_ID,
        'text': message
    }
    requests.post(url, json=payload)

@retry(max_retries=5, delay=2)
def fetch_prices():
    """Fetch the latest bid and ask prices from all exchanges."""
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
    """Find arbitrage opportunities based on bid-ask spreads."""
    opportunities = []
    for symbol in SYMBOLS:
        for buy_exchange_id, buy_prices in prices.items():
            for sell_exchange_id, sell_prices in prices.items():
                if buy_exchange_id != sell_exchange_id and symbol in buy_prices and symbol in sell_prices:
                    buy_price = buy_prices[symbol]['ask']
                    sell_price = sell_prices[symbol]['bid']

                    # Calculate potential profit
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
    """Execute arbitrage trade."""
    buy_exchange = exchanges[opportunity['buy_exchange']]
    sell_exchange = exchanges[opportunity['sell_exchange']]
    symbol = opportunity['symbol']

    try:
        # Check balances dynamically
        base_currency = symbol.split('/')[0]
        quote_currency = symbol.split('/')[1]

        buy_balance = buy_exchange.fetch_balance()[quote_currency]['free']
        sell_balance = sell_exchange.fetch_balance()[base_currency]['free']

        trade_amount = min(TRADE_AMOUNT, sell_balance, buy_balance / opportunity['buy_price'])

        if trade_amount <= 0:
            logging.warning(f"Insufficient balance for trading {symbol}. Skipping.")
            return

        # Place buy order
        logging.info(f"Placing buy order on {opportunity['buy_exchange']} at {opportunity['buy_price']} for {trade_amount} {base_currency}")
        buy_order = buy_exchange.create_order(
            symbol=symbol, type='market', side='buy', amount=float(trade_amount)
        )

        # Place sell order
        logging.info(f"Placing sell order on {opportunity['sell_exchange']} at {opportunity['sell_price']} for {trade_amount} {base_currency}")
        sell_order = sell_exchange.create_order(
            symbol=symbol, type='market', side='sell', amount=float(trade_amount)
        )

        logging.info(f"Trade executed: Bought {symbol} on {opportunity['buy_exchange']} and sold on {opportunity['sell_exchange']}. Profit: {opportunity['profit_percent']:.2f}%")

        # Send email notification
        if EMAIL_ENABLED:
            send_email_notification(opportunity, trade_amount)
        # Send telegram notification
        if TELEGRAM_ENABLED:
            notification_message = f"{opportunity} - {trade_amount}"
            send_telegram_notification(notification_message)

    except Exception as e:
        logging.error(f"Failed to execute trade: {e}")


def send_email_notification(opportunity, trade_amount):
    """Send email notification for executed trades."""
    try:
        msg = MIMEText(f"Arbitrage Trade Executed:\n\nSymbol: {opportunity['symbol']}\nBuy Exchange: {opportunity['buy_exchange']}\nSell Exchange: {opportunity['sell_exchange']}\nBuy Price: {opportunity['buy_price']}\nSell Price: {opportunity['sell_price']}\nTrade Amount: {trade_amount}\nProfit: {opportunity['profit_percent']:.2f}%")
        msg['Subject'] = "Arbitrage Trade Notification"
        msg['From'] = EMAIL_USERNAME
        msg['To'] = NOTIFICATION_RECIPIENT

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
            server.send_message(msg)

        logging.info(f"Email notification sent to {NOTIFICATION_RECIPIENT}")
    except Exception as e:
        logging.error(f"Failed to send email notification: {e}")


if __name__ == '__main__':
    logging.info("Starting arbitrage bot...")
    while True:
        try:
            # Fetch prices
            prices = fetch_prices()

            # Find arbitrage opportunities
            opportunities = find_arbitrage(prices)
            if opportunities:
                for opportunity in opportunities:
                    logging.info(f"Arbitrage opportunity for {opportunity['symbol']}: Buy on {opportunity['buy_exchange']} at {opportunity['buy_price']}, sell on {opportunity['sell_exchange']} at {opportunity['sell_price']}, profit: {opportunity['profit_percent']:.2f}%")

                    # Execute the trade
                    execute_trade(opportunity)
            else:
                logging.info("No arbitrage opportunities found.")

            # Wait before the next iteration
            time.sleep(5)

        except KeyboardInterrupt:
            logging.info("Arbitrage bot stopped by user.")
            break
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
