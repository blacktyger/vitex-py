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
- OOP approach with **Order** and **API** objects


## How to use:
- 🔎 **PublicAPI** can be used out of the box without API keys, 
enough to extract most of market data available for this platform


```
from vitexpy import PublicAPI

api = PublicAPI(print_response=True)  # Default: False

api.test_connection()
>>> Successfully connected to ViteX API with vitex-py module
>>> Server time: 2021-10-28 12:50:44.469000
>>> USD  /  CNY: 6.466199999999926

api.get_token_detail('EPIC-002')
>>> {'code': 0, 'msg': 'ok', 'data': {
>>>  'tokenId': 'tti_f370fadb275bc2a1a839c753', 
>>>  'name': 'Epic Cash', 'symbol': 'EPIC-002', 
>>>  'originalSymbol': 'EPIC', ...}, }

api.get_trading_pair('EPIC-002_BTC-000')
>>> {'code': 0, 'msg': 'ok', 'data': {
>>>  'symbol': 'EPIC-002_BTC-000', 
>>>  'tradingCurrency': 'EPIC-002', 
>>>  'quoteCurrency': 'BTC-000', ...}, }
```
- 📈 **TradingAPI** requires signature authentication by API Key and API Secret,
  which you can apply for on ViteX platform.
  Please note that API Key and API Secret are both case sensitive. 
  Also it is recommended to stake some VITE for QUOTA ('transactions fuel') 
  in order to execute multiple transactions. 
  

 
```
from vitexpy import TradingAPI

api_key = "YOUR VITEX API KEY"
api_secret = "YOUR VITEX API SECRET"

api = TradingAPI(api_key=user_key,
                 api_secret=user_secret,
                 print_response=True)

order_params = {
    'test': True,  # Optional, when True transactions are not executed in network
    'symbol': 'EPIC-002_BTC-000',  # Market pair symbol ('BASE-XXX_QUOTA-XXX')
    'amount': 5,  # Amount to buy or sell in base token ('EPIC-002' in this case)
    'price': 0.00006000,  # Price for each base token ('EPIC-002') in quota token ('BTC-000')
    'side': 1,  # Buy(0) or Sell(1)
    }
    

# If test=False this will place real sell order on EPIC/BTC market
api.place_order(**order_params)  


```
## 💌 Donations
Project is **open-source** and free, if you like it please consider donation:
- Vite Chain: vite_15d3230e3c31c009c968beea7160ae98b491475236ae2cddbc
- EPIC Chain: https://fastepic.eu/keybaseid_blacktyg3r
- WAN  Chain: 0x37b056F68120a250D28C7de9650Fa02Ee740fec1 
- BSC  Chain: 0xE6F431178cD7B44FBCb4381eBDb14Db213BDD866

Contact: [@blacktyg3r via Telegram](https://telegram.me/blacktyg3r)

**Thanks!**
