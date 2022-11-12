from notion_client import Client
from helpers import collect_paginated_api
from dotenv import load_dotenv
from os import environ
from yfinance import Ticker
from tqdm import tqdm
from requests import get

load_dotenv()

ASSETS_DATABASE_ID =  environ.get("ASSETS_DATABASE_ID")
OPERATIONS_DATABASE_ID =  environ.get("OPERATIONS_DATABASE_ID")
NOTION_API_KEY = environ.get("NOTION_API_KEY")
URL_API_TREASURE = environ.get("URL_API_TREASURE")


def update_assets_price_in_notion() -> None:
    with Client(auth=NOTION_API_KEY) as notion_client:
        assets = collect_paginated_api(notion_client.databases.query, database_id=ASSETS_DATABASE_ID)
        assets = [asset for asset in assets if asset["properties"]["atualizar automático"]["checkbox"] == True]
        stocks = [asset for asset in assets if type(asset["properties"]["tipo"]["select"]) is dict and asset["properties"]["tipo"]["select"].get('name') in ['ação', 'ETF', 'FIIS', 'BDR', 'cripto']]
        treasures = [asset for asset in assets if type(asset["properties"]["tipo"]["select"]) is dict and asset["properties"]["tipo"]["select"].get('name') in ['tesouro']]

        dolar_price = Ticker("BRL=X").info["previousClose"]
        for stock in tqdm(stocks):
            stock_code = stock["properties"]["code"]["rich_text"][0]["text"]["content"]
            stock_client = Ticker(stock_code)
            close_value = stock_client.info["previousClose"]
            currency = stock_client.info["currency"]
            close_value = close_value if currency != "USD" else  close_value * dolar_price
            notion_client.pages.update(stock["id"], properties={"ultimo fechamento": close_value})


        treasury_data = get(URL_API_TREASURE, verify=False).json()
        treasury_data = treasury_data["response"]["TrsrBdTradgList"]
        treasury_closes = {treasury_info["TrsrBd"]["cd"]: treasury_info["TrsrBd"]["untrRedVal"] for treasury_info in treasury_data}

        for treasury in tqdm(treasures):
            treasury_code = treasury["properties"]["code"]["rich_text"][0]["text"]["content"]
            treasury_code = int(treasury_code)
            close_value = treasury_closes[treasury_code]
            notion_client.pages.update(treasury["id"], properties={"ultimo fechamento": close_value})

update_assets_price_in_notion()