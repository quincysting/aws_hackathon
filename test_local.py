#!/usr/bin/env python
"""
Local testing script for Stock Forecast Agent.
Tests all tools and agent functionality before deployment.
"""

import sys
import json
import logging
from datetime import datetime
from typing import Dict, List, Any

# Add parent directory to path
sys.path.append('.')

from tools import (
    get_stock_price, 
    get_historical_data, 
    calculate_forecast, 
    analyze_stock
)
from forecaster import StockForecaster
from agent import run_local_agent
import yfinance as yf

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Test configuration
TEST_TICKERS = ["AAPL", "MSFT", "GOOGL", "TSLA", "INVALID_TICKER"]
VALID_TICKERS = ["AAPL", "MSFT", "GOOGL", "TSLA"]

class TestResults:
    """Store and display test results."""
    
    def __init__(self):
        self.passed = []
        self.failed = []
        self.errors = []
    
    def add_pass(self, test_name: str, details: str = ""):
        self.passed.append({"test": test_name, "details": details})
        logger.info(f"PASS: {test_name}")
    
    def add_fail(self, test_name: str, reason: str):
        self.failed.append({"test": test_name, "reason": reason})
        logger.error(f"FAIL: {test_name} - {reason}")
    
    def add_error(self, test_name: str, error: str):
        self.errors.append({"test": test_name, "error": error})
        logger.error(f"ERROR: {test_name} - {error}")
    
    def display_summary(self):
        """Display test summary."""
        total = len(self.passed) + len(self.failed) + len(self.errors)
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        print(f"Total Tests: {total}")
        print(f"Passed: {len(self.passed)} ({len(self.passed)/total*100:.1f}%)")
        print(f"Failed: {len(self.failed)} ({len(self.failed)/total*100:.1f}%)")
        print(f"Errors: {len(self.errors)} ({len(self.errors)/total*100:.1f}%)")
        
        if self.failed:
            print("\nFailed Tests:")
            for fail in self.failed:
                print(f"  - {fail['test']}: {fail['reason']}")
        
        if self.errors:
            print("\nTest Errors:")
            for error in self.errors:
                print(f"  - {error['test']}: {error['error']}")
        
        return len(self.failed) == 0 and len(self.errors) == 0


def test_get_stock_price(results: TestResults):
    """Test the get_stock_price tool."""
    logger.info("\n=== Testing get_stock_price ===")
    
    # Test valid ticker
    for ticker in VALID_TICKERS[:2]:
        try:
            result = get_stock_price(ticker)
            if "error" not in result and result.get("current_price"):
                results.add_pass(f"get_stock_price({ticker})", 
                               f"Price: ${result['current_price']}")
            else:
                results.add_fail(f"get_stock_price({ticker})", 
                               result.get("error", "No price returned"))
        except Exception as e:
            results.add_error(f"get_stock_price({ticker})", str(e))
    
    # Test invalid ticker
    try:
        result = get_stock_price("INVALID_TICKER_XYZ")
        if "error" in result:
            results.add_pass("get_stock_price(invalid)", "Correctly handled invalid ticker")
        else:
            results.add_fail("get_stock_price(invalid)", "Should return error for invalid ticker")
    except Exception as e:
        results.add_error("get_stock_price(invalid)", str(e))


def test_get_historical_data(results: TestResults):
    """Test the get_historical_data tool."""
    logger.info("\n=== Testing get_historical_data ===")
    
    test_periods = ["1mo", "3mo", "6mo"]
    
    for period in test_periods:
        try:
            result = get_historical_data("AAPL", period)
            if "error" not in result and result.get("statistics"):
                stats = result["statistics"]
                results.add_pass(f"get_historical_data(AAPL, {period})", 
                               f"Mean: ${stats.get('mean_price', 'N/A')}")
            else:
                results.add_fail(f"get_historical_data(AAPL, {period})", 
                               result.get("error", "No data returned"))
        except Exception as e:
            results.add_error(f"get_historical_data(AAPL, {period})", str(e))


def test_calculate_forecast(results: TestResults):
    """Test the calculate_forecast tool."""
    logger.info("\n=== Testing calculate_forecast ===")
    
    forecast_days = [7, 30, 60]
    
    for days in forecast_days:
        try:
            result = calculate_forecast("MSFT", days)
            if "error" not in result and result.get("forecast"):
                forecast = result["forecast"]
                prediction = forecast.get(f"{days}_day_prediction")
                confidence = result.get("trend_analysis", {}).get("confidence", "N/A")
                results.add_pass(f"calculate_forecast(MSFT, {days})", 
                               f"Prediction: ${prediction}, Confidence: {confidence}")
            else:
                results.add_fail(f"calculate_forecast(MSFT, {days})", 
                               result.get("error", "No forecast returned"))
        except Exception as e:
            results.add_error(f"calculate_forecast(MSFT, {days})", str(e))


def test_analyze_stock(results: TestResults):
    """Test the comprehensive analyze_stock tool."""
    logger.info("\n=== Testing analyze_stock ===")
    
    for ticker in ["AAPL", "GOOGL"]:
        try:
            result = analyze_stock(ticker)
            if "error" not in result:
                has_current = "current_status" in result
                has_historical = "historical_summary" in result
                has_forecast = "forecast" in result
                has_recommendation = "recommendation" in result
                
                if all([has_current, has_historical, has_forecast, has_recommendation]):
                    results.add_pass(f"analyze_stock({ticker})", 
                                   f"Recommendation: {result.get('recommendation', 'N/A')}")
                else:
                    missing = []
                    if not has_current: missing.append("current_status")
                    if not has_historical: missing.append("historical_summary")
                    if not has_forecast: missing.append("forecast")
                    if not has_recommendation: missing.append("recommendation")
                    results.add_fail(f"analyze_stock({ticker})", 
                                   f"Missing fields: {', '.join(missing)}")
            else:
                results.add_fail(f"analyze_stock({ticker})", 
                               result.get("error", "Analysis failed"))
        except Exception as e:
            results.add_error(f"analyze_stock({ticker})", str(e))


