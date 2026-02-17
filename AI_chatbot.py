import clickhouse_connect
import os
from dotenv import load_dotenv
from datetime import datetime

# Load credentials from .env
load_dotenv()

def get_clickhouse_client():
    """
    Uses the same logic as clickhouse_setup.py for consistency.
    """
    return clickhouse_connect.get_client(
        host=os.getenv("CLICKHOUSE_HOST", "localhost"),
        port=int(os.getenv("CLICKHOUSE_PORT", "8123")),
        username=os.getenv("CLICKHOUSE_USER", "default"),
        password=os.getenv("CLICKHOUSE_PASSWORD", "")
    )

def get_latest_crypto(client, coin_symbol):
    """
    Fetches latest data using SECURE parameterized queries.
    """
    # Use %s for parameterization to prevent SQL injection
    query = """
        SELECT timestamp, coin, name, price, volume_24h, market_cap, change_24h
        FROM crypto_prices
        WHERE coin = %s
        ORDER BY timestamp DESC
        LIMIT 1
    """
    
    # Pass parameters as a list/tuple
    result = client.query(query, parameters=[coin_symbol.upper()])
    
    if result.result_rows:
        # Zip column names with values to create a safe dictionary
        row_dict = dict(zip(result.column_names, result.result_rows[0]))
        return row_dict
    return None

def run_chatbot():
    try:
        client = get_clickhouse_client()
        print("💬 MrCrypto Chatbot ready! Type 'exit' to quit.\n")
        
        while True:
            user_input = input("You (Enter Symbol, e.g., BTC): ").strip()
            if user_input.lower() == "exit":
                print("Goodbye! 👋")
                break
            
            if not user_input:
                continue

            data = get_latest_crypto(client, user_input)
            
            if data:
                print("-" * 30)
                print(f"🪙  Asset: {data['name']} ({data['coin']})")
                print(f"💰 Price: ${data['price']:,.2f}")
                print(f"📊 24h Change: {data['change_24h']:.2f}%")
                print(f"💵 Market Cap: ${data['market_cap']:,.0f}")
                print(f"🔄 24h Volume: ${data['volume_24h']:,.0f}")
                print(f"⏰ Last Updated: {data['timestamp']}")
                print("-" * 30 + "\n")
            else:
                print(f"❌ No data found for symbol '{user_input.upper()}'. Is the pipeline running?\n")
                
    except Exception as e:
        print(f"⚠️ Connection Error: {e}")
    finally:
        if 'client' in locals():
            client.close()

if __name__ == "__main__":
    run_chatbot()