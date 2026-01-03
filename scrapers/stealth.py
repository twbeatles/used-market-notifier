# scrapers/stealth.py
"""
Advanced stealth module for bot detection bypass.
Implements comprehensive techniques to avoid detection by various anti-bot systems.
"""

import random
import logging
from typing import Optional
from playwright.async_api import BrowserContext, Page

logger = logging.getLogger("StealthModule")


# User-Agent rotation pool (real Chrome user agents)
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
]

# Viewport sizes (common screen resolutions)
VIEWPORTS = [
    {"width": 1920, "height": 1080},
    {"width": 1366, "height": 768},
    {"width": 1536, "height": 864},
    {"width": 1440, "height": 900},
    {"width": 1280, "height": 720},
]


def get_random_user_agent() -> str:
    """Get a random user agent from the pool"""
    return random.choice(USER_AGENTS)


def get_random_viewport() -> dict:
    """Get a random viewport size"""
    return random.choice(VIEWPORTS)


# Comprehensive stealth JavaScript
STEALTH_SCRIPTS = """
// ==========================================
// 1. WebDriver Detection Bypass
// ==========================================
Object.defineProperty(navigator, 'webdriver', {
    get: () => undefined,
    configurable: true
});

// Remove webdriver from prototype chain
delete Navigator.prototype.webdriver;

// ==========================================
// 2. Chrome Detection
// ==========================================
window.chrome = {
    runtime: {
        id: undefined,
        connect: function() {},
        sendMessage: function() {},
        onMessage: {
            addListener: function() {},
            removeListener: function() {}
        }
    },
    loadTimes: function() {},
    csi: function() {},
    app: {
        isInstalled: false
    }
};

// ==========================================
// 3. Plugins Detection
// ==========================================
Object.defineProperty(navigator, 'plugins', {
    get: () => {
        const plugins = [
            {
                name: 'Chrome PDF Plugin',
                filename: 'internal-pdf-viewer',
                description: 'Portable Document Format',
                length: 1
            },
            {
                name: 'Chrome PDF Viewer',
                filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai',
                description: '',
                length: 1
            },
            {
                name: 'Native Client',
                filename: 'internal-nacl-plugin',
                description: '',
                length: 2
            }
        ];
        plugins.item = (index) => plugins[index];
        plugins.namedItem = (name) => plugins.find(p => p.name === name);
        plugins.refresh = () => {};
        return plugins;
    },
    configurable: true
});

// ==========================================
// 4. Languages Detection
// ==========================================
Object.defineProperty(navigator, 'languages', {
    get: () => ['ko-KR', 'ko', 'en-US', 'en'],
    configurable: true
});

Object.defineProperty(navigator, 'language', {
    get: () => 'ko-KR',
    configurable: true
});

// ==========================================
// 5. Platform Detection
// ==========================================
Object.defineProperty(navigator, 'platform', {
    get: () => 'Win32',
    configurable: true
});

// ==========================================
// 6. Hardware Concurrency
// ==========================================
Object.defineProperty(navigator, 'hardwareConcurrency', {
    get: () => 8,
    configurable: true
});

// ==========================================
// 7. Device Memory
// ==========================================
Object.defineProperty(navigator, 'deviceMemory', {
    get: () => 8,
    configurable: true
});

// ==========================================
// 8. Max Touch Points
// ==========================================
Object.defineProperty(navigator, 'maxTouchPoints', {
    get: () => 0,
    configurable: true
});

// ==========================================
// 9. Permissions API
// ==========================================
const originalQuery = window.navigator.permissions?.query;
if (originalQuery) {
    window.navigator.permissions.query = (parameters) => {
        if (parameters.name === 'notifications') {
            return Promise.resolve({ state: 'denied', onchange: null });
        }
        return originalQuery.call(window.navigator.permissions, parameters);
    };
}

// ==========================================
// 10. WebGL Vendor/Renderer
// ==========================================
const getParameterProxyHandler = {
    apply: function(target, thisArg, argumentsList) {
        const param = argumentsList[0];
        const result = Reflect.apply(target, thisArg, argumentsList);
        
        // UNMASKED_VENDOR_WEBGL
        if (param === 37445) {
            return 'Google Inc. (NVIDIA)';
        }
        // UNMASKED_RENDERER_WEBGL
        if (param === 37446) {
            return 'ANGLE (NVIDIA, NVIDIA GeForce GTX 1080 Direct3D11 vs_5_0 ps_5_0, D3D11)';
        }
        return result;
    }
};

const webglContexts = ['webgl', 'experimental-webgl', 'webgl2', 'experimental-webgl2'];
webglContexts.forEach(contextName => {
    const originalGetContext = HTMLCanvasElement.prototype.getContext;
    HTMLCanvasElement.prototype.getContext = function(type, ...args) {
        const context = originalGetContext.apply(this, [type, ...args]);
        if (context && webglContexts.includes(type)) {
            const originalGetParameter = context.getParameter.bind(context);
            context.getParameter = new Proxy(originalGetParameter, getParameterProxyHandler);
        }
        return context;
    };
});

// ==========================================
// 11. Iframe contentWindow
// ==========================================
Object.defineProperty(HTMLIFrameElement.prototype, 'contentWindow', {
    get: function() {
        return null;
    }
});

// ==========================================
// 12. Console Debug Detection
// ==========================================
const consoleDebugOverride = () => undefined;
Object.defineProperty(console, 'debug', { value: consoleDebugOverride });

// ==========================================
// 13. Auto-dismiss Alerts
// ==========================================
window.alert = () => {};
window.confirm = () => true;
window.prompt = () => '';

// ==========================================
// 14. Canvas Fingerprint Protection
// ==========================================
const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
HTMLCanvasElement.prototype.toDataURL = function(type) {
    if (type === 'image/png' && this.width === 16 && this.height === 16) {
        // Add small noise to fingerprint canvas
        const ctx = this.getContext('2d');
        if (ctx) {
            const imageData = ctx.getImageData(0, 0, this.width, this.height);
            for (let i = 0; i < imageData.data.length; i += 4) {
                imageData.data[i] = imageData.data[i] ^ (Math.random() > 0.99 ? 1 : 0);
            }
            ctx.putImageData(imageData, 0, 0);
        }
    }
    return originalToDataURL.apply(this, arguments);
};

// ==========================================
// 15. AudioContext Fingerprint
// ==========================================
const originalCreateOscillator = AudioContext.prototype.createOscillator;
AudioContext.prototype.createOscillator = function() {
    const osc = originalCreateOscillator.apply(this, arguments);
    osc.frequency.value = osc.frequency.value + Math.random() * 0.0001;
    return osc;
};

console.log('[Stealth] All protections applied');
"""


