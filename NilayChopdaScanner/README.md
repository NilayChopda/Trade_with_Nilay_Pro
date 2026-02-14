# NilayChopdaScanner

A comprehensive stock scanning system for Indian markets (NSE/BSE) built with clean architecture principles.

## Features

- Real-time stock scanning
- Multi-exchange support (NSE, BSE)
- Modular and extensible architecture
- Comprehensive logging and error handling
- Configurable scanning parameters

## Project Structure

```
NilayChopdaScanner/
├── src/
│   ├── scanner/
│   │   ├── core/          # Core scanning logic
│   │   ├── data/          # Data fetching and processing
│   │   └── utils/         # Utility functions
├── tests/                 # Unit and integration tests
├── config.py             # Configuration settings
├── main.py               # Application entry point
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- Git (optional, for version control)

### 1. Clone or Download

Navigate to your desired directory and create the project folder:

```bash
cd "G:\My Drive\Trade_with_Nilay"
# The project structure is already created
```

### 2. Create Virtual Environment

It's recommended to use a virtual environment to isolate dependencies.

#### Using venv (built-in):

```bash
# Navigate to project root
cd NilayChopdaScanner

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
# source venv/bin/activate
```

#### Using conda (if you prefer conda):

```bash
# Create conda environment
conda create -n nilay-scanner python=3.9

# Activate conda environment
conda activate nilay-scanner
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root (optional, for sensitive configurations):

```env
SCANNER_API_KEY=your_api_key_here
SCANNER_API_SECRET=your_api_secret_here
DATABASE_URL=sqlite:///scanner.db
LOG_LEVEL=INFO
```

### 5. Run the Application

```bash
python main.py
```

## Swing Trading Scanner

The system includes a sophisticated swing trading scanner that identifies stocks meeting specific technical criteria using Weighted Moving Averages (WMA) across multiple timeframes.

### Scanner Criteria

The scanner evaluates stocks against these 7 conditions:

1. **Daily WMA(1) > Monthly WMA(2) + 1**
2. **Monthly WMA(2) > Monthly WMA(4) + 2**
3. **Daily WMA(1) > Weekly WMA(6) + 2**
4. **Weekly WMA(6) > Weekly WMA(12) + 2**
5. **Daily WMA(1) > 4 days ago WMA(12) + 2**
6. **Daily WMA(1) > 2 days ago WMA(20) + 2**
7. **Daily Close > 20**

### WMA Calculation

- **Weights**: Linear weighting (1, 2, 3, ..., n) where most recent data has highest weight
- **Formula**: WMA = Σ(Pi × wi) / Σ(wi)
- **Timeframes**:
  - Daily: Daily price data
  - Weekly: Weekly aggregated data
  - Monthly: Monthly aggregated data

### Usage

```bash
# Run swing trading scan on first 100 symbols
python main.py --swing-scan --max-symbols 100

# Run scan with fresh data download
python main.py --swing-scan --refresh-data

# Show universe information
python main.py --universe-info

# Fetch data for universe
python main.py --fetch-universe --max-symbols 50
```

### Output

The scanner provides:
- **Qualifying stocks** that meet all criteria
- **Technical metrics** (returns, volatility, volume ratios)
- **Price performance** (5d, 20d, 60d changes)
- **Success rate** statistics

## Order Block Engine

The system includes a sophisticated Order Block detection engine based on Smart Money Concepts (SMC). Order Blocks are key price zones where institutional traders accumulate or distribute positions.

### Smart Money Concepts

**Order Block Formation Process:**
1. **Impulse Move**: Strong directional price action (3+ consecutive candles)
2. **Break of Structure (BOS)**: Price breaks above recent high (bullish) or below recent low (bearish)
3. **Last Opposite Candle**: The candle opposing the impulse direction before BOS
4. **Order Block Zone**: High-low range of the last opposite candle becomes the OB zone

### Order Block Types

- **BULLISH_OB (Demand Zone)**: Formed after bullish BOS, potential support/bounce zone
- **BEARISH_OB (Supply Zone)**: Formed after bearish BOS, potential resistance/drop zone

### Usage

```bash
# Run Order Block analysis on first 100 symbols
python main.py --orderblock-scan --max-symbols 100

# Monitor Order Block taps for a specific stock
python main.py --monitor-ob RELIANCE 2500.50

# Show Order Block summary for a specific stock
python main.py --ob-summary RELIANCE

# Show overall Order Block statistics
python main.py --ob-summary
```

### Telegram Alerts

When Order Block zones are tapped, the system automatically sends Telegram alerts with:
- Stock symbol and current price
- Order Block type (Demand/Supply)
- Zone price range
- Strength rating
- Expected directional bias
- TradingView chart link

### Detection Parameters

- **Minimum Impulse**: 3+ consecutive directional candles
- **BOS Lookback**: 10 candles for swing point detection
- **Minimum Strength**: 2/5 for valid Order Blocks
- **Zone Filtering**: Removes overlapping zones (keeps stronger ones)

### Data Storage

Order Blocks are saved in `data/order_blocks/` as JSON files:
```
data/order_blocks/
├── RELIANCE_order_blocks.json
├── TCS_order_blocks.json
└── ...
```

Each file contains historical Order Blocks with tap status and timestamps.

## Development

### Running Tests

```bash
python -m pytest tests/
```

### Code Style

This project follows PEP 8 style guidelines. Use tools like `black` and `flake8` for code formatting and linting.

## Data Sources

### Stock Symbols
- **Source**: NSE India Equity List (https://archives.nseindia.com/content/equities/EQUITY_L.csv)
- **Format**: Public CSV file with all listed equity symbols
- **Update Frequency**: Daily (cached locally for 24 hours)

### Historical Data
- **Source**: Yahoo Finance API via yfinance library
- **Format**: OHLCV data (Open, High, Low, Close, Volume)
- **Period**: Last 2 years of daily data by default
- **Storage**: Individual CSV files per symbol in `data/daily_data/`

**Note**: Ensure stable internet connection for data downloads. The system includes retry logic and error handling for API failures.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is proprietary software. All rights reserved.

## Support

For support or questions, please contact the development team.