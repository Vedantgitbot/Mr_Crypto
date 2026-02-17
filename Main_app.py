from nicegui import ui
import pandas as pd
import plotly.graph_objects as go
import asyncio
import sys, os
import markdown

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from AI_chatbot import get_clickhouse_client, get_latest_crypto
from GenAi import get_mrcrypto_response

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════
TOP_COINS = ["BTC", "ETH", "SOL", "BNB", "XRP", "ADA", "AVAX", "DOGE", "LINK", "DOT"]

COLORS = {
    'bg': '#0a0e14',
    'surface': '#151922',
    'surface_light': '#1e222a',
    'border': '#2d3139',
    'text': '#e6edf3',
    'text_dim': '#8b949e',
    'accent': '#ff6b35',
    'accent_hover': '#ff8c5a',
    'success': '#3fb950',
    'danger': '#f85149',
    'chart_up': '#26a69a',
    'chart_down': '#ef5350',
}

# ═══════════════════════════════════════════════════════════════
# GLOBAL STYLES
# ═══════════════════════════════════════════════════════════════
def get_global_css():
    return f"""
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<style>
* {{
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}}

body, .nicegui-content {{
    background: {COLORS['bg']};
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    color: {COLORS['text']};
    overflow: hidden;
}}

::-webkit-scrollbar {{
    width: 8px;
    height: 8px;
}}

::-webkit-scrollbar-track {{
    background: {COLORS['surface']};
}}

::-webkit-scrollbar-thumb {{
    background: {COLORS['border']};
    border-radius: 4px;
}}

::-webkit-scrollbar-thumb:hover {{
    background: {COLORS['text_dim']};
}}

.terminal-header {{
    background: linear-gradient(135deg, {COLORS['surface']} 0%, {COLORS['surface_light']} 100%);
    border-bottom: 1px solid {COLORS['border']};
    padding: 12px 24px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: 60px;
}}

.logo-text {{
    font-size: 18px;
    font-weight: 800;
    letter-spacing: -0.02em;
    background: linear-gradient(135deg, {COLORS['accent']} 0%, {COLORS['accent_hover']} 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}}

.status-badge {{
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 6px 12px;
    background: rgba(63, 185, 80, 0.1);
    border: 1px solid rgba(63, 185, 80, 0.3);
    border-radius: 20px;
    font-size: 12px;
    color: {COLORS['success']};
}}

.status-dot {{
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: {COLORS['success']};
    animation: pulse-dot 2s ease-in-out infinite;
}}

@keyframes pulse-dot {{
    0%, 100% {{ opacity: 1; transform: scale(1); }}
    50% {{ opacity: 0.6; transform: scale(0.9); }}
}}

.coin-selector {{
    padding: 20px;
    border-bottom: 1px solid {COLORS['border']};
}}

.coin-card {{
    background: {COLORS['surface']};
    border: 2px solid {COLORS['border']};
    border-radius: 10px;
    padding: 14px;
    cursor: pointer;
    transition: all 0.2s ease;
    position: relative;
    overflow: hidden;
    margin-bottom: 10px;
}}

.coin-card:hover {{
    border-color: {COLORS['accent']};
    transform: translateY(-2px);
    box-shadow: 0 8px 16px rgba(255, 107, 53, 0.15);
}}

.coin-card.active {{
    background: linear-gradient(135deg, rgba(255, 107, 53, 0.15) 0%, rgba(255, 107, 53, 0.05) 100%);
    border-color: {COLORS['accent']};
    box-shadow: 0 4px 12px rgba(255, 107, 53, 0.2);
}}

.coin-card.active::before {{
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 4px;
    height: 100%;
    background: {COLORS['accent']};
}}

.coin-symbol {{
    font-size: 13px;
    font-weight: 700;
    color: {COLORS['text']};
    margin-bottom: 4px;
}}

.coin-price {{
    font-size: 15px;
    font-weight: 600;
    color: {COLORS['text']};
}}

.coin-change {{
    font-size: 11px;
    font-weight: 600;
    margin-top: 4px;
}}

.coin-change.positive {{ color: {COLORS['success']}; }}
.coin-change.negative {{ color: {COLORS['danger']}; }}

.chart-container {{
    background: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    border-radius: 12px;
    padding: 20px;
    height: 100%;
    display: flex;
    flex-direction: column;
}}

.chart-header {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 16px;
    padding-bottom: 16px;
    border-bottom: 1px solid {COLORS['border']};
}}

.chart-title {{
    font-size: 20px;
    font-weight: 700;
    color: {COLORS['text']};
}}

.chart-price {{
    font-size: 28px;
    font-weight: 700;
    color: {COLORS['text']};
}}

.chart-change {{
    font-size: 14px;
    font-weight: 600;
    margin-left: 12px;
}}

.chart-subtitle {{
    font-size: 13px;
    color: {COLORS['text_dim']};
    margin-top: 4px;
}}

.chat-panel {{
    background: {COLORS['surface']};
    border-left: 1px solid {COLORS['border']};
    display: flex;
    flex-direction: column;
    height: 100%;
}}

.chat-header {{
    padding: 20px;
    border-bottom: 1px solid {COLORS['border']};
}}

.chat-title {{
    font-size: 16px;
    font-weight: 700;
    color: {COLORS['text']};
    display: flex;
    align-items: center;
    gap: 8px;
}}

.chat-subtitle {{
    font-size: 12px;
    color: {COLORS['text_dim']};
    margin-top: 4px;
}}

.messages-container {{
    flex: 1;
    overflow-y: auto;
    padding: 20px;
    display: flex;
    flex-direction: column;
    gap: 16px;
}}

.message-user {{
    align-self: flex-end;
    max-width: 75%;
    background: linear-gradient(135deg, rgba(255, 107, 53, 0.2) 0%, rgba(255, 107, 53, 0.1) 100%);
    border: 1px solid rgba(255, 107, 53, 0.3);
    border-radius: 16px 16px 4px 16px;
    padding: 12px 16px;
    font-size: 14px;
    line-height: 1.5;
    animation: slideInRight 0.3s ease;
    word-wrap: break-word;
}}

.message-assistant {{
    align-self: flex-start;
    max-width: 85%;
    background: {COLORS['surface_light']};
    border: 1px solid {COLORS['border']};
    border-radius: 16px 16px 16px 4px;
    padding: 14px 18px;
    font-size: 14px;
    line-height: 1.6;
    animation: slideInLeft 0.3s ease;
    word-wrap: break-word;
}}

@keyframes slideInRight {{
    from {{ opacity: 0; transform: translateX(20px); }}
    to {{ opacity: 1; transform: translateX(0); }}
}}

@keyframes slideInLeft {{
    from {{ opacity: 0; transform: translateX(-20px); }}
    to {{ opacity: 1; transform: translateX(0); }}
}}

.typing-indicator {{
    align-self: flex-start;
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 14px 18px;
    background: {COLORS['surface_light']};
    border: 1px solid {COLORS['border']};
    border-radius: 16px 16px 16px 4px;
}}

.typing-dot {{
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: {COLORS['text_dim']};
    animation: typing-bounce 1.4s infinite ease-in-out;
}}

.typing-dot:nth-child(1) {{ animation-delay: 0s; }}
.typing-dot:nth-child(2) {{ animation-delay: 0.2s; }}
.typing-dot:nth-child(3) {{ animation-delay: 0.4s; }}

@keyframes typing-bounce {{
    0%, 60%, 100% {{ transform: translateY(0); opacity: 0.7; }}
    30% {{ transform: translateY(-10px); opacity: 1; }}
}}

.welcome-container {{
    text-align: center;
    padding: 60px 24px;
    opacity: 0.7;
}}

.welcome-icon {{
    font-size: 48px;
    margin-bottom: 16px;
    opacity: 0.5;
}}

.welcome-title {{
    font-size: 20px;
    font-weight: 700;
    color: {COLORS['text']};
    margin-bottom: 8px;
}}

.welcome-text {{
    font-size: 14px;
    color: {COLORS['text_dim']};
    line-height: 1.6;
    max-width: 300px;
    margin: 0 auto;
}}

.chat-input-container {{
    padding: 20px;
    border-top: 1px solid {COLORS['border']};
    background: {COLORS['surface']};
}}

.chat-input-wrapper {{
    display: flex;
    align-items: center;
    gap: 12px;
    background: {COLORS['surface_light']};
    border: 2px solid {COLORS['border']};
    border-radius: 24px;
    padding: 4px 4px 4px 20px;
    transition: all 0.2s ease;
}}

.chat-input-wrapper:focus-within {{
    border-color: {COLORS['accent']};
    box-shadow: 0 0 0 3px rgba(255, 107, 53, 0.1);
}}

.send-button {{
    background: linear-gradient(135deg, {COLORS['accent']} 0%, {COLORS['accent_hover']} 100%);
    border: none;
    border-radius: 50%;
    width: 40px;
    height: 40px;
    cursor: pointer;
    transition: all 0.2s ease;
    box-shadow: 0 2px 8px rgba(255, 107, 53, 0.3);
}}

.send-button:hover {{
    transform: scale(1.05);
    box-shadow: 0 4px 12px rgba(255, 107, 53, 0.5);
}}

@media (max-width: 768px) {{
    .terminal-header {{ padding: 12px 16px; }}
    .logo-text {{ font-size: 16px; }}
    .chart-price {{ font-size: 24px; }}
    .message-user, .message-assistant {{ max-width: 90%; }}
}}
</style>
"""

