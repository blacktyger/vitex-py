## Python wrapper for vitex.net API v2

###### vitex-py by `blacktyger


## Installation:
<code>python -m pip install vitexpy</code>

## Description:
Python wrapper for ViteX - Decentralized cryptocurrency exchange API.

- URL: https://x.vite.net/
- API DOCUMENTATION: https://vite.wiki/dex/api/dex-apis.html#overview

## Features:
- Handling transaction signatures required by ViteX API
- Decimals library to keep high precision with floating point numbers 
- Well documented and readable for everyone
- OOP approach with **Token**, **TraidingPair**, **Order**, and **API** objects


## How to use:
- 🔎 **PublicAPI** can be used out of the box without API keys, 
enough to extract most of market data available for this platform
- All PublicAPI endpoints https://vite.wiki/dex/api/dex-apis.html#public-rest-api

```
from vitexpy import PublicAPI

api = PublicAPI(print_response=True)  # Default: False

# Test connection with ViteX server
api.test_connection()
>>> Successfully connected to ViteX API with vitex-py module
>>> Server time: 2021-10-28 12:50:44.469000
>>> USD  /  CNY: 6.466199999999926

# Get list with Token object/s
api.get_token('EPIC-002')  
>>> [Token(EPIC-002)]

# Get list with all Token object/s
api.get_all_tokens()  
>>> [Token(AAVO-000), Token(ABC-000), Token(AGS-000), ...]

# Get list with TradingPair object/s
api.get_trading_pair('EPIC-002_BTC-000')  
>>> [TradingPair(EPIC-002/BTC-000)]

```





- 📈 **TradingAPI** requires signature authentication by API Key and API Secret,
  which you can apply for on ViteX platform.
  Please note that API Key and API Secret are both case sensitive. 
  Also it is recommended to stake some VITE for QUOTA ('transactions fuel') 
  in order to execute multiple transactions. 
- All TradingAPI endpoints https://vite.wiki/dex/api/dex-apis.html#private-rest-api

```
from vitexpy import TradingAPI, TradingPair

api_key = "YOUR VITEX API KEY"
api_secret = "YOUR VITEX API SECRET"

api = TradingAPI(api_key=user_key,
                 api_secret=user_secret,
                 print_response=True)

# Create dictionary with required values
order_params = {
    'test': True,  # Optional, when True transactions are not executed in network
    'symbol': 'EPIC-002_BTC-000',  # Market pair symbol ('BASE-XXX_QUOTA-XXX')
    'amount': 5,  # Amount to buy or sell in base token ('EPIC-002' in this case)
    'price': 0.00006000,  # Price for each base token ('EPIC-002') in quota token ('BTC-000')
    'side': 1,  # Buy(0) or Sell(1)
    }

# Create Order object with given params
order = api.prepare_order(**order_params)  

# Prepare, sign and execute Order object to Vitex network
api.execute_order(order)  

# Cancel all orders within given pair (TradingPair object or string with symbol)
api.cancel_all_orders(pair='EPIC-002_BTC-00')

```
## 💌 Donations
Project is **open-source** and free, if you like it please consider donation:
- Vite Chain: vite_15d3230e3c31c009c968beea7160ae98b491475236ae2cddbc
- EPIC Chain: https://fastepic.eu/keybaseid_blacktyg3r
- WAN  Chain: 0x37b056F68120a250D28C7de9650Fa02Ee740fec1 
- BSC  Chain: 0xE6F431178cD7B44FBCb4381eBDb14Db213BDD866

Contact: [@blacktyg3r via Telegram](https://telegram.me/blacktyg3r)

**Thanks!**
