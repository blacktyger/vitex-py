"""PYTHON WRAPPER FOR VITEX.NET API v2"""

from collections import OrderedDict
from urllib.parse import urlencode
from typing import Union
from decimal import *
import hashlib
import time
import hmac

import requests

__version__ = '1.0.4'

"""
-----------------------------------------------------------------------
   vitex-py | `blacktyger
  donations | vite_15d3230e3c31c009c968beea7160ae98b491475236ae2cddbc
-----------------------------------------------------------------------

API DOCUMENTATION: https://vite.wiki/dex/api/dex-apis.html#overview 
DECENTRALIZED EXCHANGE: https://x.vite.net/
"""


class Token:
    """
    Base class to manage ViteX tokens as objects,
    Template for future subclasses with more abstraction build around

    :param id: _str, token ID, example: 'tti_f370fadb275bc2a1a839c753'
    :param symbol: _str, token symbol, example: 'EPIC-002'
    :param name: _str, token name, example: 'Epic Cash'
    :param meta: _dict, token details from ViteX API
    """

    def __init__(self, id: str,
                 symbol: str,
                 name: str = None,
                 meta: dict = None):
        self.id = id
        self.name = name
        self.meta = meta
        self.symbol = symbol

    def __repr__(self):
        return f"Token({self.symbol})"


class TradingPair:
    """
    Base class to manage ViteX trading pairs as objects,
    Template for future subclasses with more abstraction build around

    :param symbol: _str, trading pair symbol, example: 'EPIC-002_BTC-000'
    :param trading_token: Token object you buying, example EPIC-002
    :param quote_token: Token object you pay with, example BTC-000
    :param meta: _dict, token details from ViteX API
    """

    def __init__(self, symbol: str,
                 trading_token: Token = None,
                 quote_token: Token = None,
                 meta: dict = None):
        self.symbol = symbol
        self.trading_token = trading_token
        self.quote_token = quote_token
        self.meta = meta

    def __repr__(self):
        return f"TradingPair({self.symbol.replace('_', '/')})"


class HistoryOrder:
    """ Helping class to save and work with already executed in past orders fetched by API
    :param pair: TradingPair object
    :param meta: _dict, order details from ViteX API
    """
    def __init__(self, pair: Union[TradingPair, str],
                 meta: dict = None, network_response: dict = None):
        self.pair = pair
        self.meta = meta
        self.network_response = network_response

    def __repr__(self):
        return f"HistoryOrder({self.pair.symbol} | {self.meta['status'] if 'status' in self.meta.keys() else ''})"


class Order:
    """
    Base class to manage ViteX exchange orders as objects,
    Basic values handlers before creating object (like non negative numbers etc)
    template for future subclasses with more abstraction build around (tx status etc)

    :param pair: TradingPair object
    :param side: Tuple, (0, Buy) or (1, Sell)
    :param price: Decimal object, in quota token
    :param amount: Decimal object, in trading token
    :param meta: _dict, order details from ViteX API
    """

    def __init__(self,
                 pair: TradingPair, side: Union[str, int, float, bool] = None,
                 amount: Union[int, float, str, Decimal] = None,
                 price: Union[int, float, str, Decimal] = None,
                 meta: dict = None, signature: str = None,
                 network_response: dict = None):

        self.pair = pair
        self.side = side
        self.meta = meta
        self.price = price
        self.amount = amount
        self.decimals = Decimal(10) ** -8  # default value
        self.signature = signature
        self.network_response = network_response

        if self.pair.trading_token and self.pair.quote_token:
            self.trading_symbol = self._pair.trading_token.symbol
            self.quote_symbol = self._pair.quote_token.symbol
        else:
            self.trading_symbol = self._pair.symbol.split('_')[0]
            self.quote_symbol = self._pair.symbol.split('_')[1]

    def __iter__(self):
        # Calling dict(this_obj) will yield required
        # parameters for POST request to network (hacky)
        yield 'symbol', self.pair.symbol
        yield 'side', self.side[0]
        yield 'price', str(self.price)
        yield 'amount', str(self.amount)

    def __repr__(self):
        return f"Order({self._side[1].capitalize()} | " \
               f"{float(self.amount.quantize(self.decimals).normalize())} {self.trading_symbol} for " \
               f"{self.price.quantize(self.decimals).normalize()} {self.quote_symbol})"

    def get_params(self):
        return

    @property
    def pair(self):
        return self._pair

    @pair.setter
    def pair(self, value):
        # print(value)
        try:
            self._pair = value
        except Exception as e:
            print(e)
            raise ValueError(f"input [{value}] - wrong market/pair symbol or pattern ('BASE-XXX_QUOT-XXX')")

    @property
    def side(self):
        return self._side

    @side.setter
    def side(self, value):
        def stringfy(side):
            if side:
                return 'sell'
            else:
                return 'buy'

        # print(value)
        if isinstance(value, str):
            # print('str side')
            if any(value in x for x in ['buy', 'Buy', 'BUY', '0']):
                self._side = (0, stringfy(0))
            elif any(value in x for x in ['sell', 'Sell', 'SELL', '1']):
                self._side = (1, stringfy(1))

        elif isinstance(value, (int, float)):
            # print('int/float side')
            self._side = (int(value) if int(value) in [0, 1] else 1, stringfy(int(value)))

        elif isinstance(value, bool):
            # print('bool side')
            self._side = (int(bool is True), stringfy(int(bool is True)))

        else:
            raise ValueError(f"input [{value}] - can't parse this as side value")

    @property
    def amount(self):
        return self._amount

    @amount.setter
    def amount(self, value):
        try:
            value = Decimal(value)
            if value <= 0:
                raise ValueError(f"input [{value}] - value must be bigger than 0")

            self._amount = Decimal(value)
        except Exception as e:
            print(e)
            raise ValueError(f"input [{value}] can't be parsed as Decimal object")

    @property
    def price(self):
        return self._price

    @price.setter
    def price(self, value):
        try:
            value = Decimal(value)
            if value <= 0:
                raise ValueError(f"input [{value}] - value must be bigger than 0")

            self._price = Decimal(value)
        except Exception as e:
            print(e)
            raise ValueError(f"input [{value}] can't be parsed as Decimal object")