# ═══════════════════════════════════════════════════════════════
# DATA FUNCTIONS
# ═══════════════════════════════════════════════════════════════
_client = None

def get_client():
    global _client
    if not _client:
        _client = get_clickhouse_client()
    return _client

def fetch_coin(sym):
    try:
        return get_latest_crypto(get_client(), sym)
    except:
        return None

def create_chart(sym):
    try:
        q = """
        SELECT timestamp, price
        FROM crypto_prices
        WHERE coin = %s
        ORDER BY timestamp DESC
        LIMIT 288
        """
        r = get_client().query(q, parameters=[sym])
        df = pd.DataFrame(r.result_rows, columns=r.column_names)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.sort_values("timestamp")
    except:
        return go.Figure()

    if df.empty:
        return go.Figure()

    price_change = df.price.iloc[-1] - df.price.iloc[0]
    line_color = COLORS['chart_up'] if price_change >= 0 else COLORS['chart_down']
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df.timestamp,
        y=df.price,
        mode='lines',
        line=dict(color=line_color, width=2.5),
        fill='tozeroy',
        fillcolor=f'rgba({int(line_color[1:3], 16)}, {int(line_color[3:5], 16)}, {int(line_color[5:7], 16)}, 0.15)',
        hovertemplate='<b>$%{y:,.2f}</b><br>%{x|%b %d, %H:%M}<extra></extra>',
        name=sym
    ))
    
    fig.update_layout(
        autosize=True,
        height=450,
        margin=dict(l=0, r=0, t=10, b=0),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=False,
        xaxis=dict(
            showgrid=True,
            gridcolor=COLORS['border'],
            color=COLORS['text_dim'],
            showline=False,
            zeroline=False
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor=COLORS['border'],
            color=COLORS['text_dim'],
            showline=False,
            zeroline=False,
            tickprefix='$',
            tickformat=',.0f'
        ),
        hovermode='x unified',
        font=dict(family='Inter', size=12, color=COLORS['text_dim'])
    )
    
    return fig

