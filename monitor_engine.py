# monitor_engine.py
"""Core monitoring engine that orchestrates scraping and notifications"""

import asyncio
import logging
from datetime import datetime
from typing import Optional, Callable
from scrapers import DanggeunScraper, BunjangScraper, JoonggonaraScraper, Item
from notifiers import TelegramNotifier, DiscordNotifier, SlackNotifier
from db import DatabaseManager
from settings_manager import SettingsManager
from models import SearchKeyword, NotificationType


class MonitorEngine:
    """
    Core engine for monitoring used marketplaces.
    Coordinates scrapers, database, and notifications.
    """
    
    def __init__(self, settings_manager: SettingsManager):
        self.settings = settings_manager
        self.logger = logging.getLogger("MonitorEngine")
        self.db = DatabaseManager(self.settings.settings.db_path)
        
        self.scrapers = {}
        self.notifiers = []
        self.running = False
        self._task: Optional[asyncio.Task] = None
        
        # Callbacks for UI updates
        self.on_new_item: Optional[Callable[[Item], None]] = None
        self.on_price_change: Optional[Callable[[Item, str, str], None]] = None
        self.on_status_update: Optional[Callable[[str], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None
    
    def initialize_scrapers(self):
        """Initialize all scrapers"""
        headless = self.settings.settings.headless_mode
        
        try:
            self.scrapers['danggeun'] = DanggeunScraper(headless=headless)
            self.logger.info("Danggeun scraper initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize Danggeun scraper: {e}")
        
        try:
            self.scrapers['bunjang'] = BunjangScraper(headless=headless)
            self.logger.info("Bunjang scraper initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize Bunjang scraper: {e}")
        
        try:
            self.scrapers['joonggonara'] = JoonggonaraScraper(headless=headless)
            self.logger.info("Joonggonara scraper initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize Joonggonara scraper: {e}")
    
    def initialize_notifiers(self):
        """Initialize notification channels based on settings"""
        self.notifiers.clear()
        
        for config in self.settings.settings.notifiers:
            if not config.enabled:
                continue
            
            try:
                if config.type == NotificationType.TELEGRAM:
                    if config.token and config.chat_id:
                        notifier = TelegramNotifier(config.token, config.chat_id)
                        self.notifiers.append(notifier)
                        self.logger.info("Telegram notifier initialized")
                
                elif config.type == NotificationType.DISCORD:
                    if config.webhook_url:
                        notifier = DiscordNotifier(config.webhook_url)
                        self.notifiers.append(notifier)
                        self.logger.info("Discord notifier initialized")
                
                elif config.type == NotificationType.SLACK:
                    if config.webhook_url:
                        notifier = SlackNotifier(config.webhook_url)
                        self.notifiers.append(notifier)
                        self.logger.info("Slack notifier initialized")
            
            except Exception as e:
                self.logger.error(f"Failed to initialize {config.type.value} notifier: {e}")
    
    async def send_notifications(self, item: Item, is_price_change: bool = False, 
                                  old_price: str = None, new_price: str = None):
        """Send notifications through all enabled channels"""
        # Check schedule
        schedule = self.settings.settings.notification_schedule
        if not schedule.is_active_now():
            self.logger.info("Notification skipped - outside scheduled hours")
            return
        
        for notifier in self.notifiers:
            try:
                if is_price_change:
                    await notifier.send_price_change(item, old_price, new_price)
                else:
                    await notifier.send_item(item, with_image=True)
            except Exception as e:
                self.logger.error(f"Notification error: {e}")
    
    async def search_keyword(self, keyword_config: SearchKeyword) -> int:
        """
        Search for a single keyword across all enabled platforms.
        
        Returns:
            Number of new items found
        """
        new_count = 0
        
        for platform in keyword_config.platforms:
            scraper = self.scrapers.get(platform)
            if not scraper:
                continue
            
            try:
                self._update_status(f"{platform}에서 '{keyword_config.keyword}' 검색 중...")
                
                # Search
                items = scraper.search(keyword_config.keyword, keyword_config.location)
                
                # Apply filters
                if keyword_config.min_price or keyword_config.max_price:
                    items = scraper.filter_by_price(
                        items, keyword_config.min_price, keyword_config.max_price
                    )
                
                if keyword_config.exclude_keywords:
                    items = scraper.filter_by_keywords(items, keyword_config.exclude_keywords)
                
                self.logger.info(f"Found {len(items)} items on {platform} for '{keyword_config.keyword}'")
                
                # Process items
                platform_new = 0
                for item in items:
                    is_new, price_change = self.db.add_listing(item)
                    
                    if is_new:
                        platform_new += 1
                        self.logger.info(f"New item: {item.title}")
                        
                        if self.on_new_item:
                            self.on_new_item(item)
                        
                        await self.send_notifications(item)
                        await asyncio.sleep(1)  # Rate limiting
                    
                    elif price_change:
                        self.logger.info(f"Price change: {item.title} ({price_change['old_price']} → {price_change['new_price']})")
                        
                        if self.on_price_change:
                            self.on_price_change(item, price_change['old_price'], price_change['new_price'])
                        
                        await self.send_notifications(
                            item, is_price_change=True,
                            old_price=price_change['old_price'],
                            new_price=price_change['new_price']
                        )
                        await asyncio.sleep(1)
                
                # Record stats
                self.db.record_search_stats(
                    keyword_config.keyword, platform, len(items), platform_new
                )
                new_count += platform_new
                
            except Exception as e:
                self.logger.error(f"Error searching {platform}: {e}")
                if self.on_error:
                    self.on_error(f"{platform} 검색 오류: {e}")
            
            await asyncio.sleep(2)  # Pause between platforms
        
        return new_count
    
    async def run_cycle(self) -> int:
        """
        Run one complete monitoring cycle.
        
        Returns:
            Total number of new items found
        """
        total_new = 0
        keywords = self.settings.settings.keywords
        
        for kw in keywords:
            if not kw.enabled:
                continue
            
            try:
                new_count = await self.search_keyword(kw)
                total_new += new_count
            except Exception as e:
                self.logger.error(f"Error processing keyword '{kw.keyword}': {e}")
            
            await asyncio.sleep(2)  # Pause between keywords
        
        return total_new
    
    async def start(self):
        """Start the monitoring loop"""
        if self.running:
            return
        
        self.running = True
        self.logger.info("Starting monitor engine...")
        
        self.initialize_scrapers()
        self.initialize_notifiers()
        
        # Send startup notification
        for notifier in self.notifiers:
            try:
                await notifier.send_message("🚀 중고거래 알리미가 시작되었습니다!")
            except:
                pass
        
        self._update_status("모니터링 시작됨")
        
        while self.running:
            try:
                self._update_status("검색 사이클 시작...")
                new_items = await self.run_cycle()
                
                interval = self.settings.settings.check_interval_seconds
                self._update_status(f"다음 검색까지 {interval}초 대기 중... (새 상품 {new_items}개 발견)")
                
                await asyncio.sleep(interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                if self.on_error:
                    self.on_error(f"모니터링 오류: {e}")
                await asyncio.sleep(30)  # Wait before retry
        
        self._update_status("모니터링 중지됨")
    
    def stop(self):
        """Stop the monitoring loop"""
        self.running = False
        self.logger.info("Stopping monitor engine...")
        
        # Close scrapers
        for name, scraper in self.scrapers.items():
            try:
                scraper.close()
                self.logger.info(f"Closed {name} scraper")
            except Exception as e:
                self.logger.error(f"Error closing {name} scraper: {e}")
        
        self.scrapers.clear()
    
    def _update_status(self, status: str):
        """Update status and notify callback"""
        self.logger.info(status)
        if self.on_status_update:
            self.on_status_update(status)
    
    def get_stats(self) -> dict:
        """Get current statistics"""
        return {
            'total_listings': self.db.get_total_listings(),
            'by_platform': self.db.get_listings_by_platform(),
            'by_keyword': self.db.get_listings_by_keyword(),
            'daily_stats': self.db.get_daily_stats(7),
            'recent_listings': self.db.get_recent_listings(10),
            'price_changes': self.db.get_price_changes(7),
        }
    
    def close(self):
        """Clean up resources"""
        self.stop()
        self.db.close()
