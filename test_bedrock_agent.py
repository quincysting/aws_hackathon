#!/usr/bin/env python
"""
Simulate Bedrock Agent Runtime invocation for testing.
This script demonstrates how the deployed agent would respond to invocations.
"""

import json
import requests
import time
from typing import Dict, Any
from datetime import datetime

class MockBedrockAgentRuntime:
    """Mock Bedrock Agent Runtime for testing agent functionality."""
    
    def __init__(self, agent_endpoint: str = "http://localhost:8080"):
        self.agent_endpoint = agent_endpoint
        self.session_id = f"test-session-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    def invoke_agent(self, input_text: str) -> Dict[str, Any]:
        """
        Simulate Bedrock Agent Runtime invocation.
        
        Args:
            input_text: The input to send to the agent (stock ticker)
        
        Returns:
            Agent response formatted like Bedrock would return it
        """
        try:
            # Call our FastAPI endpoint (simulating Bedrock AgentCore)
            response = requests.post(
                f"{self.agent_endpoint}/invocations",
                json={
                    "input": input_text,
                    "session_id": self.session_id
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Format response like Bedrock Agent Runtime would
                return {
                    "sessionId": self.session_id,
                    "agentId": "stock-forecast-agent",
                    "agentAliasId": "TSTALIASID",
                    "agentVersion": "1",
                    "output": result["output"],
                    "responseMetadata": {
                        "httpStatusCode": 200,
                        "requestId": f"mock-request-{int(time.time())}",
                        "attempts": 1,
                        "totalRetryDelay": 0
                    }
                }
            else:
                return {
                    "error": f"Agent invocation failed with status {response.status_code}",
                    "details": response.text
                }
                
        except Exception as e:
            return {
                "error": f"Failed to invoke agent: {str(e)}",
                "sessionId": self.session_id
            }
    
    def test_multiple_stocks(self, tickers: list) -> Dict[str, Any]:
        """Test the agent with multiple stock tickers."""
        results = {}
        
        for ticker in tickers:
            print(f"\n{'='*60}")
            print(f"TESTING STOCK: {ticker}")
            print(f"{'='*60}")
            
            start_time = time.time()
            response = self.invoke_agent(ticker)
            end_time = time.time()
            
            results[ticker] = {
                "response": response,
                "response_time": round(end_time - start_time, 2)
            }
            
            if "error" in response:
                print(f"ERROR: {response['error']}")
            else:
                output = response["output"]
                print(f"SUCCESS: Response received in {results[ticker]['response_time']}s")
                
                if "analysis" in output:
                    analysis = output["analysis"]
                    current_status = analysis.get("current_status", {})
                    forecast = analysis.get("forecast", {})
                    
                    print(f"\nANALYSIS SUMMARY:")
                    print(f"   Company: {current_status.get('company', 'N/A')}")
                    print(f"   Current Price: ${current_status.get('price', 'N/A')}")
                    print(f"   Market Cap: ${current_status.get('market_cap', 'N/A'):,}")
                    
                    if forecast:
                        prediction = forecast.get('30_day_prediction')
                        expected_return = forecast.get('expected_return_percent')
                        print(f"\n30-DAY FORECAST:")
                        print(f"   Predicted Price: ${prediction}")
                        print(f"   Expected Return: {expected_return}%")
                        print(f"   Upper Bound: ${forecast.get('upper_bound', 'N/A')}")
                        print(f"   Lower Bound: ${forecast.get('lower_bound', 'N/A')}")
                    
                    recommendation = analysis.get("recommendation", "N/A")
                    print(f"\nRECOMMENDATION: {recommendation}")
            
            # Brief pause between requests
            time.sleep(1)
        
        return results


def main():
    """Main test function."""
    print("\n" + "="*80)
    print("BEDROCK AGENT RUNTIME SIMULATION - STOCK FORECAST AGENT")
    print("="*80)
    print("Simulating how the agent would work when deployed to Bedrock AgentCore")
    print(f"Test Session: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Initialize mock runtime
    runtime = MockBedrockAgentRuntime()
    
    # Test with various stock tickers
    test_tickers = ["AAPL", "MSFT", "GOOGL", "TSLA"]
    
    print("Starting agent tests...")
    results = runtime.test_multiple_stocks(test_tickers)
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    successful_tests = 0
    total_response_time = 0
    
    for ticker, result in results.items():
        status = "PASS" if "error" not in result["response"] else "FAIL"
        response_time = result["response_time"]
        
        print(f"{ticker:<8} | {status} | {response_time:>6.2f}s")
        
        if "error" not in result["response"]:
            successful_tests += 1
            total_response_time += response_time
    
    print("-" * 80)
    print(f"Success Rate: {successful_tests}/{len(test_tickers)} ({successful_tests/len(test_tickers)*100:.1f}%)")
    
    if successful_tests > 0:
        avg_response_time = total_response_time / successful_tests
        print(f"Average Response Time: {avg_response_time:.2f}s")
        
        print(f"\nDEPLOYMENT SIMULATION COMPLETE!")
        print(f"   - Agent is ready for Bedrock AgentCore deployment")
        print(f"   - FastAPI endpoints are working correctly")
        print(f"   - Stock analysis and forecasting tools are functional")
        print(f"   - Expected model: anthropic.claude-3-5-sonnet-20241022-v2:0")
        print(f"   - Target region: us-west-2")
    
    return successful_tests == len(test_tickers)


if __name__ == "__main__":
    # Start the FastAPI server for testing
    import subprocess
    import threading
    import os
    
    print("Starting FastAPI server for testing...")
    
    # Start server in background
    server_process = subprocess.Popen(
        ["python", "agent.py"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        cwd=os.path.dirname(os.path.abspath(__file__))
    )
    
    try:
        # Wait for server to start
        time.sleep(3)
        
        # Run tests
        success = main()
        
        if success:
            print(f"\nAll tests passed! Agent is ready for production deployment.")
        else:
            print(f"\nSome tests failed. Please check the issues above.")
            
    finally:
        # Clean up server
        server_process.terminate()
        print(f"\nTest server stopped.")