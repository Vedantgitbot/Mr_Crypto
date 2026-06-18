import os
import sys
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool

# Fix import path - add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from AI_chatbot import get_clickhouse_client
from Analytics_engine import get_crypto_analysis

# 1. SETUP & CONFIG
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

GROQ_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_KEY:
    raise ValueError("❌ Error: GROQ_API_KEY not found in .env file.")

# 2. HELPER: HANDLE DATETIMES IN JSON
def datetime_handler(obj):
    if isinstance(obj, datetime):
        return obj.strftime("%Y-%m-%d %H:%M:%S")
    return str(obj)

# 3. SYSTEM PROMPT
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

    "2. **Structure every response like this:**\n"
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
    "   • BTC Correlation: X.XX ([High/Moderate/Low/Inverse]) — omit this line entirely if analyzing BTC itself\n\n"
    "   **Key Levels:**\n"
    "   • Support: $X,XXX (X.X% away)\n"
    "   • Resistance: $X,XXX (X.X% away)\n\n"
    "   **Bottom Line:** [Specific action with entry/exit conditions]\n\n"

    "3. **Trend Interpretation:**\n"
    "   - strong_uptrend: 'Strong uptrend (price > MA7 > MA30)'\n"
    "   - uptrend: 'Uptrend momentum (price > MA7)'\n"
    "   - sideways: 'Consolidating/sideways'\n"
    "   - downtrend: 'Downtrend (price < MA7)'\n"
    "   - strong_downtrend: 'Strong downtrend (price < MA7 < MA30)'\n\n"

    "4. **Volume Context:**\n"
    "   - >2.0x: 'Extreme volume spike (potential breakout/panic)'\n"
    "   - 1.5-2.0x: 'High conviction move'\n"
    "   - 0.8-1.2x: 'Normal trading'\n"
    "   - <0.8x: 'Low conviction/fading interest'\n\n"

    "5. **Momentum Context:**\n"
    "   - RSI > 70: 'Overbought - potential pullback risk'\n"
    "   - RSI < 30: 'Oversold - potential bounce setup'\n"
    "   - MACD bullish_crossover / bearish_crossover: flag as a fresh signal worth calling out explicitly\n"
    "   - Bollinger squeeze=true: 'Volatility compression - breakout move likely imminent'\n\n"

    "6. **Actionable Conclusions:**\n"
    "   - Give specific conditions: 'Wait for break above $70,650 with 1.5x+ volume'\n"
    "   - Cite risk/reward: 'Limited upside (5.76% to resistance), downside risk to $65,000'\n"
    "   - Never be vague: Replace 'might', 'could', 'possibly' with data-backed statements\n\n"

    "7. **For Comparisons:**\n"
    "   Compare same metrics side-by-side:\n"
    "   • BTC: -2.61% below MA7, 0.55x volume, Low risk\n"
    "   • ETH: -3.65% below MA7, 0.52x volume, Low risk\n"
    "   **Conclusion:** Both weak, but BTC closer to support breakout\n\n"

    "8. **Error Handling:**\n"
    "   If data missing: 'Insufficient data for [SYMBOL]. Try BTC, ETH, SOL, or other top 10 coins.'\n\n"

    "### FORBIDDEN:\n"
    "❌ Vague language: 'struggles', 'moderate', 'fairly', 'seems like'\n"
    "❌ Missing numbers: Always show actual values with percentages\n"
    "❌ Generic advice: 'Be cautious' → Show exact levels to watch\n"
    "❌ Repetition: Don't restate the same metric multiple ways\n\n"

    "Remember: You're analyzing PRE-CALCULATED metrics. Never make up analysis. "
    "Explain what the numbers mean for trading decisions."
)

# 4. TOOL DEFINITION (native LangChain tool)
@tool
def fetch_crypto_analysis(symbol: str) -> str:
    """Fetches comprehensive market analysis including price trends, moving averages,
    volatility, RSI, MACD, Bollinger Bands, BTC correlation, volume patterns,
    support/resistance levels, and historical pattern context for a crypto asset.

    Args:
        symbol: The crypto ticker in uppercase (e.g., BTC, ETH, SOL).
    """
    ch_client = get_clickhouse_client()
    try:
        data = get_crypto_analysis(ch_client, symbol.upper())
        if not data:
            return f"Error: {symbol} not found in database."
        return json.dumps(data, default=datetime_handler)
    except Exception as e:
        return f"Database Sync Error: {str(e)}"
    finally:
        ch_client.close()

# 5. MODELS
# Reasoning model: decides whether/which tool to call
reasoning_llm = ChatGroq(
    api_key=GROQ_KEY,
    model="llama-3.3-70b-versatile",
    temperature=0.1
).bind_tools([fetch_crypto_analysis])

# Synthesis model: turns tool results into the final formatted answer
synthesis_llm = ChatGroq(
    api_key=GROQ_KEY,
    model="llama-3.1-8b-instant"
)

# 6. CORE LOGIC
def get_mrcrypto_response(user_input: str) -> str:
    """
    Same public signature as before, so Main_app.py does not need to change.
    Stateless by design (no conversation memory) — matches original behavior.
    """
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_input)
    ]

    try:
        # --- PHASE 1: INITIAL REASONING ---
        ai_message = reasoning_llm.invoke(messages)

        # --- PHASE 2: TOOL EXECUTION ---
        if ai_message.tool_calls:
            messages.append(ai_message)

            for tool_call in ai_message.tool_calls:
                tool_result = fetch_crypto_analysis.invoke(tool_call["args"])
                messages.append(
                    ToolMessage(content=tool_result, tool_call_id=tool_call["id"])
                )

            # --- PHASE 3: FINAL SYNTHESIS ---
            final_message = synthesis_llm.invoke(messages)
            return final_message.content

        return ai_message.content

    except Exception as e:
        return f"🚨 Neural Link Failure: {str(e)}"