class PublicAPI:
    """
    This is BASE class for ViteX API classes with public market methods available for everyone.
    TradingAPI Subclass have access to trading methods where authorization and authentications is needed.
    """
    BASE_URL = "https://api.vitex.net"
    API_VERSION = 'ViteX API v2'
    ORDER_STATES = ["Unknown", "PendingRequest", "Received", "Open", "Filled", "PartiallyFilled", "PendingCancel",
                    "Cancelled", "PartiallyCancelled", "Failed", "Expired"]

    def __init__(self, print_response=False):
        """
        :param print_response: If True will print all API responses to stdout (for testing)
        """
        self.print_response = print_response
        self.api_version = self.API_VERSION
        self.base_url = self.BASE_URL

    def _response_parser(self, response: dict) -> Union[dict, list, int, float, str]:
        """Parse API responses"""
        if self.print_response:
            print(response)

        if isinstance(response, dict):
            if not response['code']:
                if response['data'] is not None:
                    return response['data']
                elif response['msg']:
                    return response['msg']
                else:
                    return response
            else:
                if 'The order status has been terminated' in response['msg']:
                    response['msg'] = f"Order already canceled"
                    return response
                else:
                    return response

    def get_order_limit(self) -> dict:
        """
        :return: Dictionary, pair with minimum order quantity

        RESPONSE: { 'minAmount': {'BTC-000': '0.0001', ...},
                    'depthStepsLimit': {'DUN-000_BTC-000': {'min': 5, 'max': 8}, ...}}}
        """
        url = self.base_url + "/api/v2/limit"
        json_response = requests.get(url).json()
        response = self._response_parser(json_response)
        return response

    @staticmethod
    def _create_order_object(response: Union[dict, list]) -> list:
        """
        Create Order object from response data
        :param response: order data
        :return: List, Order object/s
        """
        orders = []
        if isinstance(response, list):
            for order_ in response['order']:
                order = Order(pair=order_['symbol'],
                              side=order_['side'],
                              amount=order_['quantity'],
                              price=order_['price'],
                              meta=order_)
                orders.append(order)

        elif isinstance(response, dict):
            order = Order(pair=response['symbol'],
                          side=response['side'],
                          amount=response['quantity'],
                          price=response['price'],
                          meta=response)
            orders.append(order)

        return orders

    @staticmethod
    def _create_token_object(response: Union[dict, list]) -> list:
        """
        Create Token object from response data
        :param response: order data
        :return: List, Token object/s
        """

        tokens = []
        if isinstance(response, list):
            for token_ in response:
                token = Token(id=token_['tokenId'],
                              symbol=token_['symbol'])
                try:
                    token.name = token_['name']
                    token.meta = token_
                except KeyError:
                    pass

                tokens.append(token)

        elif isinstance(response, dict):
            token = Token(id=response['tokenId'],
                          symbol=response['symbol'])
            try:
                token.name = response['name']
                token.meta = response
            except Exception as e:
                print(f"_create_token_object: {e}")
            tokens.append(token)

        return tokens

    @staticmethod
    def _create_pair_object(response: Union[dict, list]) -> list:
        """
        Create TradingPair object from response data
        :param response: order data
        :return: List, TradingPair object/s
        """

        pairs = []
        if isinstance(response, list):
            for pair_ in response:
                pair = TradingPair(symbol=pair_['symbol'], meta=pair_)
                pairs.append(pair)

        elif isinstance(response, dict):
            pair = TradingPair(symbol=response['symbol'], meta=response)
            pairs.append(pair)

        return pairs

    def get_all_tokens(self, **kwargs) -> list:
        """
        :param category: String, Token category, [ quote , all ], default all
        :param tokenSymbolLike: String, Token symbol. For example EPIC-002 | Fuzzy search supported.
        :param offset: Int, Search starting index, starts at 0 , default 0
        :param limit: Int, Search limit, max 500 , default 500
        :return: List, all registered tokens

        RESPONSE: [{'tokenId': 'tti_30831c79099bbe5af0b037b1',
                    'name': 'AAVO',
                    'symbol': 'AAVO-000',
                    'originalSymbol': 'AAVO',
                    'totalSupply': '1123581321000000000000000000',
                    'owner': 'vite_6137c4252bd057c65dd31024ac9ed7e484d736545ffa57d85d',
                    'tokenDecimals': 18,
                    'urlIcon': 'https://....png'}, ...]
        """
        url = self.base_url + "/api/v2/tokens"
        json_response = requests.get(url, kwargs).json()
        response = self._response_parser(json_response)
        return self._create_token_object(response)

    def get_token(self, tokenSymbol=None, tokenId=None, **kwargs) -> list:
        """
        :param tokenSymbol: Token symbol. For example EPIC-002
        :param tokenId: Token id. For example, tti_5649544520544f4b454e6e40
        :return: List, Token object

        RESPONSE: { 'tokenId': 'tti_f370fadb275bc2a1a839c753',
                    'name': 'Epic Cash',
                    'symbol': 'EPIC-002',
                    'originalSymbol': 'EPIC',
                    'totalSupply': '890000000000000',
                    'publisher': 'vite_721a68f6ebd764e3f932832a05d87f8b1e8428393a0025bc72',
                    'tokenDecimals': 8,
                    'tokenAccuracy': '0.00000001',
                    'publisherDate': None,
                    'reissue': 1, 'urlIcon': 'https://...png',
                    'gateway': {'name': 'VGATE', 'icon': 'https://....png',
                    'policy': {'en': 'https://vgate.io/clause'},
                    'overview': {'en': "As an operator of ViteX...."},
                    'links': {'website': ['https://vgate.io/'],
                    'email': ['vgateservice@gmail.com']},
                    'support': 'vgateservice@gmail.com',
                    'serviceSupport': 'https://vgate.zendesk.com/hc/en-us/requests/new',
                    'isOfficial': True,
                    'level': 2, 'website': 'https://vgate.io/',
                    'mappedToken': {'symbol': 'EPIC', 'name': None, 'tokenCode': '1461', 'platform': 'EPIC',
                                    'tokenAddress': None, 'standard': '', 'tokenIndex': None,
                                    'url': 'https://gateway.vgate.io/gateway/epic',  'icon': 'https://....png',
                                    'decimal': 8, 'mappedTokenExtras': None},
                    'url': 'https://gateway.vgate.io/gateway/epic'},
                    'links': {'website': ['https://epic.tech/'], 'twitter': ['https://twitter.com/EpicCashTech'],
                              'discord': ['https://discordapp.com/invite/ZjnC6bh'],
                              'explorer': ['https://explorer.epic.tech/'],
                              'reddit': ['https://www.reddit.com/r/epiccash/'],
                              'telegram': [' https://t.me/EpicCashAnn']},
                    'overview': {'en': 'Epic is designed to be a currency for everyone, ....'}
        """
        url = self.base_url + "/api/v2/token/detail"

        # A little parsing tricks to make calls more convenient
        # Finding '-' in either params assumes it's tokenSymbol, else tokenId
        if any('-' in x for x in [tokenSymbol, tokenId] if x is not None):
            params = {**{'tokenSymbol': tokenSymbol if tokenSymbol else tokenId}, **kwargs}
        else:
            params = {**{'tokenId': tokenId if tokenId else tokenSymbol}, **kwargs}

        json_response = requests.get(url, params).json()
        response = self._response_parser(json_response)

        if 'data' in response.keys() and 'ok' in response['msg']:
            response['msg'] = f'found token [{tokenSymbol if tokenSymbol else tokenId}] but no data present'
            return response
        else:
            return self._create_token_object(response)

    def get_listed_tokens(self, quoteTokenSymbol=None) -> list:
        """
        :param quoteTokenSymbol: REQUIRED! Quote token symbol. For example EPIC-002
        :return: List, Token objects that are already listed in specific market

        RESPONSE: [{'tokenId': 'tti_687d8a93915393b219212c73', 'symbol': 'ETH-000'}, ...]
        """
        url = self.base_url + "/api/v2/token/mapped"
        params = {'quoteTokenSymbol': quoteTokenSymbol}
        json_response = requests.get(url, params).json()
        response = self._response_parser(json_response)
        return self._create_token_object(response)

    def get_unlisted_tokens(self, quoteTokenSymbol=None) -> list:
        """
        :param quoteTokenSymbol: REQUIRED! Quote token symbol. For example EPIC-002
        :return: List tokens that are not yet listed in specific market

        RESPONSE: [{'tokenId': 'tti_687d8a93915393b219212c73', 'symbol': 'ETH-000'}, ...]
        """
        url = self.base_url + "/api/v2/token/unmapped"
        params = {'quoteTokenSymbol': quoteTokenSymbol}
        json_response = requests.get(url, params).json()
        response = self._response_parser(json_response)
        return self._create_token_object(response)

    def get_trading_pair(self, symbol=None) -> list:
        """
        :param symbol: REQUIRED! Trading pair name. For example EPIC-002_BTC-000
        :return: List, TradingPair object/s in detail

        RESPONSE:  {'symbol': 'EPIC-002_BTC-000',
                    'tradingCurrency': 'EPIC-002',
                    'quoteCurrency': 'BTC-000',
                    'tradingCurrencyId': 'tti_f370fadb275bc2a1a839c753',
                    'quoteCurrencyId': 'tti_b90c9baffffc9dae58d1f33f',
                    'tradingCurrencyName': 'Epic Cash',
                    'quoteCurrencyName': 'Bitcoin',
                    'operator': 'vite_721a68f6ebd764e3f932832a05d87f8b1e8428393a0025bc72',
                    'operatorName': 'VGATE',
                    'operatorLogo': 'https://...png',
                    'pricePrecision': 8,
                    'amountPrecision': 8,
                    'minOrderSize': '0.0001',
                    'operatorMakerFee': 0.002,
                    'operatorTakerFee': 0.002,
                    'highPrice': '0.00004100',
                    'lowPrice': '0.00002500',
                    'lastPrice': '0.00003733',
                    'volume': '275000.40511192',
                    'baseVolume': '8.99756407',
                    'bidPrice': '0.00003600',
                    'askPrice': '0.00004088',
                    'openBuyOrders': 110,
                    'openSellOrders': 82}
        """
        url = self.base_url + "/api/v2/market"
        params = {'symbol': symbol}
        json_response = requests.get(url, params).json()
        response = self._response_parser(json_response)
        return self._create_pair_object(response)

    def get_all_trading_pairs(self, **kwargs) -> list:
        """
        :param offset: Search starting index, starts at 0 , default 0
        :param limit: Search limit, max 500 , default 500
        :return: List, all TradingPair objects

        RESPONSE: [{'symbol': 'AAVO-000_VITE',
                    'tradeTokenSymbol': 'AAVO-000',
                    'quoteTokenSymbol': 'VITE',
                    'tradeToken': 'tti_30831c79099bbe5af0b037b1',
                    'quoteToken': 'tti_5649544520544f4b454e6e40',
                    'pricePrecision': 8,
                    'quantityPrecision': 8}, ...]
        """
        url = self.base_url + "/api/v2/markets"
        json_response = requests.get(url, kwargs).json()
        response = self._response_parser(json_response)
        return self._create_pair_object(response)

    def get_order(self, address=None, orderId=None) -> list:
        """
        :param address: REQUIRED! User's account address (not delegation address)
        :param orderId: REQUIRED! Order id
        :return: List, single Order object

        RESPONSE:{'address': 'vite_15d3230e3c31c009c968beea7160ae98b491475236ae2cddbc',
                  'orderId': 'bba7552f0ef4aefef95e741a63ed11f66e62a33009e7adda5db0ab285ac59801',
                  'symbol': 'EPIC-002_BTC-000',
                  'tradeTokenSymbol': 'EPIC-002',
                  'quoteTokenSymbol': 'BTC-000',
                  'tradeToken': 'tti_f370fadb275bc2a1a839c753',
                  'quoteToken': 'tti_b90c9baffffc9dae58d1f33f',
                  'side': 1,
                  'price': '0.00003999',
                  'quantity': '9.00000000',
                  'amount': '0.00035991',
                  'executedQuantity': '9.00000000',
                  'executedAmount': '0.00035991',
                  'executedPercent': '1.00000000',
                  'executedAvgPrice': '0.00003999',
                  'fee': '0.00000130',
                  'status': 4, 'type': 0,
                  'createTime': 1635343678},
                  ...]}
        """
        url = self.base_url + "/api/v2/order"
        params = {'address': address, 'orderId': orderId}
        json_response = requests.get(url, params).json()
        response = self._response_parser(json_response)
        return self._create_order_object(response)

    def get_orders(self, address=None, **kwargs) -> list:
        """
        :param address: REQUIRED! User's account address (not delegation address)
        :param symbol: Trading pair name. For example, EPIC-002_BTC-000
        :param quoteTokenSymbol: Quote token symbol. For example, EPIC-002
        :param side: Trade token symbol. For example, EPIC-002
        :param tradeTokenSymbol: Start time (s)
        :param startTime: End time (s)
        :param endTime: Order side. 0 - buy, 1 - sell
        :param status:Order status, valid in [ 0-10 ]. 3 , 5 - returns orders t
                      hat are unfilled or partially filled; 7 , 8 - returns orders
                      that are cancelled or partially cancelled
        :param offset: Search starting index, starts at 0 , default 0
        :param limit: Search limit, default 30 , max 100
        :param total: Include total number searched in result? 0 - not included, 1 - included.
                      Default is 0 , in this case total=-1 in response
        :return: List, Order objects

        RESPONSE: {'order': [{'address': 'vite_15d3230e3c31c009c968beea7160ae98b491475236ae2cddbc',
                              'orderId': 'bba7552f0ef4aefef95e741a63ed11f66e62a33009e7adda5db0ab285ac59801',
                              'symbol': 'EPIC-002_BTC-000',
                              'tradeTokenSymbol': 'EPIC-002',
                              'quoteTokenSymbol': 'BTC-000',
                              'tradeToken': 'tti_f370fadb275bc2a1a839c753',
                              'quoteToken': 'tti_b90c9baffffc9dae58d1f33f',
                              'side': 1,
                              'price': '0.00003999',
                              'quantity': '9.00000000',
                              'amount': '0.00035991',
                              'executedQuantity': '9.00000000',
                              'executedAmount': '0.00035991',
                              'executedPercent': '1.00000000',
                              'executedAvgPrice': '0.00003999',
                              'fee': '0.00000130',
                              'status': 4, 'type': 0,
                              'createTime': 1635343678},
                              ...]}
        """
        url = self.base_url + "/api/v2/orders"
        params = {**{'address': address}, **kwargs}
        json_response = requests.get(url, params).json()
        response = self._response_parser(json_response)
        return self._create_order_object(response)

    def get_24hr_ticker_price_changes(self, quoteTokenSymbol=None) -> list:
        """
        :param quoteTokenSymbol: Quote token symbol. For example, EPIC-002 . Returns all pairs if not present
        :return: List, tickers for last 24h

        RESPONSE: [{'symbol': 'PGOLD-001_BTC-000',
                    'tradeTokenSymbol': 'PGOLD-001',
                    'quoteTokenSymbol': 'BTC-000',
                    'tradeToken': 'tti_3cc6dddfb53f3cc5fbb4e7a4',
                    'quoteToken': 'tti_b90c9baffffc9dae58d1f33f',
                    'openPrice': '0.00000000',
                    'prevClosePrice': '0.00000000',
                    'closePrice': '0.00000000',
                    'priceChange': '0.00000000',
                    'priceChangePercent': 0.0,
                    'highPrice': '0.00000000',
                    'lowPrice': '0.00000000',
                    'quantity': '0.00000000',
                    'amount': '0.00000000',
                    'pricePrecision': 8,
                    'quantityPrecision': 2,
                    'openTime': None,
                    'closeTime': None},
                    ...]
        """
        url = self.base_url + "/api/v2/ticker/24hr"
        params = {'quoteTokenSymbol': quoteTokenSymbol}
        json_response = requests.get(url, params).json()
        response = self._response_parser(json_response)
        return response

    def get_order_book_ticker(self, symbol=None) -> dict:
        """
        :param symbol: REQUIRED! Trading pair name. For example, EPIC-002_BTC-000
        :return: Dictionary, current best price/qty on the order book for a trading pair

        RESPONSE: {'symbol': 'EPIC-002_BTC-000',
                   'bidPrice': '0.00003600',
                   'bidQuantity': '572.58383134',
                   'askPrice': '0.00003733',
                   'askQuantity': '56.37728146',
                   'height': None}
        """
        url = self.base_url + "/api/v2/ticker/bookTicker"
        params = {'symbol': symbol}
        json_response = requests.get(url, params).json()
        response = self._response_parser(json_response)
        return response

    def get_trade_history(self, symbol=None, **kwargs) -> list:
        """
        :param symbol: REQUIRED! Trading pair name. For example. EPIC-002_BTC-000
        :param limit: Search limit, default 500
        :return: List, trades history on given pair

        RESPONSE: [{'timestamp': 1635355988000,
                    'price': '0.00003733',
                    'amount': '500.00000000',
                    'side': 0}, ...]
        """
        url = self.base_url + "/api/v2/trades"
        params = {**{'symbol': symbol}, **kwargs}
        json_response = requests.get(url, params).json()
        response = self._response_parser(json_response)
        return response

    def get_detailed_trade_history(self, symbol=None, **kwargs) -> dict:
        """
        :param symbol: REQUIRED! Trading pair name. For example, EPIC-002_BTC-000
        :param orderId: Order id
        :param startTime: Start time (s)
        :param endTime: End time (s)
        :param side: Order side. 0 - buy, 1 - sell
        :param offset: Search starting index, starts at 0 , default 0
        :param limit: Search limit, default 30 , max 100
        :param total: Include total number searched in result? 0 - not included,
                      1 - included. Default is 0 , in this case total=-1 in response
        :return: List, detailed trades history on given pair

        RESPONSE: {'height': None,
                   'trade': [{'tradeId': '29b58e69079295499f5c815db002f29111cfb55d',
                              'symbol': 'EPIC-002_BTC-000',
                              'tradeTokenSymbol': 'EPIC-002',
                              'quoteTokenSymbol': 'BTC-000',
                              'tradeToken': 'tti_f370fadb275bc2a1a839c753',
                              'quoteToken': 'tti_b90c9baffffc9dae58d1f33f',
                              'price': '0.00003733',
                              'quantity': '128.54395437',
                              'amount': '0.00479854',
                              'time': 1635355704,
                              'side': 1,
                              'buyFee': '0.00001728',
                              'sellFee': '0.00001919',
                              'blockHeight': 48313111},
                              ...]}
        """
        url = self.base_url + "/api/v2/trades/all"
        params = {**{'symbol': symbol}, **kwargs}
        json_response = requests.get(url, params).json()
        response = self._response_parser(json_response)
        return response

    def get_order_book_depth(self, symbol=None, **kwargs) -> dict:
        """
        :param symbol:  REQUIRED! Trading pair name. For example, EPIC-002_BTC-000
        :param limit: Search limit, max 100 , default 100
        :param precision: Price Precision
        :return: Dictionary, bid and ask lists

        RESPONSE: {'timestamp': 1635355653689,
                   'asks': [['0.00004088', '55.53242804'], ...],
                   'bids': [[...], ...]}
        """
        url = self.base_url + "/api/v2/depth"
        params = {**{'symbol': symbol}, **kwargs}
        json_response = requests.get(url, params).json()
        response = self._response_parser(json_response)
        return response

    def get_candlestick_bars(self, symbol=None, interval=None, **kwargs) -> dict:
        """
        :param symbol: REQUIRED! Trading pair name. For example, GRIN-000_VITE
        :param interval: REQUIRED! Interval, [ minute , hour , day , minute30 , hour6 , hour12 , week ]
        :param limit: Search limit, max 1500 , default 500
        :param startTime: Start time (s)
        :param endTime: End time (s)
        :return: Dictionary, candles

        RESPONSE {"t": [1554207060],
                  "c": [1.0],
                  "p": [1.0],
                  "h": [1.0],
                  "l": [1.0],
                  "v": [12970.8]}
        """
        url = self.base_url + "/api/v2/klines"
        params = {**{'symbol': symbol, 'interval': interval}, **kwargs}
        json_response = requests.get(url, params).json()
        response = self._response_parser(json_response)
        return response

    def get_deposit_withdrawal_records(self, address=None, tokenId=None, **kwargs) -> dict:
        """
        :param address: REQUIRED! Account address
        :param tokenId: REQUIRED! Token id. For example tti_f370fadb275bc2a1a839c753
        :param offset:Search starting index, starts at 0 , default 0
        :param limit: Search limit, max 100 , default 100
        :return: Dictionary, withdraw from exchange transactions list

        RESPONSE {'time': 1635252570,
                  'tokenSymbol': 'EPIC',
                  'amount': '10.00000000',
                  'type': 2}
        """
        url = self.base_url + "/api/v2/deposit-withdraw"
        params = {**{'address': address, 'tokenId': tokenId}, **kwargs}
        json_response = requests.get(url, params).json()
        response = self._response_parser(json_response)
        return response

    def get_currency_price(self, tokenSymbols=None, **kwargs) -> dict:
        """
        :param tokenSymbols: Trading pairs, split by ",". For example BTC-000,EPIC-002
        :param tokenIds:Token ids, split by ",".
        :return: List of token/s rates in other currencies

        RESPONSE: {'tokenId': 'tti_f370fadb275bc2a1a839c753',
                   'tokenSymbol': 'EPIC-002',
                   'usdRate': 2.36, ...}
        """
        url = self.base_url + "/api/v2/exchange-rate"
        params = {**{'tokenSymbols': tokenSymbols}, **kwargs}
        json_response = requests.get(url, params).json()
        response = self._response_parser(json_response)
        return response

    def get_account_exchange_balance(self, address=None) -> dict:
        """
        :param address: Account address
        :return: Dictionary, balances of exchange wallet for given account address

        RESPONSE: {'EPIC-002': {'available': '3682.95575597',
                                'locked': '0.00000000'}, ...}
        """
        url = self.base_url + "/api/v2/balance"
        params = {'address': address}
        json_response = requests.get(url, params).json()
        response = self._response_parser(json_response)
        return response

    def get_trade_mining_info(self) -> dict:
        """
        :return: Dictionary, current cycle's trade mining pool size and real-time fees accumulated

        RESPONSE: {'tradePoolVx': {'1': '2386.387391592278053218', '2': '2386.387391592278053218',
                   '3': '2386.387391592278053218', '4': '2386.387391592278053218'},
                   'tradePoolFee': {'1': '4865.323236794250000000', '2': '0.118197284244750000',
                   '3': '0.00794865', '4': '490.970596'}}
        """
        url = self.base_url + "/api/v2/trade_fee_info"
        json_response = requests.get(url).json()
        response = self._response_parser(json_response)
        return response

    def get_server_time(self) -> int:
        """
        :return: Int, Vitex server timestamp, need for making transactions signatures
        """

        url = self.base_url + "/api/v2/time"
        json_response = requests.get(url).json()
        response = self._response_parser(json_response)
        return int(response)

    def get_usd_cny_rate(self) -> float:
        """
        :return: Float, USD CNY rate
        """
        url = self.base_url + "/api/v2/usd-cny"
        json_response = requests.get(url).json()
        response = self._response_parser(json_response)
        return float(response)

    def test_connection(self):
        import datetime
        try:
            ts = self.get_server_time()
            dt = datetime.datetime.utcfromtimestamp(ts / 1000)
        except Exception:
            dt = False

        try:
            t2 = f"{self.get_usd_cny_rate()}"
        except Exception:
            t2 = False

        if dt or t2:
            print(f"✅ Successfully connected to ViteX API with vitex-py module\n"
                  f"Server time: {f'{dt} (from vitex.net server)' if dt else 'ERROR'}\n"
                  f"USD  /  CNY: {f'{t2} (from vitex.net server)' if t2 else 'ERROR'}")


