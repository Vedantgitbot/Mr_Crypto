# Mr_Crypto
Real-time crypto analytics powered by quantitative analysis and AI, eliminating hallucination with data-backed insights
🎯 The Problem
Crypto traders face a critical gap in decision-making tools:

TradingView & Exchanges → Overwhelming data, no actionable insights
AI Chatbots → Hallucinate price predictions without data backing
Manual Analysis → Time-consuming, requires technical expertise

The cost? Traders make decisions based on either incomplete data or unreliable AI advice.

💡 The Solution
MrCrypto Terminal bridges this gap by combining pre-calculated quantitative analytics with AI-powered explanations:
✅ Data-First Architecture → Calculate metrics (MAs, volatility, S/R levels) before AI analysis
✅ Zero Hallucination → AI explains your math, doesn't invent it
✅ Actionable Insights → Specific entry/exit levels, not vague advice
✅ Real-Time Updates → Automated ETL pipeline with 5-min refresh

🏗️ Architecture
┌─────────────────┐      ┌──────────────────┐      ┌─────────────────┐
│   CoinGecko API │─────▶│  ClickHouse DB   │─────▶│  Analytics      │
│   (50 coins)    │      │  (Time-Series)   │      │  Engine         │
└─────────────────┘      └──────────────────┘      └─────────────────┘
                                  │                          │
                                  ▼                          ▼
                         ┌──────────────────────────────────────┐
                         │   NiceGUI Frontend + Groq AI        │
                         │   (Bloomberg Terminal-style UI)      │
                         └──────────────────────────────────────┘
ETL Pipeline:
CoinGecko API → Data Validation → ClickHouse Storage → Analytics Calculation → AI Synthesis → User Interface

🛠️ Tech Stack
Data Infrastructure

ClickHouse – Columnar time-series database with partitioning
Pandas – Analytics pipeline (MAs, volatility, pattern recognition)
Automated ETL – Retry logic, backoff strategies, data validation

AI/ML Layer

Groq API – Llama 3.3 70B for low-latency inference
Function Calling – Tool execution with structured outputs
Zero-Hallucination Design – AI explains pre-calculated metrics only

Application Layer

Python 3.12+ – Async backend with NiceGUI framework
Plotly – Interactive real-time charting
Docker Compose – Multi-container orchestration

Analytics Capabilities

Moving Averages (7-day, 30-day)
Volatility & Risk Assessment (standard deviation of returns)
Support/Resistance Detection (rolling window analysis)
Volume Spike Analysis (statistical thresholds)
Pattern Recognition (correlation-based historical matching)


🚀 Quick Start
Prerequisites

Docker & Docker Compose
CoinGecko API Key (Get free key)
Groq API Key (Get free key)


mrcrypto-terminal/
├── .env.example          
├── .gitignore           
├── README.md            
├── docker-compose.yml   
├── Dockerfile           
├── requirements.txt     
├── API/
│   └── fetch_api.py     ← 
├── DB/
│   ├── Clickhouse_setup.py  ← 
│   └── run_pipeline.py      ← 
├── AI/
│   ├── AI_chatbot.py    ← 
│   ├── Analytics_engine.py  ← 
│   ├── GenAi.py         ← 
│   └── Main_app.py      ← 
