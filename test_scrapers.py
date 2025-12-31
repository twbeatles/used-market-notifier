import logging
import sys
from scrapers.danggeun import DanggeunScraper
from scrapers.bunjang import BunjangScraper



logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger("Test")

def test_scrapers():
    keyword = "맥북"
    
    # Test Danggeun
    print("\n--- Testing Danggeun Market ---")
    dg = DanggeunScraper()
    items = dg.search(keyword)
    print(f"Found {len(items)} items.")
    for item in items[:3]:
        print(item)
    dg.close()

    # Test Bunjang
    print("\n--- Testing Bunjang ---")
    bj = BunjangScraper()
    # We need to hack the search method or just copy code here to debug extraction.
    # I'll just run search and if title is empty, I'll print the first element's outerHTML from within the class if I could, 
    # but I can't modify the class easily while running this script.
    # So I will rely on my deduction or modify the class code directly in next step.
    # Actually, I'll modify the scrapers to log error/debug info.
    
    items = bj.search(keyword)
    print(f"Found {len(items)} items.")
    for item in items[:5]:
        print(f"ID: {item.article_id}, Title: '{item.title}', Price: '{item.price}'")
    bj.close()

if __name__ == "__main__":
    test_scrapers()