def extract_coin_symbols(text):
    text_upper = text.upper()
    detected = []
    
    for coin in TOP_COINS:
        if coin in text_upper:
            detected.append(coin)
    
    name_map = {
        "BITCOIN": "BTC", "ETHEREUM": "ETH", "SOLANA": "SOL",
        "BINANCE": "BNB", "RIPPLE": "XRP", "CARDANO": "ADA",
        "AVALANCHE": "AVAX", "DOGECOIN": "DOGE", "CHAINLINK": "LINK",
        "POLKADOT": "DOT"
    }
    
    for name, symbol in name_map.items():
        if name in text_upper and symbol not in detected:
            detected.append(symbol)
    
    return detected

# ═══════════════════════════════════════════════════════════════
# MAIN APPLICATION
# ═══════════════════════════════════════════════════════════════
@ui.page('/')
def main_page():
    ui.add_head_html(get_global_css())
    
    state = {"current_coin": "BTC", "coin_data": {}}
    
    for coin in TOP_COINS:
        state["coin_data"][coin] = fetch_coin(coin) or {}
    
    with ui.row().classes('w-full terminal-header'):
        ui.html('<div class="logo-text">⚡ MRCRYPTO TERMINAL</div>', sanitize=False)
        ui.html('''
            <div class="status-badge">
                <div class="status-dot"></div>
                <span>Live Market Data</span>
            </div>
        ''', sanitize=False)
    
    with ui.row().classes('w-full').style(f'height: calc(100vh - 60px); background: {COLORS["bg"]};'):
        
        with ui.column().classes('h-full').style('flex: 0 0 280px; overflow-y: auto;'):
            ui.html('<div class="coin-selector"><div style="font-size: 13px; font-weight: 700; color: #8b949e; margin-bottom: 12px; text-transform: uppercase; letter-spacing: 0.05em;">Markets</div></div>', sanitize=False)
            
            coin_cards_container = ui.column().style('padding: 0 20px 20px 20px;')
            coin_cards = {}
            
            with coin_cards_container:
                for coin in TOP_COINS:
                    data = state["coin_data"].get(coin, {})
                    price = data.get("price", 0)
                    change = data.get("change_24h", 0)
                    
                    card_html = f'''
                    <div class="coin-card {'active' if coin == state["current_coin"] else ''}" id="coin-{coin}">
                        <div class="coin-symbol">{coin}</div>
                        <div class="coin-price">${price:,.2f}</div>
                        <div class="coin-change {'positive' if change >= 0 else 'negative'}">{change:+.2f}%</div>
                    </div>
                    '''
                    card_element = ui.html(card_html, sanitize=False)
                    coin_cards[coin] = card_element
                    
                    def make_click_handler(symbol):
                        async def handler():
                            state["current_coin"] = symbol
                            
                            for c, card in coin_cards.items():
                                data = state["coin_data"].get(c, {})
                                price = data.get("price", 0)
                                change = data.get("change_24h", 0)
                                card.content = f'''
                                <div class="coin-card {'active' if c == symbol else ''}" id="coin-{c}">
                                    <div class="coin-symbol">{c}</div>
                                    <div class="coin-price">${price:,.2f}</div>
                                    <div class="coin-change {'positive' if change >= 0 else 'negative'}">{change:+.2f}%</div>
                                </div>
                                '''
                            
                            data = state["coin_data"].get(symbol, {})
                            chart_header.content = f'''
                            <div class="chart-header">
                                <div>
                                    <div class="chart-title">{symbol} / USD</div>
                                    <div class="chart-subtitle">Last 24 hours</div>
                                </div>
                                <div style="text-align: right;">
                                    <div class="chart-price">${data.get("price", 0):,.2f}</div>
                                    <div class="chart-change {'positive' if data.get('change_24h', 0) >= 0 else 'negative'}">{data.get('change_24h', 0):+.2f}%</div>
                                </div>
                            </div>
                            '''
                            chart_element.update_figure(create_chart(symbol))
                        return handler
                    
                    card_element.on('click', make_click_handler(coin))
        
        with ui.column().classes('h-full').style('flex: 1; padding: 20px; overflow: hidden;'):
            with ui.column().classes('chart-container'):
                initial_data = state["coin_data"].get("BTC", {})
                chart_header = ui.html(f'''
                <div class="chart-header">
                    <div>
                        <div class="chart-title">BTC / USD</div>
                        <div class="chart-subtitle">Last 24 hours</div>
                    </div>
                    <div style="text-align: right;">
                        <div class="chart-price">${initial_data.get("price", 0):,.2f}</div>
                        <div class="chart-change {'positive' if initial_data.get('change_24h', 0) >= 0 else 'negative'}">{initial_data.get('change_24h', 0):+.2f}%</div>
                    </div>
                </div>
                ''', sanitize=False)
                
                chart_element = ui.plotly(create_chart("BTC")).style('flex: 1; width: 100%;')
        
        with ui.column().classes('chat-panel').style('flex: 0 0 400px;'):
            ui.html('''
            <div class="chat-header">
                <div class="chat-title">
                    <span>🤖</span>
                    <span>AI Assistant</span>
                </div>
                <div class="chat-subtitle">Powered by advanced market analytics</div>
            </div>
            ''', sanitize=False)
            
            messages_scroll = ui.scroll_area().classes('messages-container')
            with messages_scroll:
                messages_container = ui.column().classes('w-full')
                
                with messages_container:
                    ui.html('''
                    <div class="welcome-container">
                        <div class="welcome-icon">💬</div>
                        <div class="welcome-title">Welcome to MrCrypto</div>
                        <div class="welcome-text">
                            Ask me about market trends, price analysis, or specific cryptocurrencies. 
                            I'll provide data-driven insights based on real-time analytics.
                        </div>
                    </div>
                    ''', sanitize=False)
            
            with ui.column().classes('chat-input-container'):
                with ui.row().classes('w-full chat-input-wrapper'):
                    chat_input = ui.input(placeholder='Ask about crypto markets...').props('borderless').style(
                        'flex: 1; font-size: 14px; background: transparent; color: #e6edf3;'
                    )
                    send_btn = ui.button(icon='send').props('flat round dense').classes('send-button')
            
            typing_indicator = None
            
            async def send_message():
                nonlocal typing_indicator
                
                user_text = chat_input.value.strip()
                if not user_text:
                    return
                
                chat_input.value = ""
                
                with messages_container:
                    ui.html(f'<div class="message-user">{user_text}</div>', sanitize=False)
                
                mentioned = extract_coin_symbols(user_text)
                if mentioned:
                    symbol = mentioned[0]
                    state["current_coin"] = symbol
                    
                    for c, card in coin_cards.items():
                        data = state["coin_data"].get(c, {})
                        price = data.get("price", 0)
                        change = data.get("change_24h", 0)
                        card.content = f'''
                        <div class="coin-card {'active' if c == symbol else ''}" id="coin-{c}">
                            <div class="coin-symbol">{c}</div>
                            <div class="coin-price">${price:,.2f}</div>
                            <div class="coin-change {'positive' if change >= 0 else 'negative'}">{change:+.2f}%</div>
                        </div>
                        '''
                    
                    data = state["coin_data"].get(symbol, {})
                    chart_header.content = f'''
                    <div class="chart-header">
                        <div>
                            <div class="chart-title">{symbol} / USD</div>
                            <div class="chart-subtitle">Last 24 hours</div>
                        </div>
                        <div style="text-align: right;">
                            <div class="chart-price">${data.get("price", 0):,.2f}</div>
                            <div class="chart-change {'positive' if data.get('change_24h', 0) >= 0 else 'negative'}">{data.get('change_24h', 0):+.2f}%</div>
                        </div>
                    </div>
                    '''
                    chart_element.update_figure(create_chart(symbol))
                
                with messages_container:
                    typing_indicator = ui.html('''
                    <div class="typing-indicator">
                        <div class="typing-dot"></div>
                        <div class="typing-dot"></div>
                        <div class="typing-dot"></div>
                    </div>
                    ''', sanitize=False)
                
                messages_scroll.scroll_to(percent=1.0)
                
                loop = asyncio.get_event_loop()
                try:
                    response = await loop.run_in_executor(None, get_mrcrypto_response, user_text)
                except Exception as e:
                    response = f"⚠️ Error: Unable to process request. {str(e)}"
                
                if typing_indicator:
                    typing_indicator.delete()
                    typing_indicator = None
                
                with messages_container:
                    html_response = markdown.markdown(response)
                    ui.html(f'<div class="message-assistant">{html_response}</div>', sanitize=False)
                
                messages_scroll.scroll_to(percent=1.0)
            
            send_btn.on('click', send_message)
            chat_input.on('keydown.enter', send_message)

if __name__ in {"__main__", "__mp_main__"}:
    ui.run(
        host='0.0.0.0',
        port=8080,
        title="MrCrypto Terminal",
        dark=True,
        reload=False
    )