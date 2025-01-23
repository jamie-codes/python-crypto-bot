import ccxt
import time
import logging
from decimal import Decimal

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Exchanges to include in arbitrage
EXCHANGES = [
    'binance',
    'kraken',
    'coinbasepro'
]

# Arbitrage settings
SYMBOLS = ['ICP/USDT', 'SOL/USDT', 'BASE/USDT', 'NEAR/USDT']  # The trading pairs to arbitrage
ARBITRAGE_THRESHOLD = Decimal('0.5')  # Minimum percentage profit for arbitrage
TRADE_AMOUNT = Decimal('1')  # Amount to trade (adjust as needed)

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
        # Place buy order
        logging.info(f"Placing buy order on {opportunity['buy_exchange']} at {opportunity['buy_price']} for {TRADE_AMOUNT} {symbol.split('/')[0]}")
        buy_order = buy_exchange.create_order(
            symbol=symbol, type='market', side='buy', amount=float(TRADE_AMOUNT)
        )

        # Place sell order
        logging.info(f"Placing sell order on {opportunity['sell_exchange']} at {opportunity['sell_price']} for {TRADE_AMOUNT} {symbol.split('/')[0]}")
        sell_order = sell_exchange.create_order(
            symbol=symbol, type='market', side='sell', amount=float(TRADE_AMOUNT)
        )

        logging.info(f"Trade executed: Bought {symbol} on {opportunity['buy_exchange']} and sold on {opportunity['sell_exchange']}. Profit: {opportunity['profit_percent']:.2f}%")
    except Exception as e:
        logging.error(f"Failed to execute trade: {e}")


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