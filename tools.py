from strands import tool
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import json


@tool
def get_stock_price(ticker: str) -> Dict[str, Any]:
    """
    Get the current stock price and basic information for a given ticker.
    
    Args:
        ticker (str): The stock ticker symbol (e.g., 'AAPL', 'MSFT')
    
    Returns:
        Dict containing current price and basic stock information
    """
    try:
        stock = yf.Ticker(ticker.upper())
        info = stock.info
        
        if not info or 'currentPrice' not in info:
            history = stock.history(period="1d")
            if history.empty:
                return {
                    "error": f"Unable to fetch data for ticker: {ticker}",
                    "suggestion": "Please provide a valid stock ticker symbol"
                }
            
            current_price = float(history['Close'].iloc[-1])
        else:
            current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
        
        return {
            "ticker": ticker.upper(),
            "current_price": round(current_price, 2) if current_price else None,
            "company_name": info.get('longName', 'N/A'),
            "market_cap": info.get('marketCap', 'N/A'),
            "volume": info.get('volume', 'N/A'),
            "day_high": info.get('dayHigh', 'N/A'),
            "day_low": info.get('dayLow', 'N/A'),
            "52_week_high": info.get('fiftyTwoWeekHigh', 'N/A'),
            "52_week_low": info.get('fiftyTwoWeekLow', 'N/A')
        }
    except Exception as e:
        return {
            "error": f"Error fetching stock price for {ticker}: {str(e)}",
            "suggestion": "Please check if the ticker symbol is valid"
        }


@tool
def get_historical_data(ticker: str, period: str = "1mo") -> Dict[str, Any]:
    """
    Get historical stock data for analysis.
    
    Args:
        ticker (str): The stock ticker symbol
        period (str): Time period for historical data (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
    
    Returns:
        Dict containing historical data summary and statistics
    """
    try:
        stock = yf.Ticker(ticker.upper())
        history = stock.history(period=period)
        
        if history.empty:
            return {
                "error": f"No historical data available for ticker: {ticker}",
                "suggestion": "Please provide a valid stock ticker symbol"
            }
        
        closing_prices = history['Close']
        
        return {
            "ticker": ticker.upper(),
            "period": period,
            "data_points": len(history),
            "start_date": str(history.index[0].date()),
            "end_date": str(history.index[-1].date()),
            "statistics": {
                "mean_price": round(float(closing_prices.mean()), 2),
                "median_price": round(float(closing_prices.median()), 2),
                "std_deviation": round(float(closing_prices.std()), 2),
                "min_price": round(float(closing_prices.min()), 2),
                "max_price": round(float(closing_prices.max()), 2),
                "price_change": round(float(closing_prices.iloc[-1] - closing_prices.iloc[0]), 2),
                "price_change_percent": round(float(((closing_prices.iloc[-1] - closing_prices.iloc[0]) / closing_prices.iloc[0]) * 100), 2)
            },
            "volatility": round(float(closing_prices.pct_change().std() * np.sqrt(252) * 100), 2),
            "recent_trend": "bullish" if closing_prices.iloc[-1] > closing_prices.iloc[0] else "bearish"
        }
    except Exception as e:
        return {
            "error": f"Error fetching historical data for {ticker}: {str(e)}",
            "suggestion": "Please check if the ticker symbol and period are valid"
        }


@tool
def calculate_forecast(ticker: str, days: int = 30) -> Dict[str, Any]:
    """
    Calculate a stock price forecast based on historical data and simple technical analysis.
    
    Args:
        ticker (str): The stock ticker symbol
        days (int): Number of days to forecast (default: 30)
    
    Returns:
        Dict containing forecast predictions and analysis
    """
    try:
        stock = yf.Ticker(ticker.upper())
        
        # Get historical data for analysis (6 months for better trend analysis)
        history = stock.history(period="6mo")
        
        if history.empty or len(history) < 30:
            return {
                "error": f"Insufficient historical data for ticker: {ticker}",
                "suggestion": "Please provide a ticker with at least 30 days of historical data"
            }
        
        closing_prices = history['Close']
        current_price = float(closing_prices.iloc[-1])
        
        # Calculate moving averages
        ma_20 = closing_prices.rolling(window=20, min_periods=1).mean()
        ma_50 = closing_prices.rolling(window=50, min_periods=1).mean()
        
        # Calculate trend using linear regression
        x = np.arange(len(closing_prices))
        y = closing_prices.values
        z = np.polyfit(x, y, 1)
        slope = z[0]
        
        # Calculate daily return statistics
        daily_returns = closing_prices.pct_change().dropna()
        avg_daily_return = daily_returns.mean()
        daily_volatility = daily_returns.std()
        
        # Simple forecast using trend and volatility
        # Project forward based on historical trend
        forecast_price = current_price * (1 + avg_daily_return * days)
        
        # Add volatility-based confidence intervals
        std_dev = daily_volatility * np.sqrt(days) * current_price
        upper_bound = forecast_price + std_dev
        lower_bound = forecast_price - std_dev
        
        # Determine trend strength and confidence
        trend_strength = abs(slope) / current_price
        if trend_strength < 0.001:
            trend = "neutral"
            confidence = "low"
        elif trend_strength < 0.005:
            trend = "moderate bullish" if slope > 0 else "moderate bearish"
            confidence = "moderate"
        else:
            trend = "strong bullish" if slope > 0 else "strong bearish"
            confidence = "moderate"
        
        # Adjust confidence based on volatility
        if daily_volatility > 0.03:
            confidence = "low"
        elif daily_volatility < 0.01:
            confidence = "high" if confidence == "moderate" else confidence
        
        # Technical indicators for additional context
        rsi = calculate_rsi(closing_prices)
        macd_signal = "buy" if ma_20.iloc[-1] > ma_50.iloc[-1] else "sell"
        
        return {
            "ticker": ticker.upper(),
            "forecast_period_days": days,
            "current_price": round(current_price, 2),
            "forecast": {
                f"{days}_day_prediction": round(forecast_price, 2),
                "upper_bound": round(upper_bound, 2),
                "lower_bound": round(lower_bound, 2),
                "expected_return_percent": round(((forecast_price - current_price) / current_price) * 100, 2)
            },
            "trend_analysis": {
                "trend": trend,
                "confidence": confidence,
                "daily_volatility_percent": round(daily_volatility * 100, 2),
                "trend_slope": round(slope, 4)
            },
            "technical_indicators": {
                "rsi": round(rsi, 2) if rsi else "N/A",
                "ma_20": round(ma_20.iloc[-1], 2),
                "ma_50": round(ma_50.iloc[-1], 2) if len(ma_50) >= 50 else "N/A",
                "macd_signal": macd_signal
            },
            "factors": get_forecast_factors(trend, confidence, rsi, macd_signal),
            "disclaimer": "This forecast is based on historical data and simple technical analysis. It should not be used as the sole basis for investment decisions."
        }
        
    except Exception as e:
        return {
            "error": f"Error calculating forecast for {ticker}: {str(e)}",
            "suggestion": "Please check if the ticker symbol is valid and has sufficient historical data"
        }


