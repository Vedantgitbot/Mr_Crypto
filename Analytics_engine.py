import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from AI_chatbot import get_clickhouse_client

# ============================================================================
# DATA FETCHING
# ============================================================================

def fetch_historical_data(client, coin_symbol, days=30):
    """Get historical price/volume data"""
    query = """
        SELECT timestamp, price, volume_24h, market_cap, change_24h
        FROM crypto_prices
        WHERE coin = %s
        AND timestamp >= now() - INTERVAL %s DAY
        ORDER BY timestamp ASC
    """
    
    result = client.query(query, parameters=[coin_symbol.upper(), days])
    
    if not result.result_rows:
        return None
    
    df = pd.DataFrame(result.result_rows, columns=result.column_names)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp')
    
    return df

# ============================================================================
# PRICE ANALYSIS
# ============================================================================

def calculate_moving_averages(df):
    """7-day and 30-day moving averages"""
    current_price = df['price'].iloc[-1]
    
    ma_7 = df['price'].tail(7).mean() if len(df) >= 7 else current_price
    ma_30 = df['price'].mean()
    
    return {
        'ma_7': round(ma_7, 2),
        'ma_30': round(ma_30, 2),
        'price_vs_ma7_pct': round(((current_price / ma_7) - 1) * 100, 2),
        'price_vs_ma30_pct': round(((current_price / ma_30) - 1) * 100, 2)
    }

def calculate_volatility(df):
    """Standard deviation of returns"""
    if len(df) < 2:
        return {'volatility_7d': 0, 'volatility_30d': 0}
    
    df['returns'] = df['price'].pct_change()
    
    vol_7d = df['returns'].tail(7).std() * 100 if len(df) >= 7 else 0
    vol_30d = df['returns'].std() * 100
    
    return {
        'volatility_7d_pct': round(vol_7d, 2),
        'volatility_30d_pct': round(vol_30d, 2),
        'risk_level': 'High' if vol_30d > 5 else 'Medium' if vol_30d > 2 else 'Low'
    }

def detect_trend(current_price, ma_7, ma_30):
    """Uptrend/Downtrend/Sideways"""
    if current_price > ma_7 > ma_30:
        return 'strong_uptrend'
    elif current_price > ma_7:
        return 'uptrend'
    elif current_price < ma_7 < ma_30:
        return 'strong_downtrend'
    elif current_price < ma_7:
        return 'downtrend'
    else:
        return 'sideways'

# ============================================================================
# VOLUME ANALYSIS  
# ============================================================================

def analyze_volume(df):
    """Volume spikes and patterns"""
    if len(df) < 2:
        return {'volume_status': 'insufficient_data'}
    
    current_volume = df['volume_24h'].iloc[-1]
    avg_volume = df['volume_24h'].mean()
    
    volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
    
    # Detect volume spike
    if volume_ratio > 2.0:
        status = 'extreme_spike'
    elif volume_ratio > 1.5:
        status = 'high_volume'
    elif volume_ratio < 0.5:
        status = 'low_volume'
    else:
        status = 'normal'
    
    return {
        'current_volume': round(current_volume, 0),
        'avg_volume_30d': round(avg_volume, 0),
        'volume_ratio': round(volume_ratio, 2),
        'volume_status': status,
        'interpretation': get_volume_interpretation(status, volume_ratio)
    }

def get_volume_interpretation(status, ratio):
    """Human-readable volume analysis"""
    if status == 'extreme_spike':
        return f"Unusual activity - {ratio:.1f}x normal volume (potential breakout or panic)"
    elif status == 'high_volume':
        return f"Above average activity - {ratio:.1f}x normal volume"
    elif status == 'low_volume':
        return f"Below average activity - {ratio:.1f}x normal volume (low conviction)"
    else:
        return "Normal trading volume"

# ============================================================================
# SUPPORT/RESISTANCE
# ============================================================================

