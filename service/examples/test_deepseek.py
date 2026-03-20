"""
Test script for using DeepSeek with Mnemosyne's OpenAILLM.

Usage:
1. Set your DeepSeek API key in environment variables or .env file:
   export OPENAI_API_KEY="sk-..."
   export OPENAI_BASE_URL="https://api.deepseek.com"
   export OPENAI_MODEL="deepseek-chat"
   
2. Run this script:
   python test_deepseek.py
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Add parent directory to path to import mnemosyne
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mnemosyne.llms import OpenAILLM
from mnemosyne.llms.configs import OpenAILLMConfig

# Load environment variables
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
print(f"Loading .env from: {env_path}")
load_dotenv(env_path)

def test_deepseek():
    # Configuration for DeepSeek
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com")
    model = os.getenv("OPENAI_MODEL", "deepseek-chat")

    print(f"Env vars loaded: API_KEY={'Set' if api_key else 'Not Set'}, BASE_URL={base_url}, MODEL={model}")
    if api_key:
        print(f"API Key Length: {len(api_key)}")
        print(f"API Key First 3 chars: {api_key[:3]}")
        print(f"API Key Last 3 chars: {api_key[-3:]}")

    if not api_key:
        print("❌ Please set OPENAI_API_KEY env var to your DeepSeek API key.")
        return

    print(f"Testing DeepSeek API...")
    print(f"URL: {base_url}")
    print(f"Model: {model}")

    config = OpenAILLMConfig(
        api_key=api_key,
        base_url=base_url,
        model=model,
        temperature=0.7
    )

    try:
        llm = OpenAILLM(config)
        
        # Test 1: Simple Generation
        print("\n1. Testing Generation...")
        prompt = "Hello, who are you and what model are you using?"
        response = llm.generate(prompt)
        print(f"Response: {response}")

        # Test 2: Entity Extraction (JSON)
        print("\n2. Testing Entity Extraction...")
        text = "DeepSeek AI was founded in Hangzhou, China."
        entities = llm.extract_entities(text)
        print(f"Entities: {entities}")

        print("\n✅ DeepSeek test completed successfully!")

    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    test_deepseek()
