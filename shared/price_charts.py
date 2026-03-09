"""
Price Chart Generator for Market Data Visualization
Uses Plotly for interactive charts
Supports both demo data and real API integration
"""

import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import random
import requests
import os


class PriceChartGenerator:
    """Generate interactive price comparison charts"""
    
    def __init__(self, use_real_api: bool = False):
        """
        Initialize chart generator
        
        Args:
            use_real_api: If True, attempts to fetch real market data from APIs
                         If False or API fails, uses demo data
        """
        self.crops = ["Wheat", "Rice", "Cotton", "Maize", "Soybean", "Potato", "Onion", "Tomato"]
        self.locations = ["Mumbai", "Delhi", "Bangalore", "Kolkata", "Chennai", "Hyderabad", "Pune", "Ahmedabad"]
        self.use_real_api = use_real_api
        self.api_key = os.getenv('AGMARKNET_API_KEY', '')  # Optional API key from .env
    
    def fetch_real_price_data(self, crop: str, location: str, days: int = 30) -> Optional[Dict]:
        """
        Fetch real market price data from API
        
        Args:
            crop: Crop name
            location: Market location
            days: Number of days of historical data
            
        Returns:
            Dict with dates and prices, or None if API fails
        """
        if not self.use_real_api:
            return None
        
        try:
            # Example: Agmarknet API (you'll need to register for API key)
            # Replace with actual API endpoint
            api_url = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"
            
            params = {
                'api-key': self.api_key,
                'format': 'json',
                'filters[commodity]': crop.lower(),
                'filters[market]': location,
                'limit': days
            }
            
            response = requests.get(api_url, params=params, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                
                # Parse API response (format depends on actual API)
                dates = []
                prices = []
                
                for record in data.get('records', []):
                    dates.append(record.get('date'))
                    prices.append(float(record.get('modal_price', 0)))
                
                if dates and prices:
                    return {
                        'dates': dates,
                        'prices': prices,
                        'crop': crop,
                        'location': location,
                        'source': 'real_api'
                    }
            
        except Exception as e:
            print(f"API fetch failed: {e}. Falling back to demo data.")
        
        return None
    
    def get_price_data(self, crop: str, location: str, days: int = 30) -> Dict:
        """
        Get price data - tries real API first, falls back to demo data
        
        Args:
            crop: Crop name
            location: Market location
            days: Number of days of historical data
            
        Returns:
            Dict with dates, prices, crop, location, and source
        """
        # Try real API first if enabled
        if self.use_real_api:
            real_data = self.fetch_real_price_data(crop, location, days)
            if real_data:
                return real_data
        
        # Fall back to demo data
        return self.generate_demo_price_data(crop, location, days)
    
    def generate_demo_price_data(self, crop: str, location: str, days: int = 30) -> Dict:
        """Generate demo price data for testing"""
        base_prices = {
            "wheat": 2000,
            "rice": 2500,
            "cotton": 5000,
            "maize": 1800,
            "soybean": 3500,
            "potato": 1200,
            "onion": 1500,
            "tomato": 2000
        }
        
        base_price = base_prices.get(crop.lower(), 2000)
        
        # Generate dates
        dates = [(datetime.now() - timedelta(days=days-i)).strftime('%Y-%m-%d') for i in range(days)]
        
        # Generate prices with some variation
        prices = []
        current_price = base_price
        for _ in range(days):
            # Random walk with trend
            change = random.uniform(-100, 150)
            current_price = max(base_price * 0.7, min(base_price * 1.3, current_price + change))
            prices.append(round(current_price, 2))
        
        return {
            'dates': dates,
            'prices': prices,
            'crop': crop,
            'location': location,
            'source': 'demo'
        }
    
    def create_price_trend_chart(self, crop: str, location: str, days: int = 30) -> go.Figure:
        """Create a line chart showing price trends over time"""
        data = self.get_price_data(crop, location, days)
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=data['dates'],
            y=data['prices'],
            mode='lines+markers',
            name=f"{crop} - {location}",
            line=dict(color='#2E7D32', width=3),
            marker=dict(size=6),
            hovertemplate='<b>Date:</b> %{x}<br><b>Price:</b> ₹%{y}/quintal<extra></extra>'
        ))
        
        # Add average line
        avg_price = sum(data['prices']) / len(data['prices'])
        fig.add_hline(
            y=avg_price,
            line_dash="dash",
            line_color="red",
            annotation_text=f"Avg: ₹{avg_price:.2f}",
            annotation_position="right"
        )
        
        # Add data source indicator
        source_text = "Real Market Data" if data.get('source') == 'real_api' else "Demo Data"
        
        fig.update_layout(
            title=f"{crop.title()} Price Trend - {location}<br><sub>{source_text}</sub>",
            xaxis_title="Date",
            yaxis_title="Price (₹ per quintal)",
            hovermode='x unified',
            template='plotly_white',
            height=400
        )
        
        return fig
    
    def create_multi_location_comparison(self, crop: str, locations: List[str], days: int = 30) -> go.Figure:
        """Create a chart comparing prices across multiple locations"""
        fig = go.Figure()
        
        colors = ['#2E7D32', '#1976D2', '#F57C00', '#7B1FA2', '#C62828', '#00796B']
        data_source = None
        
        for idx, location in enumerate(locations):
            data = self.get_price_data(crop, location, days)
            if not data_source:
                data_source = data.get('source', 'demo')
            
            fig.add_trace(go.Scatter(
                x=data['dates'],
                y=data['prices'],
                mode='lines+markers',
                name=location,
                line=dict(color=colors[idx % len(colors)], width=2),
                marker=dict(size=4),
                hovertemplate=f'<b>{location}</b><br>Date: %{{x}}<br>Price: ₹%{{y}}/quintal<extra></extra>'
            ))
        
        source_text = "Real Market Data" if data_source == 'real_api' else "Demo Data"
        
        fig.update_layout(
            title=f"{crop.title()} Price Comparison Across Markets<br><sub>{source_text}</sub>",
            xaxis_title="Date",
            yaxis_title="Price (₹ per quintal)",
            hovermode='x unified',
            template='plotly_white',
            height=500,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        return fig
    
    def create_multi_crop_comparison(self, crops: List[str], location: str, days: int = 30) -> go.Figure:
        """Create a chart comparing prices of multiple crops in one location"""
        fig = go.Figure()
        
        colors = ['#2E7D32', '#1976D2', '#F57C00', '#7B1FA2', '#C62828', '#00796B', '#558B2F', '#D84315']
        data_source = None
        
        for idx, crop in enumerate(crops):
            data = self.get_price_data(crop, location, days)
            if not data_source:
                data_source = data.get('source', 'demo')
            
            fig.add_trace(go.Scatter(
                x=data['dates'],
                y=data['prices'],
                mode='lines',
                name=crop.title(),
                line=dict(color=colors[idx % len(colors)], width=2),
                hovertemplate=f'<b>{crop.title()}</b><br>Date: %{{x}}<br>Price: ₹%{{y}}/quintal<extra></extra>'
            ))
        
        source_text = "Real Market Data" if data_source == 'real_api' else "Demo Data"
        
        fig.update_layout(
            title=f"Multi-Crop Price Comparison - {location}<br><sub>{source_text}</sub>",
            xaxis_title="Date",
            yaxis_title="Price (₹ per quintal)",
            hovermode='x unified',
            template='plotly_white',
            height=500,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        return fig
    
    def create_current_price_bar_chart(self, crops: List[str], location: str) -> go.Figure:
        """Create a bar chart showing current prices for multiple crops"""
        prices = []
        data_source = None
        
        for crop in crops:
            data = self.get_price_data(crop, location, days=1)
            if not data_source:
                data_source = data.get('source', 'demo')
            prices.append(data['prices'][0])
        
        source_text = "Real Market Data" if data_source == 'real_api' else "Demo Data"
        
        fig = go.Figure(data=[
            go.Bar(
                x=[c.title() for c in crops],
                y=prices,
                marker_color='#2E7D32',
                text=[f"₹{p:.0f}" for p in prices],
                textposition='outside',
                hovertemplate='<b>%{x}</b><br>Price: ₹%{y}/quintal<extra></extra>'
            )
        ])
        
        fig.update_layout(
            title=f"Current Market Prices - {location}<br><sub>{source_text}</sub>",
            xaxis_title="Crop",
            yaxis_title="Price (₹ per quintal)",
            template='plotly_white',
            height=400
        )
        
        return fig


# Global instance
_price_chart_generator: PriceChartGenerator = None


def get_price_chart_generator(use_real_api: bool = False) -> PriceChartGenerator:
    """
    Get price chart generator instance
    
    Args:
        use_real_api: If True, attempts to use real market data APIs
                     If False, uses demo data
    """
    global _price_chart_generator
    
    if _price_chart_generator is None:
        _price_chart_generator = PriceChartGenerator(use_real_api=use_real_api)
    
    return _price_chart_generator


if __name__ == '__main__':
    # Test price chart generator
    generator = get_price_chart_generator()
    
    print("Price Chart Generator Test")
    print("=" * 50)
    
    # Generate demo data
    data = generator.generate_demo_price_data("wheat", "Mumbai", 30)
    print(f"\nGenerated {len(data['dates'])} days of price data for Wheat in Mumbai")
    print(f"Price range: ₹{min(data['prices']):.2f} - ₹{max(data['prices']):.2f}")