def calculate_rsi(prices: pd.Series, period: int = 14) -> Optional[float]:
    """Calculate the Relative Strength Index (RSI)."""
    try:
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        if loss.iloc[-1] == 0:
            return 100.0
        
        rs = gain.iloc[-1] / loss.iloc[-1]
        rsi = 100 - (100 / (1 + rs))
        return float(rsi)
    except:
        return None


def get_forecast_factors(trend: str, confidence: str, rsi: float, macd_signal: str) -> list:
    """Generate factors explaining the forecast."""
    factors = []
    
    if "bullish" in trend:
        factors.append("Positive price trend observed in historical data")
    elif "bearish" in trend:
        factors.append("Negative price trend observed in historical data")
    else:
        factors.append("Neutral price trend with sideways movement")
    
    if confidence == "high":
        factors.append("Low volatility suggests stable price movement")
    elif confidence == "low":
        factors.append("High volatility indicates uncertain price movement")
    
    if isinstance(rsi, (int, float)):
        if rsi > 70:
            factors.append("RSI indicates overbought conditions")
        elif rsi < 30:
            factors.append("RSI indicates oversold conditions")
        else:
            factors.append("RSI in neutral territory")
    
    if macd_signal == "buy":
        factors.append("Moving averages suggest upward momentum")
    else:
        factors.append("Moving averages suggest downward pressure")
    
    return factors


@tool
def analyze_stock(ticker: str) -> Dict[str, Any]:
    """
    Perform comprehensive stock analysis including current price, historical data, and forecast.
    
    Args:
        ticker (str): The stock ticker symbol
    
    Returns:
        Dict containing comprehensive stock analysis
    """
    try:
        # Get all components
        price_data = get_stock_price(ticker)
        if "error" in price_data:
            return price_data
        
        historical_data = get_historical_data(ticker, "3mo")
        forecast_data = calculate_forecast(ticker, 30)
        
        # Combine all analysis
        return {
            "ticker": ticker.upper(),
            "analysis_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "current_status": {
                "price": price_data.get("current_price"),
                "company": price_data.get("company_name"),
                "market_cap": price_data.get("market_cap"),
                "day_range": f"{price_data.get('day_low')} - {price_data.get('day_high')}"
            },
            "historical_summary": {
                "3_month_avg": historical_data.get("statistics", {}).get("mean_price"),
                "3_month_change_percent": historical_data.get("statistics", {}).get("price_change_percent"),
                "volatility": historical_data.get("volatility"),
                "trend": historical_data.get("recent_trend")
            },
            "forecast": forecast_data.get("forecast"),
            "recommendation": generate_recommendation(
                forecast_data.get("forecast", {}).get("expected_return_percent", 0),
                forecast_data.get("trend_analysis", {}).get("confidence", "low"),
                historical_data.get("volatility", 0)
            ),
            "technical_analysis": forecast_data.get("technical_indicators"),
            "risk_factors": forecast_data.get("factors", [])
        }
    except Exception as e:
        return {
            "error": f"Error performing comprehensive analysis for {ticker}: {str(e)}",
            "suggestion": "Please ensure the ticker symbol is valid"
        }


def generate_recommendation(expected_return: float, confidence: str, volatility: float) -> str:
    """Generate an investment recommendation based on analysis."""
    if confidence == "low" or volatility > 50:
        return "HIGH RISK - Consider waiting for more stable conditions"
    elif expected_return > 10 and confidence in ["moderate", "high"]:
        return "POSITIVE OUTLOOK - Potential for gains with moderate risk"
    elif expected_return < -10:
        return "NEGATIVE OUTLOOK - Consider risk management strategies"
    elif -5 <= expected_return <= 5:
        return "NEUTRAL - Limited movement expected, suitable for stable holdings"
    else:
        return "MODERATE - Monitor closely for entry/exit opportunities"