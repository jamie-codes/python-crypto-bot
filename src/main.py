from exchanges.binance import Binance
from exchanges.coinbase import Coinbase
from trading_logic import execute_trade
import yaml
import os

# Load configuration
with open("config/config.yaml", "r") as f:
    config = yaml.safe_load(f)

# Initialize exchanges
binance = Binance(config["binance"]["api_key"], config["binance"]["api_secret"])
coinbase = Coinbase(config["coinbase"]["api_key"], config["coinbase"]["api_secret"])

# Execute trades
execute_trade(binance, "BTCUSDT", 0.01)
execute_trade(coinbase, "BTC-USD", 0.01)