# 🚀 MrCrypto Terminal

**Real-Time Crypto Analytics & AI Explainability Platform**

MrCrypto Terminal is an end-to-end data platform that combines automated market ingestion, quantitative analytics, and LLM-powered explanations inside an interactive terminal interface. The system continuously collects cryptocurrency market data, stores it in ClickHouse, computes technical indicators, and uses Groq-hosted Llama models to answer natural language questions with low latency and cost-efficient routing.

---

## ✨ Features

* ⏱️ **Automated 5-minute ingestion pipeline** using CoinGecko API
* 📊 **Quantitative analytics engine**

  * RSI
  * MACD
  * Bollinger Bands
  * BTC Correlation
  * Support & Resistance Levels
* 🤖 **AI-powered explainability layer**
* 🧠 Intent classification with zero LLM overhead
* 💰 Cost-optimized dual-model architecture
* ⚡ TTL-cached analytics for sub-second repeated queries
* 🔍 Fuzzy coin resolution supporting typos and full names
* 🖥️ Interactive NiceGUI terminal interface
* 🐳 Fully containerized with Docker Compose
* 🔒 XSS sanitization and connection pooling for production reliability

---

# Architecture

```
CoinGecko API
      ↓
 Scheduled Ingestion (5 min)
      ↓
    ClickHouse
      ↓
 Analytics Engine
(RSI, MACD, Bollinger, Correlation)
      ↓
Intent Router + Coin Resolver
      ↓
┌───────────────────────────────┐
│ Single Coin → Llama 3.1 8B    │
│ Multi Coin  → Llama 3.3 70B   │
└───────────────────────────────┘
      ↓
      Groq API
      ↓
 NiceGUI Terminal
```

---

## Tech Stack

### Data Layer

* CoinGecko API
* ClickHouse

### AI Layer

* LangChain
* Groq API
* Llama 3.1-8B
* Llama 3.3-70B

### Backend

* Python
* FuzzyWuzzy
* Scheduled ingestion jobs
* Shared connection pooling

### Frontend

* NiceGUI

### Deployment

* Docker
* Docker Compose

---

# Intelligent Query Routing

The system classifies every user request into four categories before invoking any LLM:

| Intent     | Example                  |
| ---------- | ------------------------ |
| ANALYSIS   | "Analyze Bitcoin"        |
| COMPARISON | "BTC vs ETH"             |
| AMBIGUOUS  | "Tell me about Sol"      |
| OFF_TOPIC  | "Who won the World Cup?" |

This rule-based layer avoids unnecessary LLM calls and reduces latency and API costs.

---

# Smart Coin Resolution

Users can search assets using:

* Symbols (`BTC`)
* Full names (`Bitcoin`)
* Misspellings (`Bitcion`)
* Partial names (`Etherem`)

Powered by **FuzzyWuzzy**, the resolver maps inputs across 10 supported assets without requiring exact matches.

---

# Quantitative Analytics

The analytics engine operates on 30 days of historical data stored in ClickHouse and computes:

* Relative Strength Index (RSI)
* Moving Average Convergence Divergence (MACD)
* Bollinger Bands
* BTC Correlation Matrix
* Support and Resistance Levels

These metrics are injected into prompts so LLM responses are grounded in actual market data rather than generic explanations.

---

# Cost-Optimized AI Design

### Single Coin Analysis

Uses **Llama 3.1-8B** through Groq for fast and inexpensive synthesis.

### Multi-Coin Comparison

Uses **Llama 3.3-70B** for richer comparative reasoning when deeper analysis is required.

This split minimizes token costs while preserving answer quality.

---

# Performance Optimizations

* TTL caching for repeated analytics requests
* Shared ClickHouse connections
* Dockerized services
* Double-send guard protection
* XSS sanitization
* Low-latency response generation

---

# Repository Structure

```
Mr_Crypto/
│
├── AI/
├── API/
├── Db/
├── metadata/
├── preprocessed_configs/
├── data/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

# Example Queries

```
Analyze Bitcoin
```

```
Compare BTC and ETH
```

```
Is Solana overbought?
```

```
Show support and resistance levels for XRP
```

```
How correlated is Ethereum with Bitcoin?
```

---

## Future Improvements

* Streaming WebSocket market feeds
* More technical indicators
* Portfolio tracking
* Alerting system
* Multi-user support
* Historical backtesting
* RAG-based market news explanations

---

## Author

**Vedant Brahmbhatt**

GitHub: https://github.com/Vedantgitbot

Building data platforms and AI systems that combine analytics with explainability.
