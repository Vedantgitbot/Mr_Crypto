import clickhouse_connect

import sys

import os

import logging

from dotenv import load_dotenv



# Setup logging

logging.basicConfig(

    level=logging.INFO,

    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'

)

logger = logging.getLogger(__name__)



# Allow import from API folder

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from API.fetch_api import fetch_crypto_data



load_dotenv()



def get_clickhouse_client():

    """

    Creates ClickHouse client with credentials from environment.

    Falls back to localhost defaults if not set.

    """

    host = os.getenv("CLICKHOUSE_HOST", "localhost")

    port = int(os.getenv("CLICKHOUSE_PORT", "8123"))

    username = os.getenv("CLICKHOUSE_USER", "default")

    password = os.getenv("CLICKHOUSE_PASSWORD", "")

    

    try:

        client = clickhouse_connect.get_client(

            host=host,

            port=port,

            username=username,

            password=password,

            connect_timeout=10,

            send_receive_timeout=30

        )

        

        # Test connection

        client.command("SELECT 1")

        logger.info(f"✅ Connected to ClickHouse at {host}:{port}")

        return client

        

    except Exception as e:

        logger.error(f"Failed to connect to ClickHouse: {e}")

        raise



def setup_table(client):

    """

    Creates the table with optimized settings for time-series crypto data.

    Added 'name' column and LowCardinality optimization for symbols.

    """

    try:

        # 1. Create table with modern schema

        query = """

        CREATE TABLE IF NOT EXISTS crypto_prices (

            timestamp DateTime,

            coin LowCardinality(String),

            name String,

            price Float64,

            volume_24h Float64,

            market_cap Float64,

            change_24h Float64

        )

        ENGINE = MergeTree()

        PARTITION BY toYYYYMM(timestamp)

        ORDER BY (coin, timestamp)

        SETTINGS index_granularity = 8192

        """

        client.command(query)

        logger.info("Table 'crypto_prices' verified/created")

        

        # 2. Schema Evolution: If 'name' column doesn't exist, add it

        client.command("ALTER TABLE crypto_prices ADD COLUMN IF NOT EXISTS name String AFTER coin")

        logger.info("Table schema is up to date")

        

    except Exception as e:

        logger.error(f"Failed to setup table: {e}")

        raise



def validate_dataframe(df):

    """

    Validates DataFrame has required columns and correct types.

    """

    required_columns = ["timestamp", "coin", "name", "price", "volume_24h", "market_cap", "change_24h"]

    

    missing_columns = [col for col in required_columns if col not in df.columns]

    if missing_columns:

        raise ValueError(f"DataFrame missing required columns: {missing_columns}")

    

    # Check for nulls in critical columns

    critical_columns = ["timestamp", "coin", "price"]

    for col in critical_columns:

        null_count = df[col].isnull().sum()

        if null_count > 0:

            raise ValueError(f"Column '{col}' has {null_count} null values")

    

    logger.info(f"DataFrame validation passed: {len(df)} rows, {len(df.columns)} columns")



def insert_data(client, df):

    """

    Inserts validated data into ClickHouse.

    """

    if df.empty:

        logger.warning("No data to insert - DataFrame is empty")

        return 0

    

    try:

        # Validate before inserting

        validate_dataframe(df)

        

        columns = ["timestamp", "coin", "name", "price", "volume_24h", "market_cap", "change_24h"]

        

        # Convert to list for ClickHouse insert

        data_to_insert = df[columns].values.tolist()

        

        client.insert(

            "crypto_prices",

            data_to_insert,

            column_names=columns

        )

        

        logger.info(f"✅ Successfully inserted {len(df)} rows into ClickHouse")

        return len(df)

        

    except ValueError as e:

        logger.error(f"Data validation failed: {e}")

        raise

    except Exception as e:

        logger.error(f"Insert failed: {e}")

        raise



def main():

    """

    Main ETL pipeline: Fetch -> Validate -> Insert

    """

    client = None

    

    try:

        # 1. Connect to ClickHouse

        client = get_clickhouse_client()

        

        # 2. Ensure table exists

        setup_table(client)

        

        # 3. Fetch data from API

        logger.info("📡 Fetching crypto market data...")

        df = fetch_crypto_data(top_n=50)

        

        if df.empty:

            logger.warning("No data fetched from API - skipping insert")

            return

        

        # 4. Insert into database

        rows_inserted = insert_data(client, df)

        logger.info(f"Pipeline completed successfully: {rows_inserted} rows processed")

        

    except Exception as e:

        logger.error(f"❌ Pipeline failed: {e}")

        raise

        

    finally:

        # Always close the connection

        if client:

            try:

                client.close()

                logger.info("ClickHouse connection closed")

            except:

                pass



if __name__ == "__main__":

    main()
