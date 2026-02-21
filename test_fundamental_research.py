
import sys
import os
from dotenv import load_dotenv
from pathlib import Path

# Setup paths
base_dir = Path(__file__).resolve().parent
sys.path.append(str(base_dir))

# Load Env
env_path = base_dir / "backend" / "config" / "keys.env"
load_dotenv(env_path)

# Force UTF-8 Output for Windows Console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

if not os.getenv("GEMINI_API_KEY"):
    print("⚠️ GEMINI_API_KEY not found in environment!")
    # Try looking for it in user provided context or assume it's system env
    
from backend.services.fundamental_analysis import FundamentalAnalyzer

def test_research():
    print("Initializing Analyzer...")
    analyzer = FundamentalAnalyzer()
    
    symbol = "RELIANCE.NS"
    print(f"Generating Report for {symbol}...")
    
    result = analyzer.generate_research_report(symbol)
    
    if result:
        print("\n" + "="*50)
        print(f"REPORT FOR {result['metrics']['company_name']}")
        print("="*50)
        print(result['report'])
        print("="*50)
        print("\nmetrics:", json.dumps(result['metrics'], indent=2))
    else:
        print("Failed to generate report.")

if __name__ == "__main__":
    import json
    test_research()
