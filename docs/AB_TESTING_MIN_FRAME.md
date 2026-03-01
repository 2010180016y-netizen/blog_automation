# A/B 테스트 최소 프레임

네이버 블로그 스크립트 제약으로 인해 런타임 분기가 아닌 **발행 패키지 A/B 동시 생성** 방식으로 운영합니다.

## 1) 생성 결과 폴더 구조
동일 `content_id` 기준으로 variant A/B를 각각 생성합니다.

```text
docs/samples/naver_packages/
  ab_demo_001_A/
    post.html
    meta.json
    images/
      placeholder_1.txt
      placeholder_2.txt
      placeholder_3.txt
  ab_demo_001_B/
    post.html
    meta.json
    images/
      placeholder_1.txt
      placeholder_2.txt
      placeholder_3.txt
```

- `meta.json.cta_link`에는 `?variant=A` 또는 `?variant=B`가 자동 포함됩니다.
- A/B는 CTA 문구/위치를 다르게 생성합니다.
  - A: 상단 CTA + 문구 `지금 혜택 확인하기`
  - B: 하단 CTA + 문구 `최신 가격/리뷰 보고 결정하기`

## 2) variant 집계 예시
이벤트(`page_view`, `cta_click`, `store_click`)의 `metadata.variant`를 기준으로 집계합니다.

```json
{
  "content_id": "ab_demo_001",
  "winner": "B",
  "reason": "max_store_click_then_cta_click_then_ctr",
  "variants": [
    {
      "variant": "A",
      "views": 120,
      "clicks": 18,
      "store_clicks": 6,
      "cta_clicks": 12,
      "ctr": 15.0
    },
    {
      "variant": "B",
      "views": 118,
      "clicks": 24,
      "store_clicks": 11,
      "cta_clicks": 13,
      "ctr": 20.338983050847457
    }
  ]
}
```

- 승자 판단 기준: `store_click` > `cta_click` > `CTR`
