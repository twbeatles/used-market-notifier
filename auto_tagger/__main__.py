"""Package demo: tag sample titles."""

from .tagger import AutoTagger


def main() -> None:
    tagger = AutoTagger()

    test_titles = [
        "맥북 프로 M2 A급 풀박스 정품",
        "아이폰 15 급처 네고가능",
        "갤럭시 S24 택포 직거래",
        "맥북 에어 중고",
        "에어팟 프로 미개봉 새제품"
    ]

    for title in test_titles:
        tags = tagger.analyze(title)
        detailed = tagger.analyze_detailed(title)
        print(f"\n'{title}'")
        print(f"  Tags: {tags}")
        for t in detailed:
            print(f"    - {t.icon} {t.tag_name} (matched: '{t.matched_keyword}')")


if __name__ == "__main__":
    main()
