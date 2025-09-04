import logging
from strands import Agent
from tools import (
    get_stock_price, 
    get_historical_data, 
    calculate_forecast, 
    analyze_stock
)
from forecaster import StockForecaster
import yfinance as yf
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import json
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger(__name__)

# Enable Strands debug logging
logging.getLogger("strands").setLevel(logging.DEBUG)

# Create the Strands agent for local use
stock_agent = Agent(
    model="anthropic.claude-3-5-sonnet-20241022-v2:0",
    tools=[
        get_stock_price,
        get_historical_data,
        calculate_forecast,
        analyze_stock
    ],
    system_prompt="""You are a professional stock market analyst with expertise in technical analysis and forecasting.
    
Your role is to:
1. Analyze stock prices and historical data
2. Generate forecasts based on technical indicators
3. Provide clear, actionable insights
4. Always include appropriate disclaimers about investment risks

When analyzing stocks:
- Use the available tools to gather comprehensive data
- Explain your analysis in clear, professional language
- Highlight both opportunities and risks
- Format responses with clear sections and bullet points where appropriate

Remember: Your analysis is for informational purposes only and should not be considered as financial advice."""
)

# FastAPI app for Bedrock AgentCore deployment
app = FastAPI(title="Stock Forecast Agent")

class InvocationRequest(BaseModel):
    input: str
    session_id: Optional[str] = None

class InvocationResponse(BaseModel):
    output: Dict[str, Any]

@app.get("/ping")
async def ping():
    """Health check endpoint required by Bedrock AgentCore."""
    return {"status": "healthy"}

@app.post("/invocations")
async def invoke_agent(request: InvocationRequest) -> InvocationResponse:
    """
    Main invocation endpoint for Bedrock AgentCore.
    Processes stock ticker requests and returns forecasts.
    """
    try:
        ticker = request.input.strip().upper()
        
        # Validate ticker format
        if not ticker or len(ticker) > 10:
            return InvocationResponse(output={
                "error": "Invalid ticker format",
                "suggestion": "Please provide a valid stock ticker symbol (e.g., AAPL, MSFT)"
            })
        
        logger.info(f"Processing request for ticker: {ticker}")
        
        # Perform comprehensive analysis
        analysis = analyze_stock(ticker)
        
        # If error in analysis, return it
        if "error" in analysis:
            return InvocationResponse(output=analysis)
        
        # Get additional forecast data
        forecast_data = calculate_forecast(ticker, 30)
        
        # Use advanced forecaster for additional insights
        forecaster = StockForecaster()
        stock = yf.Ticker(ticker)
        history = stock.history(period="6mo")
        
        if not history.empty:
            advanced_forecast = forecaster.forecast_prices(history['Close'], 30)
            signals = forecaster.generate_signals(history['Close'])
        else:
            advanced_forecast = None
            signals = None
        
        # Combine all results
        output = {
            "ticker": ticker,
            "analysis": analysis,
            "forecast_30_day": forecast_data.get("forecast", {}),
            "advanced_forecast": advanced_forecast if advanced_forecast else "Insufficient data",
            "trading_signals": signals if signals else "Insufficient data",
            "disclaimer": "This analysis is for informational purposes only and should not be considered as financial advice."
        }
        
        logger.info(f"Successfully processed ticker: {ticker}")
        return InvocationResponse(output=output)
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return InvocationResponse(output={
            "error": f"An error occurred while processing the request: {str(e)}",
            "suggestion": "Please try again with a valid stock ticker"
        })

def run_local_agent(ticker: str):
    """
    Run the agent locally for testing.
    
    Args:
        ticker: Stock ticker symbol to analyze
    """
    prompt = f"""Please provide a comprehensive analysis and 30-day forecast for {ticker} stock. 
    Include current price, historical trends, technical indicators, and your forecast with confidence levels."""
    
    response = stock_agent(prompt)
    return response

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Run as standalone agent with command line argument
        ticker = sys.argv[1]
        logger.info(f"Running local agent for ticker: {ticker}")
        result = run_local_agent(ticker)
        print(result.message if hasattr(result, 'message') else result)
    else:
        # Run as FastAPI server
        logger.info("Starting FastAPI server on port 8080")
        uvicorn.run(app, host="0.0.0.0", port=8080)