class TradingAPI(PublicAPI):
    """
    Private trading API endpoints to manage trading with ViteX API keys.
    https://vitex.zendesk.com/hc/en-001/articles/360046948154-How-to-Create-API-on-ViteX-

    Private API requires signature authentication by API Key and API Secret,
    which you can apply for on ViteX platform.
    Please note that API Key and API Secret are both case sensitive.

    Besides parameters defined by specific API methods 3 additional parameters:
    key, timestamp and signature should also be included.

    timestamp - UNIX timestamp in milliseconds. To avoid replay attack,
    API request will be rejected if the timestamp in request is 5,000 ms earlier
    or 1,000 ms later than standard time.
    """

    ORDER_STATES = ["Unknown", "PendingRequest", "Received", "Open", "Filled", "PartiallyFilled",
                    "PendingCancel", "Cancelled", "PartiallyCancelled", "Failed", "Expired"]

    def __init__(self, api_key=None, api_secret=None, **kwargs):
        """
        :param key: ViteX API Key
        :param api_secret: ViteX API Key secret
        """
        super().__init__(**kwargs)
        self.api_key = api_key
        self.api_secret = api_secret

    @staticmethod
    def _alphabetically_ordered(_dict: dict) -> OrderedDict:
        """
        :param _dict: request parameters
        :return: Dictionary, alphabetically ordered parameters
        """
        return OrderedDict(sorted(_dict.items(), key=lambda t: t[0]))

    def _sign_transaction(self, sorted_params: dict) -> str:
        """
        :param sorted_params: Dictionary, alphabetically ordered params used
                              to create unique transaction signature
        :return: String, unique transaction signature used for API POST requests
        """
        try:
            encoded_params = urlencode(sorted_params)
            signature = hmac.new(self.api_secret.encode("utf8"),
                                 encoded_params.encode("utf8"),
                                 hashlib.sha256)
            signature_str = signature.hexdigest()
            return signature_str
        except Exception as e:
            print(f"_sign_transaction: {e}")
            return ''

    def _prepare_signature(self, params: dict) -> dict:
        """ Prepare given parameters and add auth_params needed in every transaction
        :param timestamp - Int, Timestamp (s)
        :param key - String,  API Key
        :param signature - String, HMAC SHA256 signature of request String

        Signature of Request String:
        - List all parameters (including key and timestamp ) in alphabet order;
        - Generate request String by concatenating parameters with = and & in above order;
        - Sign the request String by HMAC SHA256, using API Secret as secret key.
          If request String and request body are both present, put request String
          in ahead of request body
        - Signature is case in-sensitive;
        - Attach the signature to request String in signature field
        :return: Dictionary, ready to POST request params
        """

        # In case of temporary connection issue try again after 1s
        try:
            auth_params = {"key": self.api_key, "timestamp": self.get_server_time()}
        except Exception as e:
            print(f"_prepare_signature: {e}")
            time.sleep(1)
            auth_params = {"key": self.api_key, "timestamp": self.get_server_time()}

        if params is not None:
            auth_params.update(params)

        sorted_params = self._alphabetically_ordered(auth_params)
        signature = self._sign_transaction(sorted_params)
        sorted_params["signature"] = signature

        return sorted_params

    def _prepare_decimals(self, params: dict) -> dict:
        """
        Find decimal places for pair tokens and convert number values to Decimal objects
        :param params: Dictionary, order POST request params
        :return: Dictionary, prepared order POST requests params
        """
        # Check if expected values are not None
        if not params['amount'] or not params['price']:
            return params

        # Set 8 decimal places as default (0.00000000)
        amount_decimals = price_decimals = Decimal(10) ** -8

        try:
            # From API try to get number of decimal places for both tokens
            details = self.get_trading_pair(params['pair'].symbol)[0]
            amount_decimals = Decimal(10) ** -(details.meta['amountPrecision'])
            price_decimals = Decimal(10) ** -(details.meta['pricePrecision'])
        except Exception as e:
            print(f"_prepare_decimals: {e}")

        # Convert values to Decimal and set correct decimal places
        try:
            params['amount'] = str(Decimal(params['amount']).quantize(amount_decimals))
            params['price'] = str(Decimal(params['price']).quantize(price_decimals))
        except Exception as e:
            print(f"_prepare_decimals: {e}")

        return params

    def prepare_order(self, pair: Union[str, TradingPair] = None,
                      amount: Union[int, float, str, Decimal] = None,
                      price: Union[int, float, str, Decimal] = None,
                      side: Union[str, int, float, bool] = None) -> Order:

        """ Take parameters and prepare Order object ready to sign and execute

        :param pair: TradingPair object or string with pair symbol, for example 'EPIC-002_BTC-000'
        :param amount: Order amount (in trade token)
        :param price: Order price (in quote token)
        :param side: Buy - 0 , Sell - 1
        :return: Order object
        """

        if isinstance(pair, str):
            pair = TradingPair(symbol=pair)

        params = {'pair': pair, 'amount': amount,
                  'price': price, 'side': side}

        if None in params.values():
            raise ValueError(f'Each value from [{", ".join(str(x) for x in params.keys())}] '
                             f'must be provided')

        order = Order(**self._prepare_decimals(params))
        return order

    def execute_order(self, order: Order, test: bool = False) -> Order:
        """
        :param order: Order object, prepared and ready to execute
        :param test: _bool, if true do not execute order in network
        :return: Order object with updated network_response argument
        """
        if test:
            url = self.base_url + "/api/v2/order/test"
        else:
            url = self.base_url + "/api/v2/order"

        order.signature = self._prepare_signature(dict(order))
        json_response = requests.post(url, order.signature).json()
        response = self._response_parser(json_response)
        res = order.network_response = response

        if not test:
            # Print success report or handle order error
            if 'status' in res.keys():

                # Translate status number to human readable message
                readable_status = self.ORDER_STATES[res['status']]
                order.network_response['status'] = readable_status

                print(f'-----------------------------------------\n'
                      f"✅ Successfully executed!\n"
                      f"{order}\n"
                      f"ID: {res['orderId']}\n"
                      f"STATUS: {res['status']}\n"
                      f"-----------------------------------------")

            elif 'msg' in res.keys():
                if 'out of quota' in res['msg']:
                    print(f"Not enough QUOTA to execute this order")
                else:
                    print(res['msg'])
        else:
            print(f'-----------------------------------------\n'
                  f"Test order executed\n"
                  f"{order}\n"
                  f"NETWORK RESPONSE: {res}\n"
                  f"-----------------------------------------")

        return order

    def cancel_order(self, order: Union[Order, HistoryOrder] = None, id: str = None,
                     pair: Union[TradingPair, str] = None) -> list:
        """
        :param id: _str, Vitex network order ID (order must be already executed)
        :param pair: TradingPair object or string with pair symbol, for example 'EPIC-002_BTC-000'
        :param order: Order object to cancel
        :return: _list, Order object
        """

        url = self.base_url + "/api/v2/order"

        if not isinstance(pair, TradingPair):
            pair = TradingPair(symbol=pair)

        if not order:
            order = HistoryOrder(pair=pair, meta={'orderId': id})

        params = {'symbol': order.pair.symbol,
                  'orderId': order.meta['orderId']}

        signature = self._prepare_signature(params)
        json_response = requests.delete(url, data=signature).json()
        response = self._response_parser(json_response)

        order.network_response = response
        return [order]

    def cancel_all_orders(self, pair: Union[TradingPair, str] = None) -> list:
        """
        :param pair: TradingPair object or string with pair symbol, for example 'EPIC-002_BTC-000'
        :return: List, Order object/s

        RESPONSE:  [{"symbol": "VX_ETH-000",
                      "orderId": "de185edae25a60dff421c1be23ac298b121cb8bebeff2ecb25807ce7d72cf622",
                      "cancelRequest": "355b6fab007d86e7ff09b0793fbb205e82d3880b64d948ed46f88237115349ab",
                      "status": 6
                    }, ...]
        """

        url = self.base_url + "/api/v2/orders"

        if not isinstance(pair, TradingPair):
            pair = TradingPair(symbol=pair)

        signature = self._prepare_signature({'symbol': pair.symbol})
        json_response = requests.delete(url, data=signature).json()
        response = self._response_parser(json_response)

        canceled_orders = []
        if response and isinstance(response, list):
            for order_ in response:
                pair = TradingPair(symbol=order_['symbol'])

                # Translate status number to human readable message
                readable_status = self.ORDER_STATES[order_['status']]
                order_['status'] = readable_status
                canceled_orders.append(HistoryOrder(pair=pair, meta=order_))

            return canceled_orders

        else:
            if isinstance(response, dict) and 'msg' in response.keys():
                print(response['msg'])






















