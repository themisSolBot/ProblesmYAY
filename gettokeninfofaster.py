import aiohttp  # For asynchronous HTTP requests
import logging  # For logging
import asyncio  # For handling asynchronous operations
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PriceInfo:
    def __init__(self, price, lp, liquidity, last_update_unix, last_update_human):
        self.price = price
        self.lp = lp
        self.liquidity = liquidity
        self.last_update_unix = last_update_unix
        self.last_update_human = last_update_human

    @staticmethod
    def from_json(json_data):
        if 'data' not in json_data:
            return None
        data = json_data['data']
        price = data['value']
        lp = data.get('lp', 'unknown')
        liquidity = data.get('liquidity', 'unknown')
        last_update_unix = data.get('updateUnixTime', 'unknown')
        last_update_human = data.get('updateHumanTime', 'unknown')
        return PriceInfo(price, lp, liquidity, last_update_unix, last_update_human)


def return_liquidity(token_address):
    token_info = get_token_info_pump(token_address)
    data = token_info.get('data', {})
    token = data.get('token', {})
    pool_info = token.get('pool_info', {})

    liquidity_sol = float(pool_info.get('quote_reserve', 0))
    return liquidity_sol


async def get_price_info(contract_address):
    url = f"https://public-api.birdeye.so/defi/price?include_liquidity=true&address={contract_address}"
    headers = {
        "accept": "application/json",
        "x-chain": "solana",
        "X-API-KEY": BIRDEYE_API_KEY
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                if 'data' in data:
                    return PriceInfo.from_json(data)
                else:
                    logger.error(f"Invalid response structure for {contract_address}: {data}")
            else:
                logger.error(f"Failed to fetch price info for {contract_address}: {response.status}")
    return None
  
async def get_helius(method, params):
    rpc = "https://mainnet.helius-rpc.com/?api-key=<API_KEY>&commitment=finalized"
    body = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params
    }
    headers = {
        "Content-Type": "application/json"
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(rpc, headers=headers, json=body) as response:
            if response.status == 200:
                return await response.json()
            else:
                logger.error(f"Failed to fetch helius data: {response.status}")
    return None




async def format_pair_info(data, price_info, contract_address, pool):
    if 'result' not in data or 'content' not in data['result']:
        return "No data found for the given contract address."
    print(price_info)
    print('------------')
    print(data)

    content = data['result']['content']
    meta = content['metadata']
    name = meta.get('name', 'unknown')
    symbol = meta.get('symbol', 'unknown')

    description = content.get('offChainMetadata', {}).get('metadata', {}).get('description', 'No description available')
    supply_formatted = str(float(data['result']['token_info']['supply'])/(10**float(data['result']['token_info']['decimals'])))

    exchange = pool.capitalize()

    if price_info is None:
        return "Error retrieving token price."

    token_price_in_dollars = price_info.price
    liquidity_sol = return_liquidity(str(contract_address)) #Diff API called to get liquidity as birdeye has incorrect result
    last_update_human = price_info.last_update_human


async def get_pair_info(contract_address, pool):
    try:
        helius_response = await get_helius("getAsset", {"id": contract_address})
        if helius_response is None or 'result' not in helius_response:
            return "Failed to fetch token info. Please try again later."

        price_info = await get_price_info(contract_address) #Birdeye only called here, if fails its on pump, hence problem is having to make two api calls for liquidity, could be one but birdeye result is wack
        formatted_response = await format_pair_info(helius_response, price_info, contract_address, pool)

        return formatted_response, helius_response, 'raydium', price_info
    except Exception as e:
        print(e)
        try:
            helius_response = await sync_to_async(get_token_info_pump)(contract_address)

            formatted_response = await format_pair_info_pump(helius_response, contract_address, pool)

            return formatted_response, helius_response, 'pump'
        except:
            return 'formatted_response', 'helius_response', 'not supported'
