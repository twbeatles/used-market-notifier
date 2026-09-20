"""Package demo: render every default template for a sample listing."""

from .manager import MessageTemplateManager


def main() -> None:
    manager = MessageTemplateManager()

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


if __name__ == "__main__":
    main()
