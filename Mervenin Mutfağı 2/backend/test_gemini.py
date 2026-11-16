import asyncio
import os
from dotenv import load_dotenv

# load dotenv
load_dotenv()

from gemini_service import gemini_service

async def main():
    print("API configured:", gemini_service.api_key_configured)
    print("API Key:", os.getenv("GEMINI_API_KEY"))
    
    ingredients = ["domates", "yumurta"]
    cuisine = "Türk Mutfağı"
    
    print("\nTarif üretiliyor...")
    res = await gemini_service.generate_recipe(ingredients, cuisine)
    print("\nSonuç:")
    import pprint
    pprint.pprint(res)

if __name__ == "__main__":
    asyncio.run(main())
