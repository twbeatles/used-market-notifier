"""Built-in default seller message templates."""

from .template import MessageTemplate


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


__all__ = ["DEFAULT_TEMPLATES"]
