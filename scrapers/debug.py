# scrapers/debug.py
"""
Debugging helper module for scraping operations.
Provides comprehensive debugging, logging, and diagnostics capabilities.
"""

import os
import json
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Any
from dataclasses import dataclass, field, asdict
from playwright.async_api import Page, Response, Request

logger = logging.getLogger("ScraperDebug")


# Debug output directory
DEBUG_DIR = Path("debug_output")


@dataclass
class RequestLog:
    """Log entry for a network request"""
    timestamp: str
    url: str
    method: str
    status: Optional[int] = None
    resource_type: str = ""
    headers: dict = field(default_factory=dict)
    response_headers: dict = field(default_factory=dict)
    duration_ms: float = 0
    failed: bool = False
    failure_reason: str = ""


@dataclass 
class ScrapingSession:
    """Container for a complete scraping session's debug data"""
    session_id: str
    platform: str
    keyword: str
    start_time: str
    end_time: str = ""
    status: str = "running"
    items_found: int = 0
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    screenshots: list = field(default_factory=list)
    network_logs: list = field(default_factory=list)
    console_logs: list = field(default_factory=list)
    page_html: str = ""
    bot_detection_result: dict = field(default_factory=dict)


class ScraperDebugger:
    """
    Comprehensive debugger for scraping operations.
    Captures screenshots, network logs, console output, and more.
    """
    
    def __init__(
        self, 
        platform: str,
        keyword: str = "",
        debug_level: str = "info",  # debug, info, warning, error
        save_screenshots: bool = True,
        save_html: bool = True,
        save_network_logs: bool = True,
        save_console_logs: bool = True,
        output_dir: Path = DEBUG_DIR
    ):
        self.platform = platform
        self.keyword = keyword
        self.debug_level = debug_level
        self.save_screenshots = save_screenshots
        self.save_html = save_html
        self.save_network_logs = save_network_logs
        self.save_console_logs = save_console_logs
        self.output_dir = output_dir
        
        # Session data
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session = ScrapingSession(
            session_id=self.session_id,
            platform=platform,
            keyword=keyword,
            start_time=datetime.now().isoformat()
        )
        
        # Create output directory
        self.session_dir = self.output_dir / f"{platform}_{self.session_id}"
        if any([save_screenshots, save_html, save_network_logs]):
            self.session_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger(f"Debug.{platform}")
        self._request_times: dict = {}  # Track request start times
        
    async def attach_to_page(self, page: Page):
        """
        Attach debugger listeners to a page.
        
        Args:
            page: Playwright Page object
        """
        if self.save_network_logs:
            page.on("request", self._on_request)
            page.on("response", self._on_response)
            page.on("requestfailed", self._on_request_failed)
        
        if self.save_console_logs:
            page.on("console", self._on_console)
            page.on("pageerror", self._on_page_error)
        
        self.logger.info(f"Debugger attached to page (session: {self.session_id})")
    
    def _on_request(self, request: Request):
        """Handle request event"""
        self._request_times[request.url] = datetime.now()
        if self.debug_level == "debug":
            self.logger.debug(f"→ {request.method} {request.url[:80]}")
    
    def _on_response(self, response: Response):
        """Handle response event"""
        start_time = self._request_times.pop(response.url, None)
        duration = 0
        if start_time:
            duration = (datetime.now() - start_time).total_seconds() * 1000
        
        log = RequestLog(
            timestamp=datetime.now().isoformat(),
            url=response.url,
            method=response.request.method,
            status=response.status,
            resource_type=response.request.resource_type,
            duration_ms=round(duration, 2)
        )
        self.session.network_logs.append(asdict(log))
        
        # Log slow requests
        if duration > 3000:
            self.logger.warning(f"⚠️ Slow response ({duration:.0f}ms): {response.url[:60]}")
        
        # Log errors
        if response.status >= 400:
            self.logger.warning(f"⚠️ HTTP {response.status}: {response.url[:60]}")
            self.session.warnings.append(f"HTTP {response.status}: {response.url}")
    
    def _on_request_failed(self, request: Request):
        """Handle failed request event"""
        failure = request.failure
        log = RequestLog(
            timestamp=datetime.now().isoformat(),
            url=request.url,
            method=request.method,
            resource_type=request.resource_type,
            failed=True,
            failure_reason=failure if failure else "Unknown"
        )
        self.session.network_logs.append(asdict(log))
        self.logger.error(f"❌ Request failed: {request.url[:60]} - {failure}")
        self.session.errors.append(f"Request failed: {request.url} - {failure}")
    
    def _on_console(self, msg):
        """Handle console message event"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": msg.type,
            "text": msg.text
        }
        self.session.console_logs.append(log_entry)
        
        if msg.type == "error":
            self.logger.error(f"Console error: {msg.text[:100]}")
        elif msg.type == "warning" and self.debug_level in ["debug", "info"]:
            self.logger.warning(f"Console warning: {msg.text[:100]}")
    
    def _on_page_error(self, error):
        """Handle page error event"""
        self.session.errors.append(f"Page error: {str(error)}")
        self.logger.error(f"❌ Page error: {error}")
    
    async def take_screenshot(
        self, 
        page: Page, 
        name: str = "screenshot",
        full_page: bool = True
    ) -> Optional[str]:
        """
        Take a screenshot and save it.
        
        Args:
            page: Playwright Page object
            name: Screenshot name (without extension)
            full_page: Whether to capture full page
            
        Returns:
            Path to saved screenshot or None
        """
        if not self.save_screenshots:
            return None
        
        try:
            filename = f"{name}_{datetime.now().strftime('%H%M%S')}.png"
            filepath = self.session_dir / filename
            await page.screenshot(path=str(filepath), full_page=full_page)
            self.session.screenshots.append(str(filepath))
            self.logger.info(f"📸 Screenshot saved: {filepath}")
            return str(filepath)
        except Exception as e:
            self.logger.error(f"Failed to take screenshot: {e}")
            return None
    
    async def save_page_html(self, page: Page, name: str = "page") -> Optional[str]:
        """
        Save page HTML content.
        
        Args:
            page: Playwright Page object
            name: File name (without extension)
            
        Returns:
            Path to saved HTML or None
        """
        if not self.save_html:
            return None
        
        try:
            html = await page.content()
            filename = f"{name}_{datetime.now().strftime('%H%M%S')}.html"
            filepath = self.session_dir / filename
            filepath.write_text(html, encoding="utf-8")
            self.session.page_html = str(filepath)
            self.logger.info(f"📄 HTML saved: {filepath}")
            return str(filepath)
        except Exception as e:
            self.logger.error(f"Failed to save HTML: {e}")
            return None
    
    async def check_bot_detection(self, page: Page) -> dict:
        """
        Run bot detection checks and log results.
        
        Args:
            page: Playwright Page object
            
        Returns:
            Dict with detection check results
        """
        from .stealth import check_bot_detection
        
        result = await check_bot_detection(page)
        self.session.bot_detection_result = result
        
        # Log detection status
        webdriver_detected = result.get('webdriver', False)
        if webdriver_detected:
            self.logger.warning("⚠️ WebDriver DETECTED - Bot detection may block requests")
            self.session.warnings.append("WebDriver detection triggered")
        else:
            self.logger.info("✅ Bot detection check PASSED")
        
        return result
    
    def log_items_found(self, count: int):
        """Log the number of items found"""
        self.session.items_found = count
        self.logger.info(f"📦 Found {count} items for '{self.keyword}' on {self.platform}")
    
    def log_error(self, message: str, exception: Exception = None):
        """Log an error"""
        full_message = message
        if exception:
            full_message = f"{message}: {type(exception).__name__}: {exception}"
        self.session.errors.append(full_message)
        self.logger.error(f"❌ {full_message}")
    
    def log_warning(self, message: str):
        """Log a warning"""
        self.session.warnings.append(message)
        self.logger.warning(f"⚠️ {message}")
    
    def log_info(self, message: str):
        """Log info message"""
        self.logger.info(f"ℹ️ {message}")
    
    def log_debug(self, message: str):
        """Log debug message"""
        if self.debug_level == "debug":
            self.logger.debug(f"🔍 {message}")
    
    async def finalize(self, status: str = "completed") -> dict:
        """
        Finalize the debug session and save report.
        
        Args:
            status: Final status (completed, failed, partial)
            
        Returns:
            Session summary dict
        """
        self.session.end_time = datetime.now().isoformat()
        self.session.status = status
        
        # Calculate duration
        start = datetime.fromisoformat(self.session.start_time)
        end = datetime.fromisoformat(self.session.end_time)
        duration = (end - start).total_seconds()
        
        # Summary
        summary = {
            "session_id": self.session_id,
            "platform": self.platform,
            "keyword": self.keyword,
            "status": status,
            "duration_seconds": round(duration, 2),
            "items_found": self.session.items_found,
            "errors_count": len(self.session.errors),
            "warnings_count": len(self.session.warnings),
            "screenshots_count": len(self.session.screenshots),
            "network_requests": len(self.session.network_logs),
        }
        
        # Save full report
        if self.session_dir.exists():
            report_path = self.session_dir / "session_report.json"
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(asdict(self.session), f, ensure_ascii=False, indent=2)
            self.logger.info(f"📋 Session report saved: {report_path}")
        
        # Log summary
        self.logger.info(f"""