def find_support_resistance(df, window=7):
    """Key price levels based on recent highs/lows"""
    if len(df) < window:
        return {'support': [], 'resistance': []}
    
    # Find local minima (support) and maxima (resistance)
    df['local_min'] = df['price'].rolling(window=window, center=True).min()
    df['local_max'] = df['price'].rolling(window=window, center=True).max()
    
    support_levels = df[df['price'] == df['local_min']]['price'].unique()
    resistance_levels = df[df['price'] == df['local_max']]['price'].unique()
    
    # Get closest levels to current price
    current_price = df['price'].iloc[-1]
    
    support_below = [s for s in support_levels if s < current_price]
    resistance_above = [r for r in resistance_levels if r > current_price]
    
    nearest_support = max(support_below) if support_below else df['price'].min()
    nearest_resistance = min(resistance_above) if resistance_above else df['price'].max()
    
    return {
        'nearest_support': round(nearest_support, 2),
        'nearest_resistance': round(nearest_resistance, 2),
        'support_distance_pct': round(((current_price / nearest_support) - 1) * 100, 2),
        'resistance_distance_pct': round(((nearest_resistance / current_price) - 1) * 100, 2),
        'range_30d': {
            'high': round(df['price'].max(), 2),
            'low': round(df['price'].min(), 2)
        }
    }

# ============================================================================
# PATTERN RECOGNITION (BONUS)
# ============================================================================

def find_similar_patterns(df):
    """Find historical patterns similar to current situation"""
    if len(df) < 14:
        return None
    
    current_pattern = df['price'].tail(7).pct_change().values
    
    similar_events = []
    
    # Scan through history looking for similar 7-day patterns
    for i in range(7, len(df) - 7):
        historical_pattern = df['price'].iloc[i-7:i].pct_change().values
        
        # Calculate correlation
        correlation = np.corrcoef(current_pattern[1:], historical_pattern[1:])[0, 1]
        
        if correlation > 0.8:  # High similarity
            # What happened next?
            future_return = ((df['price'].iloc[i+3] / df['price'].iloc[i]) - 1) * 100
            
            similar_events.append({
                'date': df['timestamp'].iloc[i].strftime('%Y-%m-%d'),
                'correlation': round(correlation, 2),
                'outcome_3d': round(future_return, 2)
            })
    
    return similar_events[:3] if similar_events else None  # Top 3 matches

# ============================================================================
# MAIN INTERFACE
# ============================================================================

def get_crypto_analysis(client, coin_symbol):
    """
    Main function - calls all analytics and returns complete insight
    This is what GenAi.py will use
    """
    df = fetch_historical_data(client, coin_symbol, days=30)
    
    if df is None or len(df) == 0:
        return {
            'error': f'No historical data found for {coin_symbol}',
            'symbol': coin_symbol.upper()
        }
    
    # Current snapshot
    latest = df.iloc[-1]
    current_price = latest['price']
    
    # Run all analytics
    ma = calculate_moving_averages(df)
    vol = calculate_volatility(df)
    trend = detect_trend(current_price, ma['ma_7'], ma['ma_30'])
    volume = analyze_volume(df)
    levels = find_support_resistance(df)
    patterns = find_similar_patterns(df)
    
    # Compile complete analysis
    return {
        # Basic info
        'symbol': coin_symbol.upper(),
        'timestamp': latest['timestamp'],
        'current_price': round(current_price, 2),
        'change_24h': round(latest['change_24h'], 2),
        'market_cap': round(latest['market_cap'], 0),
        
        # Technical analysis
        'moving_averages': ma,
        'volatility': vol,
        'trend': trend,
        'volume_analysis': volume,
        'support_resistance': levels,
        
        # Historical context
        'similar_patterns': patterns,
        
        # Summary insight
        'data_quality': {
            'days_analyzed': len(df),
            'last_update': latest['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
        }
    }

# ============================================================================
# STANDALONE TESTING
# ============================================================================

if __name__ == "__main__":
    # Test the analytics
    client = get_clickhouse_client()
    
    analysis = get_crypto_analysis(client, 'BTC')
    
    import json
    print(json.dumps(analysis, indent=2, default=str))
    
    client.close()