def test_stock_forecaster(results: TestResults):
    """Test the StockForecaster class."""
    logger.info("\n=== Testing StockForecaster ===")
    
    try:
        forecaster = StockForecaster()
        stock = yf.Ticker("AAPL")
        history = stock.history(period="6mo")
        
        if not history.empty:
            # Test forecast generation
            forecast = forecaster.forecast_prices(history['Close'], 30)
            if forecast and "forecasts" in forecast:
                results.add_pass("StockForecaster.forecast_prices", 
                               f"Generated {len(forecast['forecasts'])} forecast methods")
            else:
                results.add_fail("StockForecaster.forecast_prices", 
                               "No forecasts generated")
            
            # Test signal generation
            signals = forecaster.generate_signals(history['Close'])
            if signals and "primary_signal" in signals:
                results.add_pass("StockForecaster.generate_signals", 
                               f"Signal: {signals['primary_signal']}")
            else:
                results.add_fail("StockForecaster.generate_signals", 
                               "No signals generated")
        else:
            results.add_fail("StockForecaster", "Unable to fetch historical data")
            
    except Exception as e:
        results.add_error("StockForecaster", str(e))


def test_agent_response(results: TestResults):
    """Test the full agent response."""
    logger.info("\n=== Testing Agent Response ===")
    
    try:
        # Import here to avoid circular imports
        from agent import stock_agent
        
        # Test with a simple query
        test_prompt = "What is the current price of AAPL?"
        response = stock_agent(test_prompt)
        
        if response and hasattr(response, 'message'):
            results.add_pass("Agent basic query", "Agent responded successfully")
            logger.info(f"Agent response sample: {response.message[:200]}...")
        else:
            results.add_fail("Agent basic query", "No response from agent")
            
        # Test with forecast request
        forecast_prompt = "Please analyze MSFT and provide a 30-day forecast"
        response = stock_agent(forecast_prompt)
        
        if response and hasattr(response, 'message'):
            results.add_pass("Agent forecast query", "Agent provided forecast")
        else:
            results.add_fail("Agent forecast query", "No forecast from agent")
            
    except Exception as e:
        results.add_error("Agent tests", str(e))


def test_error_handling(results: TestResults):
    """Test error handling for edge cases."""
    logger.info("\n=== Testing Error Handling ===")
    
    # Test empty ticker
    try:
        result = get_stock_price("")
        if "error" in result or result.get("current_price") is None:
            results.add_pass("Empty ticker handling", "Correctly handled empty ticker")
        else:
            results.add_fail("Empty ticker handling", "Should handle empty ticker")
    except:
        results.add_pass("Empty ticker handling", "Exception handled for empty ticker")
    
    # Test very long ticker
    try:
        result = get_stock_price("VERYLONGTICKERSYMBOL")
        if "error" in result:
            results.add_pass("Long ticker handling", "Correctly handled long ticker")
        else:
            results.add_fail("Long ticker handling", "Should handle long ticker")
    except:
        results.add_pass("Long ticker handling", "Exception handled for long ticker")
    
    # Test special characters
    try:
        result = get_stock_price("AAPL$#@")
        if "error" in result or result.get("current_price") is None:
            results.add_pass("Special chars handling", "Correctly handled special characters")
        else:
            results.add_fail("Special chars handling", "Should handle special characters")
    except:
        results.add_pass("Special chars handling", "Exception handled for special characters")


def run_performance_test(results: TestResults):
    """Test performance and response times."""
    logger.info("\n=== Testing Performance ===")
    
    import time
    
    # Test single tool performance
    start = time.time()
    result = get_stock_price("AAPL")
    elapsed = time.time() - start
    
    if elapsed < 5:
        results.add_pass("get_stock_price performance", f"Completed in {elapsed:.2f}s")
    else:
        results.add_fail("get_stock_price performance", f"Too slow: {elapsed:.2f}s")
    
    # Test comprehensive analysis performance
    start = time.time()
    result = analyze_stock("MSFT")
    elapsed = time.time() - start
    
    if elapsed < 10:
        results.add_pass("analyze_stock performance", f"Completed in {elapsed:.2f}s")
    else:
        results.add_fail("analyze_stock performance", f"Too slow: {elapsed:.2f}s")


def main():
    """Main test runner."""
    print("\n" + "="*60)
    print("STOCK FORECAST AGENT - LOCAL TESTING")
    print("="*60)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    results = TestResults()
    
    # Run all tests
    test_get_stock_price(results)
    test_get_historical_data(results)
    test_calculate_forecast(results)
    test_analyze_stock(results)
    test_stock_forecaster(results)
    test_error_handling(results)
    run_performance_test(results)
    test_agent_response(results)
    
    # Display results
    success = results.display_summary()
    
    if success:
        print("\nAll tests passed! Agent is ready for deployment.")
        return 0
    else:
        print("\nSome tests failed. Please fix issues before deployment.")
        return 1


if __name__ == "__main__":
    sys.exit(main())