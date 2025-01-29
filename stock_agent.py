import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

class StockBrokerAgent:
    def __init__(self):
        """Initialize the Stock Broker Agent"""
        pass

    def get_stock_data(self, ticker_symbol: str, period: str = "6mo") -> tuple:
        """Fetch stock data from Yahoo Finance"""
        try:
            stock = yf.Ticker(ticker_symbol)
            df = stock.history(period=period)
            
            # Calculate technical indicators
            df['MA20'] = df['Close'].rolling(window=20).mean()
            df['MA50'] = df['Close'].rolling(window=50).mean()
            
            # Calculate RSI
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))
            
            return df, stock.info
        except Exception as e:
            st.error(f"Error fetching data: {str(e)}")
            return None, None

    def analyze_stock(self, df: pd.DataFrame) -> dict:
        """Analyze stock data and generate recommendation"""
        if df is None or df.empty:
            return None
        
        # Get latest values
        current_price = df['Close'].iloc[-1]
        prev_price = df['Close'].iloc[-2]
        price_change = ((current_price - prev_price) / prev_price) * 100
        rsi = df['RSI'].iloc[-1]
        ma20 = df['MA20'].iloc[-1]
        ma50 = df['MA50'].iloc[-1]
        
        # Generate recommendation
        reasons = []
        score = 0
        
        # RSI Analysis
        if rsi < 30:
            reasons.append("RSI indicates oversold condition (Bullish)")
            score += 1
        elif rsi > 70:
            reasons.append("RSI indicates overbought condition (Bearish)")
            score -= 1
        
        # Moving Average Analysis
        if ma20 > ma50:
            reasons.append("Short-term trend is bullish (MA20 > MA50)")
            score += 1
        else:
            reasons.append("Short-term trend is bearish (MA20 < MA50)")
            score -= 1
        
        # Price Trend
        if price_change > 0:
            reasons.append("Price is trending upward")
            score += 1
        else:
            reasons.append("Price is trending downward")
            score -= 1
        
        # Generate final recommendation
        if score > 0:
            decision = "BUY"
            confidence = min(abs(score) / 3 * 100, 100)
        elif score < 0:
            decision = "SELL"
            confidence = min(abs(score) / 3 * 100, 100)
        else:
            decision = "HOLD"
            confidence = 50
        
        return {
            "current_price": current_price,
            "price_change": price_change,
            "rsi": rsi,
            "ma20": ma20,
            "ma50": ma50,
            "decision": decision,
            "confidence": confidence,
            "reasons": reasons
        }

def main():
    st.set_page_config(page_title="Stock Broker Agent", layout="wide")
    
    st.title("📈 Stock Broker Agent")
    st.write("Enter a stock symbol to get analysis and recommendations")
    
    # Initialize agent
    agent = StockBrokerAgent()
    
    # Stock input
    col1, col2 = st.columns([2, 1])
    with col1:
        ticker = st.text_input("Enter Stock Symbol (e.g., AAPL, GOOGL)", "AAPL").upper()
    with col2:
        period = st.selectbox("Select Time Period", 
                            ["1mo", "3mo", "6mo", "1y", "2y"], 
                            index=2)
    
    if st.button("Analyze Stock"):
        with st.spinner("Analyzing stock..."):
            # Get stock data
            df, stock_info = agent.get_stock_data(ticker, period)
            
            if df is not None and not df.empty:
                # Analyze stock
                analysis = agent.analyze_stock(df)
                
                if analysis:
                    # Display stock chart
                    st.subheader("Stock Price Chart")
                    fig = go.Figure()
                    
                    # Add candlestick chart
                    fig.add_trace(go.Candlestick(
                        x=df.index,
                        open=df['Open'],
                        high=df['High'],
                        low=df['Low'],
                        close=df['Close'],
                        name='Price'
                    ))
                    
                    # Add moving averages
                    fig.add_trace(go.Scatter(
                        x=df.index,
                        y=df['MA20'],
                        name='20-day MA',
                        line=dict(color='orange')
                    ))
                    
                    fig.add_trace(go.Scatter(
                        x=df.index,
                        y=df['MA50'],
                        name='50-day MA',
                        line=dict(color='blue')
                    ))
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Display analysis results
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader("Technical Analysis")
                        st.metric("Current Price", 
                                f"${analysis['current_price']:.2f}",
                                f"{analysis['price_change']:.2f}%")
                        st.metric("RSI", f"{analysis['rsi']:.2f}")
                        st.metric("20-day MA", f"${analysis['ma20']:.2f}")
                        st.metric("50-day MA", f"${analysis['ma50']:.2f}")
                    
                    with col2:
                        st.subheader("Recommendation")
                        
                        # Display decision with color
                        decision_color = {
                            "BUY": "green",
                            "SELL": "red",
                            "HOLD": "orange"
                        }
                        st.markdown(f"**Decision:** ::{decision_color[analysis['decision']]}[{analysis['decision']}]")
                        
                        st.markdown(f"**Confidence:** {analysis['confidence']:.1f}%")
                        
                        st.write("**Analysis:**")
                        for reason in analysis['reasons']:
                            st.write(f"- {reason}")
                
            else:
                st.error(f"Could not fetch data for {ticker}. Please check the symbol and try again.")

if __name__ == "__main__":
    main()