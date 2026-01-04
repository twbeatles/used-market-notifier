"""Test Playwright scraper initialization"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from scrapers.bunjang import BunjangScraper

async def test():
    print("Creating scraper...")
    scraper = BunjangScraper(headless=False)
    
    print("Creating browser...")
    await scraper._create_browser()
    print("Browser created successfully!")
    
    print("Testing search...")
    items = await scraper.search("테스트")
    print(f"Found {len(items)} items")
    
    print("Closing...")
    await scraper.close()
    print("Done!")

if __name__ == "__main__":
    asyncio.run(test())
