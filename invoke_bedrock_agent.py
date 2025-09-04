#!/usr/bin/env python
"""
Invoke the deployed Bedrock AgentCore runtime for stock analysis.
"""

import boto3
import json
import time
from datetime import datetime
from typing import Dict, Any

# Configuration
AGENT_RUNTIME_ARN = 'arn:aws:bedrock-agentcore:us-west-2:534831852398:runtime/stock_analysis-SDlddo218l'
REGION = 'us-west-2'

def invoke_stock_agent(ticker: str, session_id: str = None) -> Dict[str, Any]:
    """
    Invoke the Bedrock AgentCore runtime for stock analysis.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL')
        session_id: Optional session ID for conversation continuity
    
    Returns:
        Agent response with stock analysis
    """
    try:
        # Initialize Bedrock AgentCore client
        client = boto3.client('bedrock-agentcore', region_name=REGION)
        
        # Create session ID if not provided (must be at least 33 chars)
        if not session_id:
            import uuid
            session_id = f"session-{int(time.time())}-{str(uuid.uuid4())}"
        
        # Prepare the payload
        payload = json.dumps({
            "input": ticker.upper(),
            "user_id": "stock_user_001",
            "session_id": session_id,
            "identity_id": f"stock-user-{int(time.time())}",
            "context": {
                "analysis_type": "stock_forecast",
                "timezone": "America/New_York",
                "language": "en"
            }
        })
        
        print(f"Invoking Bedrock AgentCore runtime...")
        print(f"   Agent ARN: {AGENT_RUNTIME_ARN}")
        print(f"   Ticker: {ticker.upper()}")
        print(f"   Session ID: {session_id}")
        print(f"   Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Invoke the AgentCore runtime
        response = client.invoke_agent_runtime(
            agentRuntimeArn=AGENT_RUNTIME_ARN,
            runtimeSessionId=session_id,
            payload=payload,
            qualifier="DEFAULT"
        )
        
        print("Successfully invoked agent!")
        
        # Parse response
        if 'response' in response:
            # Read the response body
            response_body = response['response'].read()
            response_data = json.loads(response_body)
            
            return {
                "success": True,
                "response": {"output": response_data},
                "session_id": session_id,
                "response_metadata": {
                    "status_code": response['ResponseMetadata']['HTTPStatusCode'],
                    "request_id": response['ResponseMetadata']['RequestId']
                }
            }
        
        return {
            "success": False,
            "error": "No response received from AgentCore",
            "raw_response": response
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "ticker": ticker,
            "session_id": session_id
        }


def format_stock_analysis(result: Dict[str, Any]) -> None:
    """Format and display the stock analysis results."""
    if not result.get("success"):
        print(f"ERROR: {result.get('error', 'Unknown error')}")
        return
    
    response = result.get("response", {})
    output = response.get("output", {})
    
    if "error" in output:
        print(f"Agent Error: {output['error']}")
        return
    
    # Extract key information
    ticker = output.get("ticker", "N/A")
    analysis = output.get("analysis", {})
    
    print("="*80)
    print(f"STOCK FORECAST ANALYSIS: {ticker}")
    print("="*80)
    
    # Current Status
    if "current_status" in analysis:
        current = analysis["current_status"]
        print(f"\nCURRENT STATUS:")
        print(f"   Company: {current.get('company', 'N/A')}")
        print(f"   Current Price: ${current.get('price', 'N/A')}")
        print(f"   Market Cap: ${current.get('market_cap', 'N/A'):,}" if current.get('market_cap') != 'N/A' else "   Market Cap: N/A")
        print(f"   Day Range: {current.get('day_range', 'N/A')}")
    
    # Historical Summary
    if "historical_summary" in analysis:
        historical = analysis["historical_summary"]
        print(f"\nHISTORICAL ANALYSIS:")
        print(f"   3-Month Average: ${historical.get('3_month_avg', 'N/A')}")
        print(f"   3-Month Change: {historical.get('3_month_change_percent', 'N/A')}%")
        print(f"   Volatility: {historical.get('volatility', 'N/A')}%")
        print(f"   Trend: {historical.get('trend', 'N/A').title()}")
    
    # Forecast
    if "forecast" in analysis:
        forecast = analysis["forecast"]
        print(f"\n30-DAY FORECAST:")
        print(f"   Predicted Price: ${forecast.get('30_day_prediction', 'N/A')}")
        print(f"   Expected Return: {forecast.get('expected_return_percent', 'N/A')}%")
        print(f"   Upper Bound: ${forecast.get('upper_bound', 'N/A')}")
        print(f"   Lower Bound: ${forecast.get('lower_bound', 'N/A')}")
    
    # Technical Analysis
    if "technical_analysis" in analysis:
        technical = analysis["technical_analysis"]
        print(f"\nTECHNICAL INDICATORS:")
        print(f"   RSI: {technical.get('rsi', 'N/A')}")
        print(f"   20-Day MA: ${technical.get('ma_20', 'N/A')}")
        print(f"   50-Day MA: ${technical.get('ma_50', 'N/A')}")
        print(f"   MACD Signal: {technical.get('macd_signal', 'N/A').upper()}")
    
    # Trading Signals
    if "trading_signals" in output:
        signals = output["trading_signals"]
        print(f"\nTRADING SIGNALS:")
        print(f"   Primary Signal: {signals.get('primary_signal', 'N/A').replace('_', ' ').title()}")
        if signals.get('all_signals'):
            print(f"   All Signals: {', '.join([s.replace('_', ' ').title() for s in signals['all_signals']])}")
    
    # Recommendation
    recommendation = analysis.get("recommendation", "N/A")
    print(f"\nRECOMMENDATION:")
    print(f"   {recommendation}")
    
    # Metadata
    print(f"\nRESPONSE METADATA:")
    print(f"   Session ID: {result.get('session_id', 'N/A')}")
    print(f"   Request ID: {result.get('response_metadata', {}).get('request_id', 'N/A')}")
    print(f"   Analysis Date: {analysis.get('analysis_date', 'N/A')}")
    
    print("\n" + "="*80)
    print("DISCLAIMER: This analysis is for informational purposes only.")
    print("   Not financial advice. Always conduct your own research.")
    print("="*80)


def main():
    """Main function to test the agent with different stocks."""
    import sys
    
    # Test with command line argument or default to AAPL
    ticker = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    
    print(f"\nBEDROCK AGENTCORE STOCK ANALYSIS")
    print(f"   Testing with ticker: {ticker.upper()}")
    print(f"   Region: {REGION}")
    print()
    
    # Invoke the agent
    start_time = time.time()
    result = invoke_stock_agent(ticker)
    end_time = time.time()
    
    # Display results
    format_stock_analysis(result)
    
    print(f"\nResponse Time: {end_time - start_time:.2f} seconds")
    
    if result.get("success"):
        print("Agent invocation completed successfully!")
        return 0
    else:
        print("Agent invocation failed.")
        return 1


if __name__ == "__main__":
    exit(main())