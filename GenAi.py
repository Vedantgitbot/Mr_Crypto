import os
import sys
import json
from datetime import datetime
from groq import Groq
from dotenv import load_dotenv
from pathlib import Path

# Fix import path - add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from AI_chatbot import get_latest_crypto, get_clickhouse_client
from Analytics_engine import get_crypto_analysis  

# 1. SETUP & CONFIG
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

GROQ_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_KEY:
    raise ValueError("❌ Error: GROQ_API_KEY not found in .env file.")

client = Groq(api_key=GROQ_KEY)

# 2. HELPER: HANDLE DATETIMES IN JSON
def datetime_handler(obj):
    if isinstance(obj, datetime):
        return obj.strftime("%Y-%m-%d %H:%M:%S")
    return str(obj)

# 3. TOOL DEFINITION
def get_crypto_tools():
    return [
        {
            "type": "function",
            "function": {
                "name": "fetch_crypto_analysis", 
                "description": "Fetches comprehensive market analysis including price trends, moving averages, volatility, volume patterns, support/resistance levels, and historical context for a crypto asset.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string", 
                            "description": "The crypto ticker in uppercase (e.g., BTC, ETH, SOL)."
                        }
                    },
                    "required": ["symbol"],
                },
            },
        }
    ]

# 4. CORE LOGIC
def get_mrcrypto_response(user_input):
    ch_client = get_clickhouse_client()
    
    messages = [
        {
            "role": "system", 
            "content": (
                "You are MrCrypto, a Senior Quantitative Analyst specializing in crypto markets. "
                "Your responses combine precision analytics with clear, actionable insights.\n\n"
                
                "### CRITICAL FORMATTING RULES:\n"
                "1. **Always cite exact numbers:**\n"
                "   - Price position: '$68,808 (-2.61% below MA7, -3.39% below MA30)'\n"
                "   - Volume: '0.55x normal volume (low conviction)'\n"
                "   - Key levels: 'Support $68,808 (at level), Resistance $72,771 (+5.76%)'\n"
                "   - Volatility: 'Low risk (1.51% volatility)'\n\n"
                
                "2. **Structure every response like this:**\n"
                "   **Verdict: [Bullish/Bearish/Neutral]**\n\n"
                "   **Current State:**\n"
                "   • Price: $X,XXX (±X.X% vs MA7, ±X.X% vs MA30)\n"
                "   • Trend: [strong_uptrend/uptrend/sideways/downtrend/strong_downtrend]\n"
                "   • Volume: X.XXx normal ([high/low] conviction)\n"
                "   • Risk: [Low/Medium/High] volatility (X.XX%)\n\n"
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
                
                "5. **Actionable Conclusions:**\n"
                "   - Give specific conditions: 'Wait for break above $70,650 with 1.5x+ volume'\n"
                "   - Cite risk/reward: 'Limited upside (5.76% to resistance), downside risk to $65,000'\n"
                "   - Never be vague: Replace 'might', 'could', 'possibly' with data-backed statements\n\n"
                
                "6. **For Comparisons:**\n"
                "   Compare same metrics side-by-side:\n"
                "   • BTC: -2.61% below MA7, 0.55x volume, Low risk\n"
                "   • ETH: -3.65% below MA7, 0.52x volume, Low risk\n"
                "   **Conclusion:** Both weak, but BTC closer to support breakout\n\n"
                
                "7. **Error Handling:**\n"
                "   If data missing: 'Insufficient data for [SYMBOL]. Try BTC, ETH, SOL, or other top 10 coins.'\n\n"
                
                "### FORBIDDEN:\n"
                "❌ Vague language: 'struggles', 'moderate', 'fairly', 'seems like'\n"
                "❌ Missing numbers: Always show actual values with percentages\n"
                "❌ Generic advice: 'Be cautious' → Show exact levels to watch\n"
                "❌ Repetition: Don't restate the same metric multiple ways\n\n"
                
                "Remember: You're analyzing PRE-CALCULATED metrics. Never make up analysis. "
                "Explain what the numbers mean for trading decisions."
            )
        },
        {"role": "user", "content": user_input}
    ]

    try:
        # --- PHASE 1: INITIAL REASONING ---
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            tools=get_crypto_tools(),
            tool_choice="auto",
            temperature=0.1
        )

        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls

        # --- PHASE 2: TOOL EXECUTION ---
        if tool_calls:
            messages.append(response_message)
            
            for tool_call in tool_calls:
                function_args = json.loads(tool_call.function.arguments)
                sym = function_args.get("symbol").upper()
                
                try:
                    data = get_crypto_analysis(ch_client, sym)
                    content = json.dumps(data, default=datetime_handler) if data else f"Error: {sym} not found in database."
                except Exception as e:
                    content = f"Database Sync Error: {str(e)}"
                
                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": "fetch_crypto_analysis",  
                    "content": content
                })
            
            # --- PHASE 3: FINAL SYNTHESIS ---
            final_response = client.chat.completions.create(
                model="llama-3.1-8b-instant", 
                messages=messages
            )
            return final_response.choices[0].message.content

        return response_message.content

    except Exception as e:
        return f"🚨 Neural Link Failure: {str(e)}"
    finally:
        ch_client.close()