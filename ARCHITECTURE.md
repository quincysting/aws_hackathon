# Stock Forecast Agent - System Architecture

## High-Level Architecture

```
                             ┌─────────────────────┐
                             │     End User        │
                             │   (Stock Analyst)   │
                             └──────────┬──────────┘
                                        │
                              ┌─────────▼─────────┐
                              │   Input Methods   │
                              │ • Python Script   │
                              │ • AWS Portal      │
                              │ • REST API        │
                              └─────────┬─────────┘
                                        │
                    ┌───────────────────▼───────────────────┐
                    │         AWS Bedrock AgentCore         │
                    │    arn:...runtime/stock_analysis-...  │
                    │                                       │
                    │  ┌─────────────────────────────────┐  │
                    │  │       Request Router            │  │
                    │  │   • Payload Validation          │  │
                    │  │   • Session Management          │  │
                    │  │   • Model Invocation            │  │
                    │  └─────────────┬───────────────────┘  │
                    └────────────────┼───────────────────────┘
                                     │
                    ┌────────────────▼───────────────────┐
                    │      Claude 3.5 Sonnet Model      │
                    │  anthropic.claude-3-5-sonnet-...  │
                    │         • Natural Language        │
                    │         • Tool Orchestration      │
                    │         • Response Generation     │
                    └────────────────┬───────────────────┘
                                     │
                    ┌────────────────▼───────────────────┐
                    │         Docker Container          │
                    │          (ARM64 Linux)            │
                    │                                   │
                    │  ┌─────────────────────────────┐  │
                    │  │       FastAPI Server        │  │
                    │  │    • /ping (health)         │  │
                    │  │    • /invocations (main)    │  │
                    │  └─────────────┬───────────────┘  │
                    │                │                   │
                    │  ┌─────────────▼───────────────┐  │
                    │  │      Strands Agent          │  │
                    │  │   • Tool Orchestration      │  │
                    │  │   • Workflow Management     │  │
                    │  │   • Error Handling          │  │
                    │  └─────────────┬───────────────┘  │
                    └────────────────┼───────────────────┘
                                     │
        ┌────────────────────────────┼────────────────────────────┐
        │                            │                            │
┌───────▼───────┐        ┌──────────▼──────────┐        ┌───────▼───────┐
│   Tools.py    │        │   Forecaster.py     │        │  Data Layer   │
│               │        │                     │        │               │
│ @tool         │        │ StockForecaster     │        │ ┌───────────┐ │
│ functions:    │        │ class:              │        │ │ yfinance  │ │
│               │        │                     │        │ │   API     │ │
│• get_stock_   │        │• linear_trend()     │        │ └───────────┘ │
│  price()      │        │• monte_carlo()      │        │               │
│• get_         │        │• moving_average()   │        │ ┌───────────┐ │
│  historical_  │        │• ensemble_forecast()│        │ │Yahoo      │ │
│  data()       │        │• confidence_score() │        │ │Finance    │ │
│• calculate_   │        │                     │        │ │Market Data│ │
│  forecast()   │        │Technical Analysis:  │        │ └───────────┘ │
│• analyze_     │        │• RSI calculation    │        │               │
│  stock()      │        │• MACD signals       │        │ ┌───────────┐ │
│               │        │• Moving averages    │        │ │pandas     │ │
│               │        │• Bollinger bands    │        │ │numpy      │ │
│               │        │                     │        │ │scipy      │ │
└───────────────┘        └─────────────────────┘        │ │sklearn    │ │
                                                        │ └───────────┘ │
                                                        └───────────────┘
```

## Data Flow Diagram

