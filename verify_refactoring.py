
import sys
import logging
from PyQt6.QtWidgets import QApplication

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VERIFY")

def verify_imports():
    logger.info("Verifying imports...")
    try:
        from gui.stats_widget import StatsWidget
        logger.info("gui.stats_widget loaded.")
        
        from scrapers.selenium_base import SeleniumScraper
        logger.info("scrapers.selenium_base loaded.")
        
        from scrapers.danggeun import DanggeunScraper
        logger.info("scrapers.danggeun loaded.")
        
        from scrapers.bunjang import BunjangScraper
        logger.info("scrapers.bunjang loaded.")
        
        from gui.charts import PlatformChart, DailyChart
        logger.info("gui.charts loaded.")
        
        from gui.components import StatCard
        logger.info("gui.components loaded.")
        
    except Exception as e:
        logger.error(f"Import failed: {e}")
        sys.exit(1)
        
    logger.info("All imports successful.")

if __name__ == "__main__":
    verify_imports()
