import os
import sys
import json
import html
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from AI_chatbot import get_clickhouse_client
from Analytics_engine import get_crypto_analysis
from intent_classifier import classify_intent
from coin_resolver import resolve_coin_symbol

# ============================================================================
# SETUP & CONFIG
# ============================================================================
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

GROQ_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_KEY:
    raise ValueError("❌ Error: GROQ_API_KEY not found in .env file.")

# Shared ClickHouse client - opened once, reused across all calls
_ch_client = None

def get_shared_client():
    global _ch_client
    if _ch_client is None:
        _ch_client = get_clickhouse_client()
    return _ch_client

# ============================================================================
# HELPERS
# ============================================================================
def datetime_handler(obj):
    if isinstance(obj, datetime):
        return obj.strftime("%Y-%m-%d %H:%M:%S")
    return str(obj)

def fetch_analysis(symbol: str) -> str:
    """Fetch pre-calculated analytics for one coin. Returns JSON string."""
    resolved = resolve_coin_symbol(symbol) or symbol.upper()
    try:
        data = get_crypto_analysis(get_shared_client(), resolved)
        if not data or "error" in data:
            return json.dumps({"error": f"No data found for {resolved}."})
        return json.dumps(data, default=datetime_handler)
    except Exception as e:
        return json.dumps({"error": f"Database error: {str(e)}"})

# ============================================================================
# MODELS
# Fast/cheap model: single-coin synthesis, low-complexity responses
# Big model: multi-coin comparison (harder reasoning task)
# ============================================================================
_fast_llm = ChatGroq(api_key=GROQ_KEY, model="llama-3.1-8b-instant",    temperature=0.1)
_deep_llm = ChatGroq(api_key=GROQ_KEY, model="llama-3.3-70b-versatile", temperature=0.1)

# ============================================================================
# SYSTEM PROMPT
# ============================================================================
SYSTEM_PROMPT = (
    "You are MrCrypto, a Senior Quantitative Analyst specializing in crypto markets. "
    "Your responses combine precision analytics with clear, actionable insights.\n\n"

    "### CRITICAL FORMATTING RULES:\n"
    "1. **Always cite exact numbers:**\n"
    "   - Price position: '$68,808 (-2.61% below MA7, -3.39% below MA30)'\n"
    "   - Volume: '0.55x normal volume (low conviction)'\n"
    "   - Key levels: 'Support $68,808 (at level), Resistance $72,771 (+5.76%)'\n"
    "   - Volatility: 'Low risk (1.51% volatility)'\n"
    "   - Momentum: 'RSI 38.2 (neutral)', 'MACD bullish crossover'\n\n"

    "2. **Structure every single-coin response like this:**\n"
    "   **Verdict: [Bullish/Bearish/Neutral]**\n\n"
    "   **Current State:**\n"
    "   • Price: $X,XXX (±X.X% vs MA7, ±X.X% vs MA30)\n"
    "   • Trend: [strong_uptrend/uptrend/sideways/downtrend/strong_downtrend]\n"
    "   • Volume: X.XXx normal ([high/low] conviction)\n"
    "   • Risk: [Low/Medium/High] volatility (X.XX%)\n\n"
    "   **Momentum & Volatility:**\n"
    "   • RSI: XX.X ([Overbought >70 / Oversold <30 / Neutral])\n"
    "   • MACD: [Bullish/Bearish] ([crossover detected/no crossover])\n"
    "   • Bollinger Bands: Price [at upper band/at lower band/within bands] (squeeze: [Yes/No])\n"
    "   • BTC Correlation: X.XX ([High/Moderate/Low/Inverse]) — omit entirely if analyzing BTC\n\n"
    "   **Key Levels:**\n"
    "   • Support: $X,XXX (X.X% away)\n"
    "   • Resistance: $X,XXX (X.X% away)\n\n"
    "   **Bottom Line:** [Specific action with entry/exit conditions]\n\n"

    "3. **For comparisons, show side-by-side metrics then a clear winner:**\n"
    "   • COIN_A: -2.61% below MA7, RSI 42, 0.55x volume, Low risk\n"
    "   • COIN_B: -3.65% below MA7, RSI 38, 0.52x volume, Low risk\n"
    "   **Conclusion:** [Which is stronger and why, with exact numbers]\n\n"

    "4. **Trend Interpretation:**\n"
    "   - strong_uptrend: price > MA7 > MA30\n"
    "   - uptrend: price > MA7\n"
    "   - sideways: consolidating\n"
    "   - downtrend: price < MA7\n"
    "   - strong_downtrend: price < MA7 < MA30\n\n"

    "5. **Volume Context:**\n"
    "   >2.0x: Extreme spike | 1.5-2.0x: High conviction | 0.8-1.2x: Normal | <0.8x: Low conviction\n\n"

    "6. **Momentum Context:**\n"
    "   RSI >70: Overbought - pullback risk | RSI <30: Oversold - bounce setup\n"
    "   MACD crossover: flag as a fresh signal explicitly\n"
    "   Bollinger squeeze=true: Volatility compression - breakout likely imminent\n\n"

    "7. **Actionable Conclusions only:**\n"
    "   ❌ 'might', 'could', 'possibly', 'seems like', 'struggles', 'moderate', 'fairly'\n"
    "   ✅ 'Wait for break above $X with 1.5x+ volume' | 'Risk to $X if support breaks'\n\n"

    "Remember: You're analyzing PRE-CALCULATED metrics. Never invent numbers."
)