```
User Request
     │
     ▼
┌─────────────┐    JSON Payload     ┌─────────────────┐
│   Client    │──────────────────▶  │  Bedrock        │
│   (Python/  │    {                │  AgentCore      │
│    Portal)  │     "input": "AAPL" │                 │
└─────────────┘    }                └─────────┬───────┘
                                              │
                                              ▼
                                   ┌─────────────────┐
                                   │  Claude Model   │
                                   │  Processes      │
                                   │  Request        │
                                   └─────────┬───────┘
                                            │
                                            ▼
                                   ┌─────────────────┐
                                   │  Strands Agent  │
                                   │  Orchestrates   │
                                   │  Tool Calls     │
                                   └─────────┬───────┘
                                            │
                          ┌─────────────────┼─────────────────┐
                          │                 │                 │
                          ▼                 ▼                 ▼
               ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
               │get_stock_price()│ │get_historical() │ │calculate_       │
               │                 │ │                 │ │forecast()       │
               │• Fetch current  │ │• 3-month data   │ │• ML algorithms  │
               │  price          │ │• OHLC values    │ │• Trend analysis │
               │• Company info   │ │• Volume data    │ │• Risk metrics   │
               │• Market cap     │ │                 │ │                 │
               └─────────┬───────┘ └─────────┬───────┘ └─────────┬───────┘
                         │                   │                   │
                         ▼                   ▼                   ▼
                    ┌─────────────────────────────────────────────────────┐
                    │              YFinance API                           │
                    │     • Real-time stock prices                       │
                    │     • Historical market data                       │
                    │     • Company fundamentals                         │
                    │     • Technical indicators                         │
                    └─────────────────┬───────────────────────────────────┘
                                      │
                                      ▼
                    ┌─────────────────────────────────────────────────────┐
                    │            Data Processing                          │
                    │  • pandas DataFrames                               │
                    │  • numpy calculations                              │
                    │  • Technical analysis (RSI, MACD, MA)             │
                    │  • Statistical modeling                           │
                    └─────────────────┬───────────────────────────────────┘
                                      │
                                      ▼
                    ┌─────────────────────────────────────────────────────┐
                    │         Response Aggregation                       │
                    │                                                    │
                    │  {                                                 │
                    │    "ticker": "AAPL",                             │
                    │    "current_status": {...},                      │
                    │    "historical_summary": {...},                  │
                    │    "forecast": {...},                            │
                    │    "technical_analysis": {...},                  │
                    │    "trading_signals": {...},                     │
                    │    "recommendation": "..."                       │
                    │  }                                                 │
                    └─────────────────┬───────────────────────────────────┘
                                      │
                                      ▼
                              Return to User
```

## Component Breakdown

### 1. AWS Bedrock AgentCore
- **Runtime ARN**: `arn:aws:bedrock-agentcore:us-west-2:534831852398:runtime/stock_analysis-SDlddo218l`
- **Model**: Claude 3.5 Sonnet (`anthropic.claude-3-5-sonnet-20241022-v2:0`)
- **Region**: us-west-2
- **Endpoint**: DEFAULT

### 2. Docker Container (ARM64)
- **Base Image**: `python:3.10-slim`
- **Platform**: `linux/arm64`
- **Port**: 8080
- **Dependencies**: FastAPI, Strands, yfinance, pandas, numpy

### 3. Strands Agent Framework
- **Tools**: Decorated with `@tool` for automatic registration
- **Orchestration**: Intelligent tool selection and chaining
- **Error Handling**: Graceful fallbacks and retry logic

### 4. Analysis Tools (`tools.py`)
```python
@tool
def get_stock_price(ticker: str) -> Dict[str, Any]
@tool
def get_historical_data(ticker: str, period: str = "3mo") -> Dict[str, Any]
@tool
def calculate_forecast(ticker: str, days: int = 30) -> Dict[str, Any]
@tool
def analyze_stock(ticker: str) -> Dict[str, Any]
```

### 5. Forecasting Engine (`forecaster.py`)
- **Linear Trend**: Regression-based price prediction
- **Monte Carlo**: Stochastic simulation for risk assessment
- **Moving Average**: Trend following approach
- **Ensemble**: Combined forecast from multiple methods

## Security & Performance

### Security Features
- ✅ **Input Validation**: Ticker symbol validation
- ✅ **Session Management**: Unique session IDs (33+ chars)
- ✅ **Rate Limiting**: Implicit via Bedrock quotas
- ✅ **Error Sanitization**: Safe error responses

### Performance Metrics
- **Response Time**: ~2.5 seconds average
- **Data Refresh**: Real-time via yfinance
- **Concurrency**: Handled by Bedrock AgentCore
- **Caching**: Market data cached by yfinance

## Monitoring & Logging

### AWS CloudWatch Integration
- Request/response logging
- Error tracking and alerts
- Performance metrics
- Usage analytics

### Debug Capabilities
- Session ID tracking
- Request ID correlation
- Tool execution tracing
- Error stack traces

## Scalability Considerations

1. **Horizontal Scaling**: Managed by AWS Bedrock
2. **Data Source Limits**: YFinance API rate limits
3. **Model Throughput**: Claude 3.5 Sonnet capacity
4. **Container Resources**: ARM64 optimization

---
*Architecture designed for production deployment on AWS Bedrock AgentCore with comprehensive stock analysis capabilities.*