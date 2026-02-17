import os
import requests
import pandas as pd
from datetime import datetime, timezone
from dotenv import load_dotenv
import logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

API_KEY = os.getenv("COINGECKO_API_KEY")

def get_session_with_retries():
    """
    Creates a requests session with automatic retry logic.
    Retries on: 429 (rate limit), 500, 502, 503, 504 (server errors)
    """
    session = requests.Session()
    retry_strategy = Retry(
        total=3,  # Try 3 times
        backoff_factor=2,  # Wait 2s, then 4s, then 8s between retries
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def validate_coin_data(coin):
    """
    Validates that coin data has required fields.
    Returns True if valid, False otherwise.
    """
    required_fields = ['symbol', 'name', 'current_price', 'total_volume', 
                       'market_cap', 'price_change_percentage_24h']
    
    for field in required_fields:
        if field not in coin or coin[field] is None:
            logger.warning(f"Missing or null field '{field}' for coin: {coin.get('id', 'unknown')}")
            return False
    return True

def fetch_crypto_data(top_n=50, coin_ids=None, timeout=15):
    """
    Fetches market data from CoinGecko with retry logic and validation.
    
    :param top_n: Number of top coins by market cap (default 50).
    :param coin_ids: Optional list of specific IDs (e.g., ['bitcoin', 'solana']).
    :param timeout: Request timeout in seconds (default 15).
    :return: DataFrame with crypto data or empty DataFrame on failure.
    """
    
    if not API_KEY:
        logger.error("COINGECKO_API_KEY not found in environment variables")
        return pd.DataFrame()
    
    url = "https://api.coingecko.com/api/v3/coins/markets"
    
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": min(top_n, 250),  # CoinGecko max is 250
        "page": 1,
        "sparkline": "false",
        "price_change_percentage": "24h",
        "x_cg_demo_api_key": API_KEY
    }
    
    if coin_ids:
        params["ids"] = ",".join(coin_ids)
        logger.info(f"Fetching specific coins: {coin_ids}")
    else:
        logger.info(f"Fetching top {top_n} coins by market cap")
    
    session = get_session_with_retries()
    
    try:
        response = session.get(url, params=params, timeout=timeout)
        response.raise_for_status()
        data = response.json()
        
        # Validate response
        if not isinstance(data, list):
            logger.error(f"Unexpected response format: {type(data)}")
            return pd.DataFrame()
        
        if len(data) == 0:
            logger.warning("API returned empty data list")
            return pd.DataFrame()
        
        logger.info(f"Successfully fetched {len(data)} coins from CoinGecko")
        
    except requests.exceptions.Timeout:
        logger.error(f"Request timed out after {timeout} seconds")
        return pd.DataFrame()
    
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            logger.error("Rate limit exceeded. Consider upgrading CoinGecko plan or reducing request frequency")
        else:
            logger.error(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
        return pd.DataFrame()
    
    except requests.exceptions.ConnectionError:
        logger.error("Failed to connect to CoinGecko API. Check your internet connection")
        return pd.DataFrame()
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {str(e)}")
        return pd.DataFrame()
    
    except Exception as e:
        logger.error(f"Unexpected error during API fetch: {str(e)}")
        return pd.DataFrame()
    
    # Process and validate data
    now = datetime.now(timezone.utc)
    rows = []
    skipped = 0
    
    for coin in data:
        if not validate_coin_data(coin):
            skipped += 1
            continue
        
        rows.append({
            "timestamp": now,
            "coin": coin.get("symbol", "UNKNOWN").upper(),
            "name": coin.get("name", "Unknown"),
            "price": float(coin.get("current_price", 0)),
            "volume_24h": float(coin.get("total_volume", 0)),
            "market_cap": float(coin.get("market_cap", 0)),
            "change_24h": float(coin.get("price_change_percentage_24h", 0))
        })
    
    if skipped > 0:
        logger.warning(f"Skipped {skipped} coins due to missing/invalid data")
    
    if len(rows) == 0:
        logger.error("No valid coin data after validation")
        return pd.DataFrame()
    
    df = pd.DataFrame(rows)
    
    # Ensure timestamp is ClickHouse-friendly (no timezone)
    df["timestamp"] = pd.to_datetime(df["timestamp"]).dt.tz_convert('UTC').dt.tz_localize(None)
    
    logger.info(f"Created DataFrame with {len(df)} valid rows")
    
    return df

if __name__ == "__main__":
    # Test fetching top 5 coins
    logger.info("--- Testing: Fetching Top 5 Coins ---")
    df = fetch_crypto_data(top_n=5)
    
    if not df.empty:
        print(df)
    else:
        print("Failed to fetch data")