async def apply_full_stealth(context: BrowserContext):
    """
    Apply comprehensive stealth techniques to browser context.
    This bypasses most common bot detection systems.
    """
    await context.add_init_script(STEALTH_SCRIPTS)
    logger.info("Full stealth mode applied with 15 protection techniques")


async def apply_human_behavior(page: Page, delay_range: tuple = (100, 300)):
    """
    Apply human-like behavior patterns to page interactions.
    
    Args:
        page: Playwright page object
        delay_range: Random delay range in milliseconds (min, max)
    """
    # Random mouse movements
    await page.evaluate("""
        (delay) => {
            document.addEventListener('mousemove', () => {
                // Add slight random delay to movements
                return new Promise(r => setTimeout(r, delay));
            });
        }
    """, random.randint(*delay_range))


async def random_delay(min_ms: int = 500, max_ms: int = 2000):
    """Add random delay to mimic human behavior"""
    import asyncio
    delay = random.randint(min_ms, max_ms) / 1000
    await asyncio.sleep(delay)


async def scroll_like_human(page: Page, scroll_count: int = 3):
    """
    Scroll page in human-like pattern.
    
    Args:
        page: Playwright page object
        scroll_count: Number of scroll actions
    """
    for _ in range(scroll_count):
        scroll_amount = random.randint(200, 500)
        await page.evaluate(f"window.scrollBy(0, {scroll_amount})")
        await random_delay(300, 800)


async def type_like_human(page: Page, selector: str, text: str):
    """
    Type text with human-like delays between keystrokes.
    
    Args:
        page: Playwright page object
        selector: Element selector
        text: Text to type
    """
    element = await page.query_selector(selector)
    if element:
        for char in text:
            await element.type(char, delay=random.randint(50, 150))
            

async def check_bot_detection(page: Page) -> dict:
    """
    Check common bot detection indicators on the page.
    
    Returns:
        Dict with detection check results
    """
    results = await page.evaluate("""
        () => {
            return {
                webdriver: navigator.webdriver,
                chrome: !!window.chrome,
                plugins: navigator.plugins.length,
                languages: navigator.languages.length,
                platform: navigator.platform,
                hardwareConcurrency: navigator.hardwareConcurrency,
                deviceMemory: navigator.deviceMemory,
                hasFocus: document.hasFocus(),
                hidden: document.hidden,
                userAgent: navigator.userAgent,
            };
        }
    """)
    
    # Log detection status
    is_detected = results.get('webdriver', False)
    logger.info(f"Bot detection check: {'⚠️ DETECTED' if is_detected else '✅ PASSED'}")
    logger.debug(f"Detection details: {results}")
    
    return results