╔══════════════════════════════════════════════════════════════╗
║                    SCRAPING SESSION SUMMARY                   ║
╠══════════════════════════════════════════════════════════════╣
║  Platform: {self.platform:15}  Keyword: {self.keyword:20} ║
║  Status: {status:17}  Duration: {duration:.2f}s           ║
║  Items Found: {self.session.items_found:12}                               ║
║  Errors: {len(self.session.errors):17}  Warnings: {len(self.session.warnings):17}  ║
║  Network Requests: {len(self.session.network_logs):10}                          ║
╚══════════════════════════════════════════════════════════════╝
""")
        
        return summary


async def capture_on_error(
    page: Page, 
    debugger: ScraperDebugger,
    error: Exception,
    context: str = "unknown"
):
    """
    Capture diagnostic information when an error occurs.
    
    Args:
        page: Playwright Page object
        debugger: ScraperDebugger instance
        error: The exception that occurred
        context: Description of what was happening
    """
    debugger.log_error(f"Error during {context}", error)
    
    # Take error screenshot
    await debugger.take_screenshot(page, f"error_{context}")
    
    # Save page HTML
    await debugger.save_page_html(page, f"error_{context}")
    
    # Check bot detection
    await debugger.check_bot_detection(page)


def setup_debug_logging(level: str = "INFO"):
    """
    Setup logging configuration for debugging.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR)
    """
    log_format = "%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s"
    
    # Console handler with colors (if supported)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(log_format))
    
    # File handler for debug output
    DEBUG_DIR.mkdir(exist_ok=True)
    file_handler = logging.FileHandler(
        DEBUG_DIR / f"scraper_debug_{datetime.now().strftime('%Y%m%d')}.log",
        encoding="utf-8"
    )
    file_handler.setFormatter(logging.Formatter(log_format))
    
    # Configure loggers
    for logger_name in ["ScraperDebug", "Debug", "StealthModule"]:
        log = logging.getLogger(logger_name)
        log.setLevel(getattr(logging, level.upper()))
        log.addHandler(console_handler)
        log.addHandler(file_handler)
    
    logger.info(f"Debug logging configured at {level} level")