# ============================================================================
# INTENT-BASED RESPONSE HANDLERS
# ============================================================================

def _handle_greeting() -> str:
    return (
        "Hey! I'm MrCrypto — ask me about any of the top 10 coins. "
        "Try: *'How's BTC looking?'* or *'Compare ETH and SOL'*."
    )

def _handle_off_topic() -> str:
    return (
        "I'm built for crypto market analysis — price trends, momentum indicators, "
        "support/resistance levels, and coin comparisons. "
        "Ask me something like *'Is SOL bullish right now?'* and I'll break it down with real data."
    )

def _handle_ambiguous() -> str:
    return (
        "Which coin did you want to look at? I cover the top 10: "
        "**BTC, ETH, SOL, BNB, XRP, ADA, AVAX, DOGE, LINK, DOT**. "
        "You can also use full names — e.g. *'Bitcoin'*, *'Solana'*, *'Chainlink'*."
    )

def _handle_analysis(symbol: str, user_input: str) -> str:
    """Single-coin analysis — cheap fast model."""
    analysis_json = fetch_analysis(symbol)
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=(
            f"User question: {user_input}\n\n"
            f"Pre-calculated analytics for {symbol.upper()}:\n{analysis_json}"
        ))
    ]
    return _fast_llm.invoke(messages).content

def _handle_comparison(symbols: list, user_input: str) -> str:
    """Multi-coin comparison — big model for harder synthesis."""
    analyses = {sym: fetch_analysis(sym) for sym in symbols}
    combined = "\n\n".join(
        f"=== {sym} ===\n{data}" for sym, data in analyses.items()
    )
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=(
            f"User question: {user_input}\n\n"
            f"Pre-calculated analytics for comparison:\n{combined}"
        ))
    ]
    return _deep_llm.invoke(messages).content

# ============================================================================
# PUBLIC INTERFACE — same signature, Main_app.py unchanged
# ============================================================================

def get_mrcrypto_response(user_input: str) -> str:
    try:
        result = classify_intent(user_input)
        intent  = result["intent"]
        symbols = result["symbols"]

        if intent == "GREETING":
            return _handle_greeting()

        if intent == "OFF_TOPIC":
            return _handle_off_topic()

        if intent == "AMBIGUOUS":
            return _handle_ambiguous()

        if intent == "COMPARISON":
            return _handle_comparison(symbols, user_input)

        # ANALYSIS — single coin
        return _handle_analysis(symbols[0], user_input)

    except Exception as e:
        return f"🚨 Neural Link Failure: {str(e)}"