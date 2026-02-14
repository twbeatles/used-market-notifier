# message_templates.py
"""Message template system for quick seller communication"""

from dataclasses import dataclass
from typing import List, Dict, Optional
import re


@dataclass
class MessageTemplate:
    """Template for seller messages with variable substitution"""
    name: str
    content: str
    platform: str = "all"  # "all", "danggeun", "bunjang", "joonggonara"
    
    def render(self, context: Dict[str, str]) -> str:
        """
        Render template with context variables.
        
        Available variables:
            {title} - Listing title
            {price} - Listed price
            {seller} - Seller name
            {location} - Location
            {target_price} - User's target price (if set)
            {platform} - Platform name
        """
        result = self.content
        for key, value in context.items():
            placeholder = "{" + key + "}"
            result = result.replace(placeholder, str(value) if value else "")
        
        # Clean up any remaining placeholders
        result = re.sub(r'\{[^}]+\}', '', result)
        return result.strip()


class MessageTemplateManager:
    """Manages message templates for seller communication"""
    
    DEFAULT_TEMPLATES = [
        MessageTemplate(
            name="기본 문의",
            content="안녕하세요! {title} 상품 문의드립니다.\n아직 판매중인가요?",
            platform="all"
        ),
        MessageTemplate(
            name="가격 문의",
            content="안녕하세요! {title} 보고 연락드립니다.\n현재 {price}에 판매중이신 것 같은데, 혹시 조금 네고 가능할까요?",
            platform="all"
        ),
        MessageTemplate(
            name="직거래 문의",
            content="안녕하세요! {title} 구매 희망합니다.\n{location} 근처에서 직거래 가능하실까요?",
            platform="all"
        ),
        MessageTemplate(
            name="상태 문의",
            content="안녕하세요! {title} 관심있습니다.\n상세한 상태와 사용 기간이 어떻게 되나요?",
            platform="all"
        ),
        MessageTemplate(
            name="구성품 문의",
            content="안녕하세요! {title} 문의드립니다.\n구성품이 어떻게 되나요? 박스와 충전기 포함인가요?",
            platform="all"
        ),
        MessageTemplate(
            name="당근 안부인사",
            content="안녕하세요, {location} 이웃입니다! 😊\n{title} 아직 구매 가능한가요?",
            platform="danggeun"
        ),
        MessageTemplate(
            name="번개장터 빠른문의",
            content="⚡ 안녕하세요!\n{title} 바로 구매 가능할까요?",
            platform="bunjang"
        ),
    ]
    
    def __init__(self, custom_templates: List[MessageTemplate] = None):
        """
        Initialize with optional custom templates.
        
        Args:
            custom_templates: List of custom templates (overrides defaults if provided)
        """
        self.templates = custom_templates if custom_templates else self.DEFAULT_TEMPLATES.copy()
    
    def get_templates(self, platform: str = None) -> List[MessageTemplate]:
        """
        Get templates, optionally filtered by platform.
        
        Args:
            platform: Filter by platform ("danggeun", "bunjang", "joonggonara", or None for all)
            
        Returns:
            List of applicable templates
        """
        if not platform:
            return self.templates
        
        return [
            t for t in self.templates 
            if t.platform == "all" or t.platform == platform
        ]
    
    def render_template(self, template_name: str, context: Dict[str, str]) -> Optional[str]:
        """
        Render a template by name with the given context.
        
        Args:
            template_name: Name of the template to use
            context: Variable substitution context
            
        Returns:
            Rendered message string or None if template not found
        """
        for template in self.templates:
            if template.name == template_name:
                return template.render(context)
        return None
    
    def add_template(self, name: str, content: str, platform: str = "all"):
        """Add a new template"""
        self.templates.append(MessageTemplate(
            name=name,
            content=content,
            platform=platform
        ))
    
    def update_template(self, name: str, content: str = None, platform: str = None):
        """Update an existing template"""
        for template in self.templates:
            if template.name == name:
                if content is not None:
                    template.content = content
                if platform is not None:
                    template.platform = platform
                break
    
    def remove_template(self, name: str):
        """Remove a template by name"""
        self.templates = [t for t in self.templates if t.name != name]
    
    def get_available_variables(self) -> List[str]:
        """Get list of available template variables"""
        return [
            "{title} - 상품 제목",
            "{price} - 판매 가격",
            "{seller} - 판매자 이름",
            "{location} - 지역",
            "{target_price} - 목표 가격",
            "{platform} - 플랫폼 이름"
        ]
    
    @staticmethod
    def copy_to_clipboard(text: str) -> bool:
        """
        Copy text to system clipboard.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            from PyQt6.QtWidgets import QApplication
            from PyQt6.QtGui import QClipboard
            
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            return True
        except Exception:
            # Fallback for non-PyQt environments
            try:
                import pyperclip
                pyperclip.copy(text)
                return True
            except ImportError:
                pass
        return False
    
    def create_context_from_listing(self, listing: dict, target_price: int = None) -> Dict[str, str]:
        """
        Create a context dict from a listing dict.
        
        Args:
            listing: Listing data dict
            target_price: Optional target price to include
            
        Returns:
            Context dict for template rendering
        """
        platform_names = {
            'danggeun': '당근마켓',
            'bunjang': '번개장터',
            'joonggonara': '중고나라'
        }
        
        return {
            'title': listing.get('title', ''),
            'price': listing.get('price', ''),
            'seller': listing.get('seller', ''),
            'location': listing.get('location', ''),
            'platform': platform_names.get(listing.get('platform', ''), listing.get('platform', '')),
            'target_price': f"{target_price:,}원" if target_price else '',
        }


if __name__ == "__main__":
    # Test message templates
    manager = MessageTemplateManager()
    
    # Test listing
    test_listing = {
        'title': '맥북 프로 M2 14인치',
        'price': '1,500,000원',
        'seller': '홍길동',
        'location': '서울 강남구',
        'platform': 'danggeun'
    }
    
    context = manager.create_context_from_listing(test_listing, target_price=1400000)
    
    print("Available templates:")
    for template in manager.get_templates():
        print(f"\n[{template.name}] ({template.platform})")
        rendered = template.render(context)
        print(rendered)
