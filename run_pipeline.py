import time
import logging
from Clickhouse_setup import main

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Run every 5 minutes (300 seconds)
INTERVAL_SECONDS = 300

logger.info("🚀 Crypto Pipeline Started - Running every 5 minutes")

while True:
    try:
        logger.info("=" * 50)
        main()
        logger.info(f"💤 Sleeping for {INTERVAL_SECONDS} seconds...")
        
    except KeyboardInterrupt:
        logger.info("👋 Pipeline stopped by user")
        break
        
    except Exception as e:
        logger.error(f"❌ Pipeline cycle failed: {e}")
        logger.info(f"🔄 Retrying in {INTERVAL_SECONDS} seconds...")
    
    time.sleep(INTERVAL_SECONDS)