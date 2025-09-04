import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from typing import Dict, List, Tuple, Any
import warnings
warnings.filterwarnings('ignore')


class StockForecaster:
    """Advanced stock forecasting using multiple techniques."""
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.model = LinearRegression()
    
    def prepare_features(self, prices: pd.Series) -> pd.DataFrame:
        """
        Prepare technical features for forecasting.
        
        Args:
            prices: Series of closing prices
        
        Returns:
            DataFrame with technical features
        """
        df = pd.DataFrame(index=prices.index)
        df['price'] = prices
        
        # Moving averages
        df['ma_5'] = prices.rolling(window=5, min_periods=1).mean()
        df['ma_10'] = prices.rolling(window=10, min_periods=1).mean()
        df['ma_20'] = prices.rolling(window=20, min_periods=1).mean()
        
        # Price ratios
        df['price_to_ma5'] = df['price'] / df['ma_5']
        df['price_to_ma20'] = df['price'] / df['ma_20']
        
        # Volatility
        df['volatility'] = prices.pct_change().rolling(window=20, min_periods=1).std()
        
        # Momentum
        df['momentum'] = prices.pct_change(periods=10)
        
        # Volume-related features would go here if we had volume data
        
        # Lag features
        for lag in [1, 5, 10]:
            df[f'lag_{lag}'] = prices.shift(lag)
        
        return df.fillna(method='bfill').fillna(method='ffill')
    
    def train_model(self, prices: pd.Series) -> Dict[str, Any]:
        """
        Train a simple linear model for forecasting.
        
        Args:
            prices: Historical closing prices
        
        Returns:
            Training results and model metrics
        """
        if len(prices) < 30:
            return {"error": "Insufficient data for training"}
        
        # Prepare features
        features_df = self.prepare_features(prices)
        
        # Create target variable (next day's price)
        features_df['target'] = features_df['price'].shift(-1)
        
        # Remove last row (no target) and first rows with NaN
        features_df = features_df.dropna()
        
        if len(features_df) < 20:
            return {"error": "Insufficient clean data for training"}
        
        # Split features and target
        feature_cols = [col for col in features_df.columns if col not in ['price', 'target']]
        X = features_df[feature_cols]
        y = features_df['target']
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train model
        self.model.fit(X_scaled, y)
        
        # Calculate training metrics
        predictions = self.model.predict(X_scaled)
        mse = np.mean((predictions - y) ** 2)
        rmse = np.sqrt(mse)
        mae = np.mean(np.abs(predictions - y))
        
        return {
            "model_trained": True,
            "training_samples": len(X),
            "rmse": round(rmse, 4),
            "mae": round(mae, 4),
            "r_squared": round(self.model.score(X_scaled, y), 4)
        }
    
    def forecast_prices(self, prices: pd.Series, days: int = 30) -> Dict[str, Any]:
        """
        Generate price forecasts using multiple methods.
        
        Args:
            prices: Historical prices
            days: Number of days to forecast
        
        Returns:
            Forecast results from multiple methods
        """
        current_price = float(prices.iloc[-1])
        
        # Method 1: Linear Trend Projection
        linear_forecast = self._linear_trend_forecast(prices, days)
        
        # Method 2: Moving Average Based
        ma_forecast = self._moving_average_forecast(prices, days)
        
        # Method 3: Monte Carlo Simulation
        monte_carlo_forecast = self._monte_carlo_forecast(prices, days)
        
        # Ensemble forecast (average of methods)
        ensemble_forecast = {
            "predicted_price": round(
                (linear_forecast["predicted_price"] + 
                 ma_forecast["predicted_price"] + 
                 monte_carlo_forecast["mean_price"]) / 3, 2
            ),
            "method": "ensemble"
        }
        
        return {
            "current_price": round(current_price, 2),
            "forecast_days": days,
            "forecasts": {
                "linear_trend": linear_forecast,
                "moving_average": ma_forecast,
                "monte_carlo": monte_carlo_forecast,
                "ensemble": ensemble_forecast
            },
            "confidence_analysis": self._analyze_confidence(prices, 
                                                           linear_forecast, 
                                                           ma_forecast, 
                                                           monte_carlo_forecast)
        }
    
    def _linear_trend_forecast(self, prices: pd.Series, days: int) -> Dict[str, float]:
        """Forecast using linear trend extrapolation."""
        x = np.arange(len(prices)).reshape(-1, 1)
        y = prices.values
        
        model = LinearRegression()
        model.fit(x, y)
        
        # Predict future
        future_x = len(prices) + days - 1
        predicted_price = model.predict([[future_x]])[0]
        
        return {
            "predicted_price": round(predicted_price, 2),
            "daily_trend": round(model.coef_[0], 4),
            "method": "linear_regression"
        }
    
    def _moving_average_forecast(self, prices: pd.Series, days: int) -> Dict[str, float]:
        """Forecast using moving average trends."""
        # Calculate different MAs
        ma_short = prices.rolling(window=10, min_periods=1).mean()
        ma_long = prices.rolling(window=30, min_periods=1).mean()
        
        # Calculate trend from MA crossover
        recent_trend = (ma_short.iloc[-1] - ma_short.iloc[-10]) / 10 if len(ma_short) >= 10 else 0
        
        # Project forward
        current_price = float(prices.iloc[-1])
        predicted_price = current_price + (recent_trend * days)
        
        return {
            "predicted_price": round(predicted_price, 2),
            "ma_10": round(ma_short.iloc[-1], 2),
            "ma_30": round(ma_long.iloc[-1], 2) if len(ma_long) >= 30 else "N/A",
            "method": "moving_average_trend"
        }
    
    def _monte_carlo_forecast(self, prices: pd.Series, days: int, simulations: int = 1000) -> Dict[str, Any]:
        """Forecast using Monte Carlo simulation."""
        returns = prices.pct_change().dropna()
        
        if len(returns) < 10:
            return {
                "mean_price": float(prices.iloc[-1]),
                "std_dev": 0,
                "percentile_5": float(prices.iloc[-1]),
                "percentile_95": float(prices.iloc[-1]),
                "method": "monte_carlo_insufficient_data"
            }
        
        # Calculate parameters
        mean_return = returns.mean()
        std_return = returns.std()
        
        # Run simulations
        current_price = float(prices.iloc[-1])
        simulated_prices = []
        
        for _ in range(simulations):
            price = current_price
            for _ in range(days):
                daily_return = np.random.normal(mean_return, std_return)
                price *= (1 + daily_return)
            simulated_prices.append(price)
        
        simulated_prices = np.array(simulated_prices)
        
        return {
            "mean_price": round(np.mean(simulated_prices), 2),
            "std_dev": round(np.std(simulated_prices), 2),
            "percentile_5": round(np.percentile(simulated_prices, 5), 2),
            "percentile_95": round(np.percentile(simulated_prices, 95), 2),
            "method": "monte_carlo_simulation"
        }
    
    def _analyze_confidence(self, prices: pd.Series, linear: Dict, ma: Dict, monte_carlo: Dict) -> Dict[str, Any]:
        """Analyze forecast confidence based on method agreement and volatility."""
        # Calculate spread between forecasts
        forecasts = [
            linear["predicted_price"],
            ma["predicted_price"],
            monte_carlo["mean_price"]
        ]
        
        forecast_std = np.std(forecasts)
        forecast_mean = np.mean(forecasts)
        coefficient_of_variation = (forecast_std / forecast_mean) * 100 if forecast_mean != 0 else 100
        
        # Determine confidence level
        if coefficient_of_variation < 5:
            confidence = "high"
            confidence_score = 90
        elif coefficient_of_variation < 10:
            confidence = "moderate"
            confidence_score = 70
        elif coefficient_of_variation < 20:
            confidence = "low"
            confidence_score = 50
        else:
            confidence = "very_low"
            confidence_score = 30
        
        # Calculate historical volatility
        returns = prices.pct_change().dropna()
        historical_volatility = returns.std() * np.sqrt(252) * 100  # Annualized
        
        # Adjust confidence based on historical volatility
        if historical_volatility > 50:
            confidence_score *= 0.7
            confidence = "low" if confidence == "moderate" else "very_low"
        
        return {
            "confidence_level": confidence,
            "confidence_score": round(confidence_score, 0),
            "forecast_spread_percent": round(coefficient_of_variation, 2),
            "historical_volatility_annual": round(historical_volatility, 2),
            "methods_agreement": "high" if coefficient_of_variation < 5 else "moderate" if coefficient_of_variation < 15 else "low"
        }
    
    def generate_signals(self, prices: pd.Series) -> Dict[str, Any]:
        """Generate trading signals based on technical analysis."""
        if len(prices) < 20:
            return {"signal": "insufficient_data"}
        
        current_price = float(prices.iloc[-1])
        
        # Calculate indicators
        ma_20 = prices.rolling(window=20).mean().iloc[-1]
        ma_50 = prices.rolling(window=50).mean().iloc[-1] if len(prices) >= 50 else ma_20
        
        # RSI
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain.iloc[-1] / loss.iloc[-1] if loss.iloc[-1] != 0 else 0
        rsi = 100 - (100 / (1 + rs)) if rs != 0 else 50
        
        # Generate signals
        signals = []
        if current_price > ma_20 > ma_50:
            signals.append("bullish_trend")
        elif current_price < ma_20 < ma_50:
            signals.append("bearish_trend")
        
        if rsi > 70:
            signals.append("overbought")
        elif rsi < 30:
            signals.append("oversold")
        
        # Momentum
        momentum = (current_price - prices.iloc[-20]) / prices.iloc[-20] * 100 if len(prices) >= 20 else 0
        if momentum > 10:
            signals.append("strong_momentum")
        elif momentum < -10:
            signals.append("weak_momentum")
        
        return {
            "primary_signal": signals[0] if signals else "neutral",
            "all_signals": signals,
            "rsi": round(rsi, 2),
            "price_to_ma20": round((current_price / ma_20 - 1) * 100, 2),
            "momentum_20d": round(momentum, 2)
        }