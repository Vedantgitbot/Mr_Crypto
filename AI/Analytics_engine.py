import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from AI_chatbot import get_clickhouse_client

# ============================================================================
# SIMPLE TTL CACHE
# ============================================================================
_analysis_cache = {}
CACHE_TTL_SECONDS = 60  # cached results are reused for 60s before recomputing

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
# MOMENTUM & VOLATILITY INDICATORS (NEW)
# ============================================================================

def calculate_rsi(df, period=14):
    """Relative Strength Index - momentum oscillator (0-100)"""
    if len(df) < period + 1:
        return {'rsi': None, 'rsi_signal': 'insufficient_data'}

    delta = df['price'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    avg_gain = gain.rolling(window=period).mean().iloc[-1]
    avg_loss = loss.rolling(window=period).mean().iloc[-1]

    if avg_loss == 0:
        rsi = 100.0
    else:
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

    if rsi > 70:
        signal = 'overbought'
    elif rsi < 30:
        signal = 'oversold'
    else:
        signal = 'neutral'

    return {'rsi': round(rsi, 2), 'rsi_signal': signal}

def calculate_macd(df, fast=12, slow=26, signal=9):
    """MACD - trend-following momentum indicator"""
    if len(df) < slow + signal:
        return {'macd_line': None, 'signal_line': None, 'momentum': 'insufficient_data'}

    ema_fast = df['price'].ewm(span=fast, adjust=False).mean()
    ema_slow = df['price'].ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line

    current_hist = histogram.iloc[-1]
    prev_hist = histogram.iloc[-2] if len(histogram) > 1 else current_hist

    if current_hist > 0 and prev_hist <= 0:
        momentum = 'bullish_crossover'
    elif current_hist < 0 and prev_hist >= 0:
        momentum = 'bearish_crossover'
    elif current_hist > 0:
        momentum = 'bullish'
    else:
        momentum = 'bearish'

    return {
        'macd_line': round(macd_line.iloc[-1], 4),
        'signal_line': round(signal_line.iloc[-1], 4),
        'histogram': round(current_hist, 4),
        'momentum': momentum
    }

def calculate_bollinger_bands(df, period=20, num_std=2):
    """Bollinger Bands - volatility bands around a moving average"""
    if len(df) < period:
        return {'upper_band': None, 'lower_band': None, 'position': 'insufficient_data'}

    rolling_mean = df['price'].rolling(window=period).mean()
    rolling_std = df['price'].rolling(window=period).std()
    upper = rolling_mean + (rolling_std * num_std)
    lower = rolling_mean - (rolling_std * num_std)

    current_price = df['price'].iloc[-1]
    current_upper = upper.iloc[-1]
    current_lower = lower.iloc[-1]
    current_mean = rolling_mean.iloc[-1]
    band_width = current_upper - current_lower

    position_pct = ((current_price - current_lower) / band_width * 100) if band_width > 0 else 50.0

    if current_price >= current_upper:
        position = 'at_upper_band'
    elif current_price <= current_lower:
        position = 'at_lower_band'
    else:
        position = 'within_bands'

    is_squeeze = bool((band_width / current_mean * 100) < 5) if current_mean else False

    return {
        'upper_band': round(current_upper, 2),
        'middle_band': round(current_mean, 2),
        'lower_band': round(current_lower, 2),
        'band_position_pct': round(position_pct, 1),
        'position': position,
        'squeeze': is_squeeze  # tight bands often precede a breakout
    }

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

    df['local_min'] = df['price'].rolling(window=window, center=True).min()
    df['local_max'] = df['price'].rolling(window=window, center=True).max()

    support_levels = df[df['price'] == df['local_min']]['price'].unique()
    resistance_levels = df[df['price'] == df['local_max']]['price'].unique()

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
# BTC CORRELATION (NEW)
# ============================================================================

def calculate_btc_correlation(client, df, coin_symbol):
    """How closely an asset's returns track BTC's returns over the same window"""
    if coin_symbol.upper() == 'BTC':
        return {'btc_correlation': None, 'note': 'n/a_is_btc'}

    btc_df = fetch_historical_data(client, 'BTC', days=30)
    if btc_df is None or len(btc_df) < 2 or len(df) < 2:
        return {'btc_correlation': None, 'note': 'insufficient_data'}

    merged = pd.merge(
        df[['timestamp', 'price']],
        btc_df[['timestamp', 'price']],
        on='timestamp',
        suffixes=('_coin', '_btc')
    )

    if len(merged) < 3:
        return {'btc_correlation': None, 'note': 'insufficient_overlapping_data'}

    coin_returns = merged['price_coin'].pct_change().dropna()
    btc_returns = merged['price_btc'].pct_change().dropna()

    if len(coin_returns) < 2:
        return {'btc_correlation': None, 'note': 'insufficient_data'}

    correlation = coin_returns.corr(btc_returns)
    if pd.isna(correlation):
        return {'btc_correlation': None, 'note': 'insufficient_data'}

    if correlation > 0.7:
        strength = 'high_correlation'
    elif correlation > 0.3:
        strength = 'moderate_correlation'
    elif correlation > -0.3:
        strength = 'low_correlation'
    else:
        strength = 'inverse_correlation'

    return {'btc_correlation': round(correlation, 2), 'correlation_strength': strength}

# ============================================================================
# PATTERN RECOGNITION (BONUS)
# ============================================================================

def find_similar_patterns(df):
    """Find historical patterns similar to current situation"""
    if len(df) < 14:
        return None

    current_pattern = df['price'].tail(7).pct_change().values

    similar_events = []

    for i in range(7, len(df) - 7):
        historical_pattern = df['price'].iloc[i-7:i].pct_change().values
        correlation = np.corrcoef(current_pattern[1:], historical_pattern[1:])[0, 1]

        if correlation > 0.8:
            future_return = ((df['price'].iloc[i+3] / df['price'].iloc[i]) - 1) * 100
            similar_events.append({
                'date': df['timestamp'].iloc[i].strftime('%Y-%m-%d'),
                'correlation': round(correlation, 2),
                'outcome_3d': round(future_return, 2)
            })

    return similar_events[:3] if similar_events else None

# ============================================================================
# MAIN INTERFACE
# ============================================================================

def get_crypto_analysis(client, coin_symbol, use_cache=True):
    """
    Main function - calls all analytics and returns complete insight.
    This is what GenAi.py uses. Results are cached briefly (CACHE_TTL_SECONDS)
    so rapid repeat questions about the same coin don't re-hit ClickHouse and
    re-run every calculation from scratch.
    """
    cache_key = coin_symbol.upper()
    now = time.time()

    if use_cache and cache_key in _analysis_cache:
        cached_result, cached_at = _analysis_cache[cache_key]
        if now - cached_at < CACHE_TTL_SECONDS:
            cached_result = dict(cached_result)
            cached_result['data_quality'] = dict(cached_result['data_quality'])
            cached_result['data_quality']['served_from_cache'] = True
            return cached_result

    df = fetch_historical_data(client, coin_symbol, days=30)

    if df is None or len(df) == 0:
        return {
            'error': f'No historical data found for {coin_symbol}',
            'symbol': coin_symbol.upper()
        }

    latest = df.iloc[-1]
    current_price = latest['price']

    ma = calculate_moving_averages(df)
    vol = calculate_volatility(df)
    trend = detect_trend(current_price, ma['ma_7'], ma['ma_30'])
    volume = analyze_volume(df)
    levels = find_support_resistance(df)
    patterns = find_similar_patterns(df)
    rsi = calculate_rsi(df)
    macd = calculate_macd(df)
    bollinger = calculate_bollinger_bands(df)
    btc_corr = calculate_btc_correlation(client, df, coin_symbol)

    result = {
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
        'rsi': rsi,
        'macd': macd,
        'bollinger_bands': bollinger,
        'btc_correlation': btc_corr,

        # Historical context
        'similar_patterns': patterns,

        # Summary insight
        'data_quality': {
            'days_analyzed': len(df),
            'last_update': latest['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
            'served_from_cache': False
        }
    }

    if use_cache:
        _analysis_cache[cache_key] = (result, now)

    return result

# ============================================================================
# STANDALONE TESTING
# ============================================================================

if __name__ == "__main__":
    client = get_clickhouse_client()

    analysis = get_crypto_analysis(client, 'BTC')

    import json
    print(json.dumps(analysis, indent=2, default=str))

    client.close()