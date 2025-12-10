# test_simple.py
import os
from openai import OpenAI


print("Testing OpenAI API Connection...")
print("=" * 50)


# Check if API key exists
api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    print("❌ ERROR: OPENAI_API_KEY not found in environment!")
    print("\nSet it with:")
    print('$env:OPENAI_API_KEY = "sk-proj-your-key-here"')
    exit(1)


print(f"✅ API Key found (length: {len(api_key)})")
print(f"Key starts with: {api_key[:20]}...")


# Initialize client
client = OpenAI(api_key=api_key)


try:
    print("\n📡 Sending test request to OpenAI...")
   
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",  # Start with cheaper model
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say 'API connection successful!' in a creative way."}
        ],
        max_tokens=50
    )
   
    print("\n✅ SUCCESS! Response received:")
    print("-" * 40)
    print(response.choices[0].message.content)
    print("-" * 40)
    print(f"Model: {response.model}")
    print(f"Usage: {response.usage.total_tokens} tokens")
   
except Exception as e:
    print(f"\n❌ ERROR: {type(e).__name__}")
    print(f"Message: {str(e)}")
   
    if "401" in str(e):
        print("\n🔑 Authentication Error - Your API key is invalid")
        print("1. Get a new key from: https://platform.openai.com/account/api-keys")
        print("2. Make sure you copy the ENTIRE key (no ellipsis ...)")
        print("3. Set it with: $env:OPENAI_API_KEY = 'sk-proj-...'")
    elif "429" in str(e):
        print("\n⏱️ Rate limit error - Wait a minute and try again")
    elif "Invalid URL" in str(e):
        print("\n🌐 Network error - Check your internet connection")