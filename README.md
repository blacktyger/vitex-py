## PYTHON WRAPPER FOR VITEX.NET API v2

###### vitex-py by `blacktyger

## Installation:
<code>python -m pip install vitexpy</code>

## Description:
Python wrapper for ViteX - Decentralized cryptocurrency exchange API.

- URL: https://x.vite.net/
- API DOCUMENTATION: https://vite.wiki/dex/api/dex-apis.html#overview

## How to use:
- PublicAPI can be used out of the box without API keys


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
- TradingAPI requires signature authentication by API Key and API Secret,
  which you can apply for on ViteX platform.
  Please note that API Key and API Secret are both case sensitive.
  
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
    
api.place_order(**order_params)



```