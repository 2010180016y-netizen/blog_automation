import express from "express";
import { createServer as createViteServer } from "vite";
import Database from "better-sqlite3";
import { GoogleGenAI } from "@google/genai";
import fetch from "node-fetch";

const db = new Database("blogs.db");
db.exec(`
  CREATE TABLE IF NOT EXISTS blogs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic TEXT,
    content TEXT,
    meta_description TEXT,
    product_link TEXT,
    platform TEXT DEFAULT 'wordpress', -- wordpress, naver
    quality_notes TEXT,
    hashtags TEXT,
    disclaimer TEXT,
    audit_score INTEGER,
    audit_fails TEXT,
    audit_warns TEXT,
    audit_checklist TEXT,
    disclosure_type TEXT,
    video_link TEXT,
    page_type TEXT,
    personal_data TEXT,
    category TEXT,
    status TEXT DEFAULT 'published',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
  );

  CREATE TABLE IF NOT EXISTS keywords (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword TEXT UNIQUE,
    volume INTEGER,
    competition_ratio REAL,
    status TEXT DEFAULT 'sourced', -- sourced, planned, generated
    outline TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
  );

  CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sku TEXT,
    name TEXT,
    usp TEXT,
    target TEXT,
    price INTEGER,
    shipping TEXT,
    usage TEXT,
    precautions TEXT,
    faq TEXT,
    product_link TEXT,
    options TEXT,
    as_info TEXT,
    prohibited_expressions TEXT,
    mandatory_disclaimer TEXT,
    evidence_data TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
  );
`);

try { db.exec("ALTER TABLE blogs ADD COLUMN meta_description TEXT"); } catch(e) {}
try { db.exec("ALTER TABLE blogs ADD COLUMN status TEXT DEFAULT 'published'"); } catch(e) {}
try { db.exec("ALTER TABLE blogs ADD COLUMN platform TEXT DEFAULT 'wordpress'"); } catch(e) {}
try { db.exec("ALTER TABLE blogs ADD COLUMN quality_notes TEXT"); } catch(e) {}
try { db.exec("ALTER TABLE blogs ADD COLUMN hashtags TEXT"); } catch(e) {}
try { db.exec("ALTER TABLE blogs ADD COLUMN disclaimer TEXT"); } catch(e) {}
try { db.exec("ALTER TABLE blogs ADD COLUMN audit_score INTEGER"); } catch(e) {}
try { db.exec("ALTER TABLE blogs ADD COLUMN audit_fails TEXT"); } catch(e) {}
try { db.exec("ALTER TABLE blogs ADD COLUMN audit_warns TEXT"); } catch(e) {}
try { db.exec("ALTER TABLE blogs ADD COLUMN audit_checklist TEXT"); } catch(e) {}
try { db.exec("ALTER TABLE blogs ADD COLUMN disclosure_type TEXT"); } catch(e) {}
try { db.exec("ALTER TABLE blogs ADD COLUMN video_link TEXT"); } catch(e) {}
try { db.exec("ALTER TABLE blogs ADD COLUMN page_type TEXT"); } catch(e) {}
try { db.exec("ALTER TABLE blogs ADD COLUMN category TEXT"); } catch(e) {}
try { db.exec("ALTER TABLE blogs ADD COLUMN performance_score INTEGER DEFAULT 0"); } catch(e) {}
try { db.exec("ALTER TABLE blogs ADD COLUMN is_winning_template INTEGER DEFAULT 0"); } catch(e) {}
try { db.exec("ALTER TABLE products ADD COLUMN options TEXT"); } catch(e) {}
try { db.exec("ALTER TABLE products ADD COLUMN as_info TEXT"); } catch(e) {}
try { db.exec("ALTER TABLE products ADD COLUMN prohibited_expressions TEXT"); } catch(e) {}
try { db.exec("ALTER TABLE products ADD COLUMN mandatory_disclaimer TEXT"); } catch(e) {}
try { db.exec("ALTER TABLE products ADD COLUMN evidence_data TEXT"); } catch(e) {}

const COMMON_CONTEXT_YAML = `
project:
  name: "Content-Commerce OS"
  goal: ["검색 유입", "블로그→스토어 전환", "영문 구글 유입", "광고 수익(선택)"]
channels:
  naver_blog:
    language: "ko"
    publish_mode: "human_final_click"
    content_types: ["정보형", "스토리형", "리뷰형", "비교형"]
  wordpress:
    language: "en"
    publish_mode: "auto_draft_then_schedule"
    site_url: ""
    wp_api_base: ""
commerce:
  naver_smartstore:
    enabled: true
    store_url: ""
content_sources:
  video_assets_dir: "./assets/videos"
  image_assets_dir: "./assets/images"
  product_db: "sqlite:blogs.db"
  faq_db: "sqlite:blogs.db"
tracking:
  link_params:
    channel_param: "ch"
    content_id_param: "cid"
    sku_param: "sku"
    intent_param: "intent"
analytics:
  ga4_enabled: true
  ga4_measurement_id: ""
tech_stack:
  language: "typescript"
  runtime: "node"
  api_framework: "express"
  db: "sqlite"
llm:
  enabled: true
  provider: "gemini"
  usage: ["rewrite", "quality_review", "alt_text", "fix_plan"]
policies:
  ymyL_categories: ["건강", "금융", "세금", "법률"]
  disclosure_required: true
`;

const COMPLIANCE_RULESET = `
[컴플라이언스 룰셋]
compliance:
  categories: ["뷰티", "리빙", "식품", "건기식"]
  banned_claims:
    ko: ["무조건", "완치", "보장", "부작용 없음", "100%", "특효", "직효"]
    en: ["guaranteed", "cure", "no side effects", "100%", "miracle", "instant fix"]
  required_disclosures:
    ko: ["광고", "협찬", "제휴"]
    en: ["sponsored", "affiliate"]
  required_sections:
    common: ["주의사항", "FAQ"]
    ymyL: ["면책", "기준/가정"]
  product_page_claims_source: ["제조사 공식 설명", "직접 사용기", "성분표/스펙"]
`;

async function startServer() {
  const app = express();
  app.use(express.json());
  const PORT = 3000;

  // Seed Data for Products (10 Examples for 4050 Women)
  const productCount = db.prepare("SELECT COUNT(*) as count FROM products").get() as any;
  if (productCount.count === 0) {
    const seedProducts = [
      {
        sku: 'H-001', name: '식물성 초임계 알티지 오메가3', price: 35000,
        usp: '1. 저온 초임계 추출로 산패 위험 최소화\n2. 중금속 걱정 없는 미세조류 유래\n3. 체내 흡수율 높은 rTG 형태',
        target: '혈행 개선 및 건조한 눈이 고민인 4050 여성',
        shipping: '무료배송 / 익일도착', usage: '1일 1회, 1회 1캡슐 물과 함께 섭취',
        precautions: '특이체질, 알레르기 체질의 경우 성분 확인 후 섭취',
        faq: 'Q: 비린내가 나나요?\nA: 식물성 원료와 레몬 오일 첨가로 비린내를 잡았습니다.',
        product_link: 'https://smartstore.naver.com/example/products/1'
      },
      {
        sku: 'B-002', name: '저분자 콜라겐 펩타이드 3000', price: 42000,
        usp: '1. 평균 분자량 300Da 초저분자\n2. 식약처 기능성 인정 피부 건강 원료\n3. 비타민C, 엘라스틴, 히알루론산 배합',
        target: '피부 탄력과 보습이 필요한 중년 여성',
        shipping: '무료배송', usage: '취침 전 1포 직접 섭취',
        precautions: '임산부 및 수유부는 의사와 상담 후 섭취',
        faq: 'Q: 언제 먹는게 좋나요?\nA: 피부 재생이 활발한 밤 10시~새벽 2시 사이 섭취를 권장합니다.',
        product_link: 'https://smartstore.naver.com/example/products/2'
      },
      {
        sku: 'L-003', name: '순수 퓨어 실크 베개 커버', price: 58000,
        usp: '1. 22맘미 최고급 뽕나무 실크\n2. 머리카락 엉킴 및 피부 마찰 최소화\n3. 천연 항균 및 온도 조절 기능',
        target: '수면 중 피부 관리와 헤어 케어를 원하는 여성',
        shipping: '배송비 3,000원', usage: '베개에 씌워 사용 (중성세제 손세탁 권장)',
        precautions: '고온 세탁 및 건조기 사용 금지',
        faq: 'Q: 세탁이 번거롭지 않나요?\nA: 실크 전용 세제로 가볍게 손세탁 후 그늘에서 말리면 오래 사용 가능합니다.',
        product_link: 'https://smartstore.naver.com/example/products/3'
      },
      {
        sku: 'H-004', name: '유기농 효소 밸런스 365', price: 28000,
        usp: '1. 100% 국내산 유기농 곡물 발효\n2. 역가수치 50만 유닛 보장\n3. 정제효소 무첨가 원칙',
        target: '식후 속이 더부룩하고 소화가 안 되는 4050',
        shipping: '무료배송', usage: '식후 1포 물 없이 섭취',
        precautions: '직사광선을 피해 서늘한 곳에 보관',
        faq: 'Q: 맛이 어떤가요?\nA: 고소한 인절미 맛으로 거부감 없이 섭취 가능합니다.',
        product_link: 'https://smartstore.naver.com/example/products/4'
      },
      {
        sku: 'B-005', name: '비건 세라마이드 보습 크림', price: 32000,
        usp: '1. 5중 복합 비건 세라마이드\n2. 100시간 보습 지속력 테스트 완료\n3. 민감성 피부 저자극 테스트 완료',
        target: '겨울철 극심한 건조함과 가려움을 느끼는 피부',
        shipping: '무료배송', usage: '기초 마지막 단계에서 부드럽게 펴 바름',
        precautions: '상처가 있는 부위에는 사용 자제',
        faq: 'Q: 끈적임이 심한가요?\nA: 고보습이지만 흡수력이 빨라 산뜻하게 마무리됩니다.',
        product_link: 'https://smartstore.naver.com/example/products/5'
      },
      {
        sku: 'H-006', name: '루테인 지아잔틴 아스타잔틴', price: 39000,
        usp: '1. 황반 중심부터 주변부까지 복합 케어\n2. 눈 피로 개선을 위한 아스타잔틴 함유\n3. 개별 PTP 포장으로 산패 방지',
        target: '노안이 시작되거나 스마트폰 사용이 많은 중년',
        shipping: '무료배송', usage: '1일 1회 1캡슐 식후 섭취',
        precautions: '과다 섭취 시 일시적으로 피부가 황색으로 변할 수 있음',
        faq: 'Q: 아침에 먹나요 저녁에 먹나요?\nA: 지용성 성분이므로 식사 직후에 드시는 것이 흡수에 좋습니다.',
        product_link: 'https://smartstore.naver.com/example/products/6'
      },
      {
        sku: 'L-007', name: '편백나무 경추 베개', price: 45000,
        usp: '1. 100% 국내산 편백나무 큐브\n2. C자 커브 유지를 위한 인체공학 설계\n3. 높이 조절 가능한 지퍼형 구조',
        target: '목 어깨 결림과 불면증이 있는 4050',
        shipping: '배송비 3,000원', usage: '목의 C자 곡선에 맞춰 베고 취침',
        precautions: '편백 큐브는 세탁하지 말고 햇볕에 말려 살균',
        faq: 'Q: 너무 딱딱하지 않나요?\nA: 처음에는 어색할 수 있으나 적응되면 경추 건강에 매우 효과적입니다.',
        product_link: 'https://smartstore.naver.com/example/products/7'
      },
      {
        sku: 'H-008', name: '여성용 리포좀 비타민C', price: 48000,
        usp: '1. 흡수율을 높인 리포좀 제형 기술\n2. 위장 장애 없는 중성 비타민\n3. 항산화 및 에너지 대사 복합 기능성',
        target: '만성 피로와 면역력 저하를 느끼는 여성',
        shipping: '무료배송', usage: '공복 또는 식후 관계없이 1일 1캡슐',
        precautions: '신장 결석 등 질환이 있는 경우 전문가 상담',
        faq: 'Q: 일반 비타민C와 뭐가 다른가요?\nA: 인체 세포막과 유사한 구조로 감싸 흡수율을 획기적으로 높였습니다.',
        product_link: 'https://smartstore.naver.com/example/products/8'
      },
      {
        sku: 'B-009', name: '약산성 여성청결제 폼', price: 19000,
        usp: '1. pH 4.5~5.5 약산성 밸런스 유지\n2. 쑥, 티트리 등 천연 유래 진정 성분\n3. 유해 성분 20가지 무첨가',
        target: 'Y존 건강과 청결 관리가 필요한 여성',
        shipping: '배송비 2,500원', usage: '적당량을 덜어 세정 후 미온수로 헹굼',
        precautions: '외음부에만 사용하고 질 내 세척은 자제',
        faq: 'Q: 매일 사용해도 되나요?\nA: 순한 성분으로 매일 사용 가능하지만 주 2~3회 사용을 권장합니다.',
        product_link: 'https://smartstore.naver.com/example/products/9'
      },
      {
        sku: 'H-010', name: '보스웰리아 추출물 분말', price: 33000,
        usp: '1. 인도산 프리미엄 보스웰리아 100%\n2. 보스웰릭산 65% 이상 고농축\n3. 쇳가루 등 이물질 불검출 테스트 완료',
        target: '계단 오르내리기가 힘든 무릎 관절 고민층',
        shipping: '무료배송', usage: '물이나 요거트에 1~2g 섞어서 섭취',
        precautions: '특유의 향이 강할 수 있으니 음료와 함께 섭취 권장',
        faq: 'Q: 가루가 잘 녹나요?\nA: 찬물에는 잘 안 녹을 수 있으니 미온수나 요거트를 추천합니다.',
        product_link: 'https://smartstore.naver.com/example/products/10'
      }
    ];

    const insertStmt = db.prepare(`
      INSERT INTO products (sku, name, usp, target, price, shipping, usage, precautions, faq, product_link)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `);
    seedProducts.forEach(p => {
      insertStmt.run(p.sku, p.name, p.usp, p.target, p.price, p.shipping, p.usage, p.precautions, p.faq, p.product_link);
    });
  }
  app.post("/api/generate", async (req, res) => {
    const { 
      topic, 
      productLink, 
      productId, 
      platform = 'wordpress', 
      disclosureType = 'none', 
      pageType = 'review',
      category = 'General',
      videoLink = '',
      personalData = '',
      schedule = false 
    } = req.body;
    
    if (!process.env.GEMINI_API_KEY) {
      return res.status(500).json({ error: "GEMINI_API_KEY is not set" });
    }

    let productMetadata = "";
    let finalProductLink = productLink;
    let productSku = "N/A";

    if (productId) {
      const product = db.prepare("SELECT * FROM products WHERE id = ?").get(productId) as any;
      if (product) {
        productSku = product.sku;
        productMetadata = `
        [상품 정보 (SSOT)]
        상품명: ${product.name}
        SKU: ${product.sku}
        핵심 USP: ${product.usp}
        타겟: ${product.target}
        가격: ${product.price}
        옵션: ${product.options || "N/A"}
        배송: ${product.shipping}
        A/S 정보: ${product.as_info || "N/A"}
        사용법: ${product.usage}
        주의사항: ${product.precautions}
        금지 표현: ${product.prohibited_expressions || "N/A"}
        필수 면책 문구: ${product.mandatory_disclaimer || "N/A"}
        증거 데이터(사용로그/테스트): ${product.evidence_data || "N/A"}
        FAQ: ${product.faq}
        `;
        finalProductLink = product.product_link;
      }
    }

    // 수익 자동화: 트래킹 링크 생성 (Tracking Link Generator)
    if (finalProductLink && finalProductLink.startsWith('http')) {
      try {
        const url = new URL(finalProductLink);
        url.searchParams.set('channel', platform === 'naver' ? 'naver' : 'wp');
        url.searchParams.set('sku', productSku);
        url.searchParams.set('intent', pageType);
        url.searchParams.set('utm_source', platform);
        url.searchParams.set('utm_medium', 'automation_os');
        // content_id는 저장 후 확정되므로 생성 시점에는 topic이나 timestamp를 임시로 활용하거나 
        // LLM에게 파라미터 구조를 유지하도록 지시
        finalProductLink = url.toString();
      } catch (e) {
        console.error("URL Parsing error:", e);
      }
    }

    try {
      const ai = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY });
      const model = "gemini-3.1-pro-preview";

      // Disclosure Guidance
      const disclosureMap: Record<string, string> = {
        'ad': '[광고] 본 포스팅은 해당 업체로부터 소정의 원고료를 제공받아 작성되었습니다.',
        'sponsor': '[협찬] 본 포스팅은 해당 업체로부터 제품을 무상으로 제공받아 실제 사용 후 작성되었습니다.',
        'affiliate': '[제휴] 본 포스팅은 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받을 수 있습니다.',
        'none': ''
      };
      const disclosureHeader = disclosureMap[disclosureType] || '';

      // Step 1: Problem/Situation & Pain-point Analysis
      const step1Prompt = `
      ${COMMON_CONTEXT_YAML}
      ${COMPLIANCE_RULESET}
      
      상황/문제: "${topic}"
      타겟: 4050 여성 (건강/리빙/뷰티 관심층)
      페이지 타입: ${pageType} (정보성, 리뷰, 비교, 가이드, 스토리 중 하나)
      ${videoLink ? `참고 영상 링크: ${videoLink}` : ""}
      ${personalData ? `나만의 데이터(경험/측정값): ${personalData}` : ""}
      ${productMetadata ? `연관 상품 정보: ${productMetadata}` : ""}
      
      이 상황에서 타겟이 느끼는 심리적 불안감, 신체적 고통, 그리고 기존 해결책에 대해 느꼈던 불만을 3가지로 도출해줘.
      또한, 이 문제를 해결하기 위한 '핵심 가치 제안(Value Proposition)'을 하나 만들어줘.
      
      JSON 형식으로 응답해줘: 
      {
        "pain_points": ["...", "...", "..."],
        "value_prop": "..."
      }
      `;
      const step1Result = await ai.models.generateContent({
        model,
        contents: [{ parts: [{ text: step1Prompt }] }],
        config: { responseMimeType: "application/json" }
      });
      const { pain_points, value_prop } = JSON.parse(step1Result.text);

      // Step 2: Main Copywriting based on Platform
      const RED_LINE_POLICY = `
      [건기식 심의 방어 정책]
      - 질병의 '치료', '예방', '완치', '특효', '직효' 등의 단어 절대 금지.
      - 대체 워딩: "증상 완화에 도움을 줄 수 있음", "식약처 기능성 인정 원료", "건강 유지에 필요한", "영양 보충에 도움"
      `;

      // Internal Linking Logic
      const relatedPosts = db.prepare("SELECT id, topic, category FROM blogs WHERE category = ? AND id != ? ORDER BY created_at DESC LIMIT 3").all(category, -1) as any[];
      const internalLinksContext = relatedPosts.length > 0 
        ? `[내부 링크 후보 (Internal Links)]
           다음은 같은 카테고리의 이전 글들입니다. 본문 하단에 '함께 읽으면 좋은 글' 섹션을 만들고, 
           단순 키워드 나열이 아닌 "다음 행동 유도형(Action-oriented)" 앵커 텍스트를 사용하여 링크를 생성하세요.
           (링크 형식: [앵커 텍스트](#blog-id-ID))
           ${relatedPosts.map(p => `- 주제: ${p.topic} (ID: ${p.id})`).join('\n')}
          `
        : "";

      const platformGuidance = platform === 'naver' 
        ? `[네이버 블로그 스타일 가이드]
           - 친근하고 개인적인 경험담 톤 (블로그 이웃에게 말하듯)
           - 이모지 적절히 사용
           - 가독성 좋은 짧은 문단
           - 정보성 위주로 작성하되 마지막에 자연스러운 추천`
        : `[워드프레스 글로벌 스타일 가이드]
           - 전문적이고 신뢰감 있는 톤
           - 논리적인 구조 (H2, H3 명확히 사용)
           - SEO 최적화된 문장 구조`;

      const intentTemplates: Record<string, string> = {
        'info': `[구조: 정보형]
                 1. 문제 정의 (유저가 겪는 상황 공감)
                 2. 원인 및 해결 기준 제시 (객관적 정보)
                 3. 다양한 해결 옵션 설명
                 4. 결론: 제품을 해결 옵션 중 하나로 자연스럽게 제안`,
        'review': `[구조: 리뷰형]
                   1. 사용 환경 및 기대치 (왜 이 제품을 찾게 되었나)
                   2. 첫인상 및 언박싱 느낌
                   3. 디테일 분석 (실제 사용 로그, 장단점, 증거 데이터 활용)
                   4. 결론: 어떤 사람에게 이 제품이 맞는지 추천`,
        'comparison': `[구조: 비교형]
                       1. 비교 기준표 제시 (성분, 가격, 편의성 등)
                       2. 케이스별 추천 (A상황엔 이거, B상황엔 이거)
                       3. 최종 결론 및 선택 가이드`,
        'story': `[구조: 스토리형]
                  1. 상황 발생 (강렬한 문제 상황 묘사)
                  2. 시행착오 과정 (다른 제품 실패담 등)
                  3. 이 제품을 선택하게 된 결정적 이유
                  4. 사용 후 변화 및 주의점`,
        'guide': `[구조: 가이드형]
                  1. 단계별 사용법 (Step-by-Step)
                  2. 효과를 극대화하는 꿀팁
                  3. 자주 하는 실수 및 주의사항`
      };

      const UNIQUE_PACK_POLICY = `
      [Unique Pack: 스팸 방지 및 신뢰도 향상 장치]
      다음 중 최소 2개 이상을 본문에 반드시 포함하세요:
      1. [이미지 가이드] 직접 촬영한 사진이 들어갈 위치를 [사진: 전/후 비교] 또는 [사진: 실제 제형] 형태로 표시
      2. [체크리스트] "구매 전 반드시 확인해야 할 5가지" 또는 "이런 분들께 추천합니다" 체크리스트
      3. [실제 사용 조건] "하루 2회, 식후 30분, 7일간 꾸준히"와 같은 구체적인 가이드
      4. [비교 기준표] 타사 제품이나 기존 방식과의 차별점을 보여주는 마크다운 표(Table)
      5. [FAQ] 실제 고객들이 자주 묻는 질문 2~3가지 (상품 정보의 FAQ 활용)
      `;

      const AD_LAYOUT_POLICY = `
      [AdSense 정책 및 UX 레이아웃 엔진]
      1. [우발 클릭 방지] 구매 버튼(CTA)이나 주요 링크 주변에는 최소 2줄 이상의 텍스트 여백을 두어 광고와 겹치지 않게 하세요.
      2. [신뢰 우선 배치] 본문 하단 CTA 바로 뒤에는 광고가 아닌 '주의사항' 또는 'FAQ' 섹션을 먼저 배치하여 신뢰도를 높인 후, 그 다음에 광고/추천 섹션을 배치하세요.
      3. [모바일 최적화] 모바일 가독성을 위해 문단을 짧게 유지하고, 섹션 사이의 여백을 명확히 하세요.
      `;

      const YMYL_COMPLIANCE_POLICY = `
      [YMYL 및 컴플라이언스 엔진]
      1. [카테고리별 안전 문구] 
         - 건강/영양제: "본 정보는 질병의 진단 및 치료를 위한 의학적 정보가 아니며, 개인의 체질에 따라 효과가 다를 수 있습니다."
         - 다이어트: "적절한 운동과 식이조절을 병행해야 하며, 무리한 감량은 건강을 해칠 수 있습니다."
      2. [과장 표현 방지] "무조건", "100%", "완치", "최고" 등 검증되지 않은 절대적 표현을 지양하고 "도움을 줄 수 있는", "기대할 수 있는" 등의 완곡한 표현을 사용하세요.
      3. [제휴 고지] 본문 하단에 "이 포스팅은 제휴 마케팅 활동의 일환으로 일정액의 수수료를 제공받을 수 있습니다." 문구를 자연스럽게 포함하세요.
      `;

      const NAVER_SAFE_STRUCTURE = `
      [네이버 세이프 구조 장치]
      1. [도입부 (첫 3줄)] "누구에게 / 어떤 상황에 / 무엇을 해결"하는지 명확하게 제시하여 유저의 이탈을 막으세요.
      2. [중간부 (유저 효용)] 체크리스트, 비교표, 구체적 사용팁 등 유저가 바로 활용 가능한 실용적 정보를 배치하세요.
      3. [하단부 (신뢰/수익)] FAQ -> 주의사항 -> CTA(스토어 링크) 순서로 배치하여 신뢰를 먼저 쌓고 구매를 유도하세요.
      `;

      const REPETITION_PREVENTION_POLICY = `
      [반복 및 유사도 방지 정책]
      동일 상품에 대한 중복 발행 시 다음 요소를 강제로 다르게 구성하세요:
      - 후킹 문장 (첫 문장)
      - 소제목 (H2, H3)
      - 활용 예시 및 에피소드
      - FAQ 질문과 답변의 구성
      `;

      const EXPERIENCE_SIGNAL_POLICY = `
      [실제 경험 신호 주입 엔진]
      1. [구체적 컨텍스트] 단순히 제품 장점을 나열하지 말고, "어떤 상황에서(예: 아침 공복에)", "얼마나(예: 2주간 꾸준히)", "왜(예: 환절기 비염 때문에)" 사용했는지 구체적인 경험 신호를 주입하세요.
      2. [선택 기준 제시] 왜 수많은 제품 중 이 제품을 선택했는지에 대한 나만의 기준(예: 성분 함량, 가성비, 브랜드 신뢰도 등)을 논리적으로 설명하세요.
      3. [이미지 앵커링] 사진이 들어갈 위치에 [사진: 실제 제형 확인], [사진: 섭취 전후 컨디션 기록] 등 구체적인 캡션을 달아주세요.
      `;

      const COMMERCIAL_BALANCE_POLICY = `
      [외부 링크 및 상업성 균형 정책]
      1. [7:3 법칙] 본문의 70%는 정보 제공, 경험 공유, 비교 분석으로 채우고, 직접적인 판매 유도(CTA)는 30% 이하로 제한하세요.
      2. [링크 피로도 관리] 본문 전체에서 외부 링크(트래킹 링크)는 최대 2~3회만 노출하세요. (중간 1회, 하단 1회 권장)
      3. [가치 우선] "사세요"가 아니라 "이런 정보가 있으니 참고하시고, 필요하면 여기서 확인하세요"라는 톤을 유지하세요.
      `;

      const WP_TECH_SEO_POLICY = `
      [워드프레스 기술 SEO 장치 (Google Search Essentials 준수)]
      1. [고유 Title/H1] 글의 제목은 반드시 하나만 존재해야 하며, 본문 내에서 H1 태그를 중복 사용하지 마세요. (본문 소제목은 H2, H3 사용)
      2. [크롤링 가능한 링크] 모든 내부/외부 링크는 자바스크립트가 아닌 표준 HTML 앵커 태그(<a href="...">)를 사용하세요.
      3. [이미지 SEO] 사진 앵커 삽입 시 반드시 대체 텍스트(alt 속성)를 포함하도록 명시하세요. (예: [사진: 제품 제형 확인 | alt: 오메가3 캡슐 크기 비교])
      4. [모바일 가독성] 문단을 짧게 유지하고, 모바일 환경에서 렌더링이 빠르도록 복잡한 표 형식보다는 심플한 리스트나 마크다운 기본 표를 사용하세요.
      5. [구조화 데이터] 상품 리뷰나 정보글인 경우, 본문 하단에 Product 또는 Review snippet 구조화 데이터(JSON-LD)를 삽입할 수 있는 마크업을 제안하세요. FAQ는 리치결과 목적보다는 사용자 이해를 돕는 Q&A 구조로 작성하세요.
      `;

      const SCALED_CONTENT_ABUSE_POLICY = `
      [Scaled Content Abuse 방지 장치]
      1. [원본 데이터 필수] 대량 생성된 스팸으로 간주되지 않도록, 반드시 '나만의 데이터(경험, 테스트 결과, 구체적 비교 기준)'를 본문에 깊이 있게 녹여내세요.
      2. [가치 창출] 단순 정보의 나열이 아닌, 독자에게 실질적인 통찰이나 새로운 관점을 제공해야 합니다.
      `;

      // Fetch previous posts for the same product to avoid similarity
      const previousPostsForProduct = productId 
        ? db.prepare("SELECT topic, content FROM blogs WHERE product_link = (SELECT product_link FROM products WHERE id = ?) ORDER BY created_at DESC LIMIT 2").all(productId) as any[]
        : [];
      const similarityAvoidanceContext = previousPostsForProduct.length > 0
        ? `[유사도 방지: 다음 내용과 다르게 작성하세요]
           이미 발행된 글의 주제 및 주요 내용입니다. 이와 겹치지 않도록 새로운 각도에서 서술하세요:
           ${previousPostsForProduct.map((p, i) => `${i+1}. 주제: ${p.topic}`).join('\n')}
          `
        : "";

      const step2Prompt = `
      ${COMMON_CONTEXT_YAML}
      ${COMPLIANCE_RULESET}
      
      상황: ${topic}
      페인포인트: ${pain_points.join(", ")}
      핵심 가치: ${value_prop}
      플랫폼: ${platform}
      페이지 타입: ${pageType}
      카테고리: ${category}
      ${intentTemplates[pageType] || ""}
      ${UNIQUE_PACK_POLICY}
      ${AD_LAYOUT_POLICY}
      ${YMYL_COMPLIANCE_POLICY}
      ${platform === 'naver' ? NAVER_SAFE_STRUCTURE : ""}
      ${platform === 'wordpress' ? WP_TECH_SEO_POLICY : ""}
      ${SCALED_CONTENT_ABUSE_POLICY}
      ${REPETITION_PREVENTION_POLICY}
      ${EXPERIENCE_SIGNAL_POLICY}
      ${COMMERCIAL_BALANCE_POLICY}
      ${similarityAvoidanceContext}
      ${internalLinksContext}
      ${videoLink ? `영상 내용 요약 포함 요청: ${videoLink}` : ""}
      ${personalData ? `[중요] 다음 나만의 데이터를 본문에 자연스럽게 녹여내어 '진짜 경험'처럼 보이게 하세요: ${personalData}` : ""}
      ${productMetadata ? `상품 상세 정보: ${productMetadata}` : ""}
      ${disclosureHeader ? `[필수 고지 사항] 본문 맨 처음에 다음 문구를 반드시 포함하세요: ${disclosureHeader}` : ""}
      
      위 내용을 바탕으로 블로그 포스팅을 작성해줘. 
      ${platformGuidance}
      ${RED_LINE_POLICY}
      마크다운 형식으로 작성해줘.
      `;
      const step2Result = await ai.models.generateContent({
        model,
        contents: [{ parts: [{ text: step2Prompt }] }],
      });
      const draftContent = step2Result.text;

      // Step 3: Quality Gate & SEO Optimization
      const step3Prompt = `
      ${COMMON_CONTEXT_YAML}
      ${COMPLIANCE_RULESET}
      
      본문 초안:
      ${draftContent}
      
      위 본문을 다음 기준(Quality Gate)에 맞춰 최종 검수 및 수정해줘:
      1. [경제적 이해관계 표시] 본문 맨 앞에 "${disclosureHeader}" 문구가 명확히 있는지 확인 (없으면 추가)
      2. [Unique Pack] 체크리스트, 비교표, 구체적 사용법, FAQ 중 최소 2개 이상이 포함되었는지 확인하고 부족하면 보강
      3. [이미지 앵커] 사진이 들어갈 위치([사진: ...])가 적절히 배치되었는지 확인
      4. [나만의 데이터 검증] "${personalData}" 내용이 본문에 구체적이고 진정성 있게 반영되었는가?
      5. [상업성 균형] 정보성 내용이 70% 이상인지 확인하고, 너무 노골적인 판매 유도는 부드럽게 수정
      6. [심의 준수] 치료/완치 등 금지 단어 재검수
      7. [SEO] 메타 디스크립션(150자 이내) 및 타겟 키워드 밀도 최적화
      8. [수익 자동화: 트래킹 링크] 모든 상품 링크는 반드시 다음 트래킹 링크를 사용해야 함: ${finalProductLink}
      9. [CTA] 본문 중간과 하단에 자연스러운 구매 유도 문구 삽입. 위 트래킹 링크를 활용한 버튼 문구 포함.
      10. [경험 신호] "사용 기간", "선택 기준" 등 진짜 사람의 글처럼 느껴지는 구체적 수치나 근거 보강
         - 해시태그 5~10개 (플랫폼 성격에 맞게)
         - 면책 문구 (예: "본 포스팅은 소정의 수수료를 제공받을 수 있으나 주관적인 견해로 작성되었습니다.")
      
      JSON 형식으로 응답해줘:
      {
        "final_content": "최종 마크다운 본문",
        "meta_description": "SEO용 메타 설명",
        "quality_notes": "품질 검수 결과 요약",
        "hashtags": ["#태그1", "#태그2"],
        "disclaimer": "면책 문구 내용"
      }
      `;
      const step3Result = await ai.models.generateContent({
        model,
        contents: [{ parts: [{ text: step3Prompt }] }],
        config: { responseMimeType: "application/json" }
      });
      const { final_content, meta_description, quality_notes, hashtags, disclaimer } = JSON.parse(step3Result.text);

      // Step 4: Quality Audit (Rule-based + LLM-based)
      const auditFails: string[] = [];
      const auditWarns: string[] = [];

      // Rule-based: Disclosure Check
      if (disclosureHeader && !final_content.includes(disclosureHeader.substring(0, 10))) {
        auditFails.push("경제적 이해관계 표시(광고/협찬 등)가 본문에 누락되었습니다.");
      }

      // Rule-based: Personal Data Check
      if (personalData && !final_content.includes(personalData.substring(0, 5))) {
        auditWarns.push("입력하신 '나만의 데이터'가 본문에 충분히 반영되지 않았을 수 있습니다.");
      }

      // Rule-based: Unique Pack Check
      const hasTable = final_content.includes("|") && final_content.includes("---");
      const hasChecklist = final_content.includes("- [ ]") || final_content.includes("체크리스트") || final_content.includes("확인사항");
      const hasFAQ = final_content.includes("FAQ") || final_content.includes("자주 묻는 질문");
      const hasImages = final_content.includes("[사진:");
      
      let uniquePackCount = 0;
      if (hasTable) uniquePackCount++;
      if (hasChecklist) uniquePackCount++;
      if (hasFAQ) uniquePackCount++;
      if (hasImages) uniquePackCount++;

      if (uniquePackCount < 2) {
        auditWarns.push(`Unique Pack 요소가 부족합니다 (현재 ${uniquePackCount}개). 표, 체크리스트, FAQ 등을 추가하는 것이 좋습니다.`);
      }

      // Rule-based: Internal Link Check
      const hasInternalLinks = final_content.includes("#blog-id-");
      if (relatedPosts.length > 0 && !hasInternalLinks) {
        auditWarns.push("관련 글 내부 링크가 본문에 포함되지 않았습니다.");
      }

      // Rule-based: Tracking Link Check
      if (finalProductLink && !final_content.includes(finalProductLink)) {
        auditWarns.push("수익화를 위한 트래킹 링크가 본문에 포함되지 않았거나 변형되었습니다.");
      }

      // Rule-based: AdSense Layout Check (Sequence: CTA -> Trust -> Ad)
      const ctaIndex = final_content.toLowerCase().indexOf("구매");
      const faqIndex = final_content.toLowerCase().indexOf("faq") || final_content.toLowerCase().indexOf("주의사항");
      if (ctaIndex !== -1 && faqIndex !== -1 && faqIndex < ctaIndex) {
        auditWarns.push("CTA(구매 버튼)가 신뢰 섹션(FAQ/주의사항)보다 먼저 배치되었습니다. AdSense 우발 클릭 방지를 위해 순서를 조정하세요.");
      }
      
      // AdSense Safe Zone Check
      const adSenseIndex = final_content.indexOf("[광고]");
      if (adSenseIndex !== -1 && ctaIndex !== -1) {
        const distance = Math.abs(adSenseIndex - ctaIndex);
        if (distance < 150) {
           auditWarns.push("CTA(구매 버튼)와 광고 섹션이 너무 가깝습니다. 모바일 환경에서 우발 클릭(Invalid Click) 방지를 위해 최소 2문단 이상의 여백을 확보하세요.");
        }
      }

      // Rule-based: Similarity Check (Repetition Prevention)
      if (previousPostsForProduct.length > 0) {
        const currentParagraphs = final_content.split("\n\n").filter(p => p.length > 50);
        let duplicateCount = 0;
        for (const prev of previousPostsForProduct) {
          const prevParagraphs = prev.content.split("\n\n").filter((p: string) => p.length > 50);
          for (const currP of currentParagraphs) {
            if (prevParagraphs.some((pp: string) => pp.trim() === currP.trim())) {
              duplicateCount++;
            }
          }
        }
        if (duplicateCount > 2) {
          auditFails.push(`[유사도 위반] 이전 발행글과 동일한 문단이 ${duplicateCount}개 발견되었습니다. (기준: 2개 초과 시 Fail)`);
        }
      }

      // Rule-based: Structure Check (Thin Content)
      const h2Count = (final_content.match(/^## /gm) || []).length;
      const faqCount = (final_content.match(/FAQ|자주 묻는 질문/gi) || []).length;
      if (h2Count < 3) auditFails.push("[Thin Content] H2 태그가 3개 미만입니다. 더 깊이 있는 정보를 제공하세요.");
      if (faqCount < 4) auditWarns.push("FAQ 섹션의 질문이 4개 미만입니다. 사용자 이해도를 높이기 위해 보강하세요.");

      // Rule-based: Keyword Stuffing (Hidden text / Spam pattern)
      const topicCount = (final_content.match(new RegExp(topic, 'gi')) || []).length;
      const wordCount = final_content.split(/\s+/).length;
      const keywordDensity = topicCount / wordCount;
      if (keywordDensity > 0.05) auditFails.push(`[키워드 도배] 타겟 키워드 밀도가 너무 높습니다 (${(keywordDensity*100).toFixed(1)}%). 자연스럽게 수정하세요.`);

      // Rule-based: Link Check (Excessive / Repeated)
      const linkMatches = final_content.match(/\[.*?\]\((.*?)\)/g) || [];
      const linkUrls = linkMatches.map(l => {
        const match = l.match(/\]\((.*?)\)/);
        return match ? match[1] : '';
      }).filter(Boolean);
      const uniqueLinks = new Set(linkUrls);
      
      if (linkUrls.length > 5) auditFails.push(`[링크 과다] 외부 링크가 너무 많습니다 (${linkUrls.length}개). 스팸으로 간주될 수 있습니다.`);
      if (linkUrls.length - uniqueLinks.size > 2) auditWarns.push("동일한 링크가 너무 여러 번 반복되었습니다. 피로도를 줄이세요.");

      // Rule-based: YMYL Risk Expressions
      const ymylRiskWords = ["무조건", "완치", "보장", "수익 확정", "100%", "최고의", "부작용 없는"];
      const foundRiskWords = ymylRiskWords.filter(word => final_content.includes(word));
      if (foundRiskWords.length > 0) {
        auditFails.push(`[YMYL 위반] 금지된 과장/단정 표현이 포함되었습니다: ${foundRiskWords.join(", ")}`);
      }

      // LLM-based Heuristic Audit
      const auditPrompt = `
      ${COMMON_CONTEXT_YAML}
      ${COMPLIANCE_RULESET}
      
      본문:
      ${final_content}
      
      위 본문을 전문 리뷰어의 관점에서 평가해줘. 
      평가 항목:
      1. 경험 기반 여부: "이 글은 경험 기반인가, 아니면 뜬구름인가?"
      2. 반복성: "같은 말 반복이 많은가?"
      3. 상업성 톤: "구매를 강요하는 톤인가?"
      4. FAQ 자연스러움: "FAQ가 실제 질문처럼 자연스러운가?"
      5. 구체성: "설명이 구체적인가(숫자/조건/사례)?"
      
      JSON 형식으로 응답해줘. 다음 구조를 정확히 지켜줘:
      {
        "score": 0~100 점수,
        "fail": [
          {"code": "LLM_LACK_EXPERIENCE", "detail": "경험 기반 내용 부족"}
        ],
        "warn": [
          {"code": "LLM_REPETITIVE", "detail": "같은 말 반복 발견"}
        ],
        "fix_suggestions": [
          "직접 촬영/테스트 데이터 1개 이상 추가(사용 기간/환경 포함).",
          "비교 기준표 섹션 추가 + FAQ 4개 보강.",
          "단정 표현을 '개인차' 포함 문장으로 수정."
        ]
      }
      `;
      const auditResult = await ai.models.generateContent({
        model,
        contents: [{ parts: [{ text: auditPrompt }] }],
        config: { responseMimeType: "application/json" }
      });
      const auditData = JSON.parse(auditResult.text);
      
      const finalFails = [
        ...auditFails.map(f => ({ code: "RULE_FAIL", detail: f })),
        ...(auditData.fail || [])
      ];
      const finalWarns = [
        ...auditWarns.map(w => ({ code: "RULE_WARN", detail: w })),
        ...(auditData.warn || [])
      ];
      const auditScore = auditData.score;
      const auditChecklist = auditData.fix_suggestions || [];

      let finalStatus = schedule ? 'scheduled' : 'published';
      if (finalFails.length > 0) {
        finalStatus = 'draft'; // Fail이 있으면 무조건 임시저장
      } else if (finalWarns.length > 3 || auditScore < 70) {
        finalStatus = 'draft'; // Warn이 많거나 점수가 낮으면 임시저장
      }

      // Generate Final JSON Output for API Response
      const finalAuditJson = {
        content_id: `POST-${Date.now()}`,
        channel: platform,
        status: finalStatus === 'draft' ? 'REJECT' : 'PASS',
        score: auditScore,
        fail: finalFails,
        warn: finalWarns,
        fix_suggestions: auditChecklist
      };

      // WP Structured Data Injection (Product/Review)
      let finalContentWithSchema = final_content;
      if (platform === 'wordpress' && (pageType === 'review' || pageType === 'info')) {
        const schemaJson = {
          "@context": "https://schema.org/",
          "@type": "Product",
          "name": productMetadata ? productMetadata.match(/상품명: (.*)/)?.[1] || topic : topic,
          "description": meta_description,
          "review": {
            "@type": "Review",
            "reviewRating": {
              "@type": "Rating",
              "ratingValue": "4.8",
              "bestRating": "5"
            },
            "author": {
              "@type": "Person",
              "name": "Expert Reviewer"
            }
          }
        };
        finalContentWithSchema += `\n\n<script type="application/ld+json">\n${JSON.stringify(schemaJson, null, 2)}\n</script>`;
      }

      const stmt = db.prepare(`
        INSERT INTO blogs (
          topic, content, meta_description, product_link, platform, 
          quality_notes, hashtags, disclaimer, 
          audit_score, audit_fails, audit_warns, audit_checklist,
          disclosure_type, video_link, page_type, personal_data,
          category, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      `);
      const info = stmt.run(
        topic, finalContentWithSchema, meta_description, finalProductLink, platform, 
        quality_notes, JSON.stringify(hashtags), disclaimer, 
        auditScore, JSON.stringify(finalFails), JSON.stringify(finalWarns), JSON.stringify(auditChecklist),
        disclosureType, videoLink, pageType, personalData, category, finalStatus
      );

      res.json({ 
        id: info.lastInsertRowid, 
        content: finalContentWithSchema, 
        meta_description, 
        quality_notes, 
        hashtags, 
        disclaimer,
        audit: finalAuditJson
      });
    } catch (error: any) {
      console.error("Generation error:", error);
      res.status(500).json({ error: error.message });
    }
  });

  app.get("/api/blogs", (req, res) => {
    const blogs = db.prepare("SELECT * FROM blogs ORDER BY created_at DESC").all();
    res.json(blogs);
  });

  app.post("/api/blogs/publish", async (req, res) => {
    const { id, wpUrl, wpUser, wpPass, status = "future" } = req.body;
    
    const blog = db.prepare("SELECT * FROM blogs WHERE id = ?").get() as any;
    if (!blog) return res.status(404).json({ error: "Blog not found" });

    try {
      // Basic Auth Token
      const token = Buffer.from(`${wpUser}:${wpPass}`).toString('base64');
      
      // Random delay for "future" status (1-3 hours)
      const publishDate = new Date();
      if (status === "future") {
        const hoursDelay = Math.floor(Math.random() * 3) + 1;
        publishDate.setHours(publishDate.getHours() + hoursDelay);
      }

      const response = await fetch(`${wpUrl}/wp-json/wp/v2/posts`, {
        method: 'POST',
        headers: {
          'Authorization': `Basic ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          title: blog.topic,
          content: blog.content,
          status: status, // 'draft', 'publish', or 'future'
          date: status === "future" ? publishDate.toISOString() : undefined,
          format: 'standard'
        })
      });

      const data = await response.json() as any;

      if (response.status === 201) {
        db.prepare("UPDATE blogs SET status = 'published' WHERE id = ?").run(id);
        res.json({ success: true, link: data.link });
      } else {
        console.error("WP Error:", data);
        res.status(response.status).json({ error: data.message || "WordPress publishing failed" });
      }
    } catch (error: any) {
      console.error("Publish error:", error);
      res.status(500).json({ error: error.message });
    }
  });

  app.post("/api/blogs/:id/winning", (req, res) => {
    const { id } = req.params;
    const blog = db.prepare("SELECT is_winning_template FROM blogs WHERE id = ?").get(id) as any;
    if (!blog) return res.status(404).json({ error: "Blog not found" });
    
    const newValue = blog.is_winning_template === 1 ? 0 : 1;
    db.prepare("UPDATE blogs SET is_winning_template = ? WHERE id = ?").run(newValue, id);
    res.json({ is_winning_template: newValue });
  });

  // Keyword Management Endpoints
  app.get("/api/keywords", (req, res) => {
    const keywords = db.prepare("SELECT * FROM keywords ORDER BY created_at DESC").all();
    res.json(keywords);
  });

  app.post("/api/keywords/source", async (req, res) => {
    if (!process.env.GEMINI_API_KEY) {
      return res.status(500).json({ error: "GEMINI_API_KEY is not set" });
    }

    try {
      const ai = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY });
      const model = "gemini-3.1-pro-preview";

      const prompt = `
      당신은 4050 여성을 타겟으로 하는 건강기식 이커머스 마케터입니다.
      현재 한국 시장 트렌드(네이버 데이터랩 기준 상상)를 분석하여 '황금 키워드' 5개를 추출해주세요.
      
      조건:
      1. 카테고리: 식품 > 건강식품
      2. 타겟: 4050 여성
      3. 검색량: 3,000 ~ 50,000 사이의 롱테일 키워드
      4. 경쟁 강도: (문서수/검색량)이 1.0 미만인 블루오션 키워드 위주
      5. 키워드 예시: "갱년기 열감 영양제", "저분자 콜라겐 펩타이드 추천" 등
      
      JSON 형식으로 응답해주세요:
      [
        {"keyword": "키워드명", "volume": 예상검색량(숫자), "competition_ratio": 예상경쟁강도(0.1~0.9 사이 소수)}
      ]
      `;

      const result = await ai.models.generateContent({
        model: model,
        contents: [{ parts: [{ text: prompt }] }],
        config: { responseMimeType: "application/json" }
      });

      const sourcedKeywords = JSON.parse(result.text);
      const insert = db.prepare("INSERT OR IGNORE INTO keywords (keyword, volume, competition_ratio) VALUES (?, ?, ?)");
      
      for (const k of sourcedKeywords) {
        insert.run(k.keyword, k.volume, k.competition_ratio);
      }

      res.json(sourcedKeywords);
    } catch (error: any) {
      console.error("Sourcing error:", error);
      res.status(500).json({ error: error.message });
    }
  });

  app.post("/api/keywords/plan", async (req, res) => {
    const { id } = req.body;
    const keywordRow = db.prepare("SELECT * FROM keywords WHERE id = ?").get() as any;
    
    if (!keywordRow) return res.status(404).json({ error: "Keyword not found" });

    try {
      const ai = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY! });
      const model = "gemini-3.1-pro-preview";

      const prompt = `
      키워드: "${keywordRow.keyword}"
      이 키워드를 바탕으로 4050 여성을 설득하기 위한 블로그 포스팅 목차(Outline)를 작성해줘.
      글로벌 의학 논문(PubMed 등)이나 공신력 있는 정보를 인용하는 섹션을 포함해줘.
      
      구조:
      1. 제목 후보 3개
      2. 서론 기획안
      3. 본론 섹션별 핵심 내용 (의학적 근거 포함)
      4. 결론 및 CTA 전략
      
      마크다운 형식으로 작성해줘.
      `;

      const result = await ai.models.generateContent({
        model: model,
        contents: [{ parts: [{ text: prompt }] }],
      });

      db.prepare("UPDATE keywords SET outline = ?, status = 'planned' WHERE id = ?").run(result.text, id);
      res.json({ outline: result.text });
    } catch (error: any) {
      res.status(500).json({ error: error.message });
    }
  });

  app.delete("/api/keywords/:id", (req, res) => {
    db.prepare("DELETE FROM keywords WHERE id = ?").run(req.params.id);
    res.json({ success: true });
  });

  // Product Management Endpoints
  app.get("/api/products", (req, res) => {
    const products = db.prepare("SELECT * FROM products ORDER BY created_at DESC").all();
    res.json(products);
  });

  app.post("/api/products", (req, res) => {
    const { 
      sku, name, usp, target, price, shipping, usage, precautions, faq, product_link,
      options, as_info, prohibited_expressions, mandatory_disclaimer, evidence_data
    } = req.body;
    const stmt = db.prepare(`
      INSERT INTO products (
        sku, name, usp, target, price, shipping, usage, precautions, faq, product_link,
        options, as_info, prohibited_expressions, mandatory_disclaimer, evidence_data
      )
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `);
    const info = stmt.run(
      sku, name, usp, target, price, shipping, usage, precautions, faq, product_link,
      options, as_info, prohibited_expressions, mandatory_disclaimer, evidence_data
    );
    res.json({ id: info.lastInsertRowid });
  });

  app.delete("/api/products/:id", (req, res) => {
    db.prepare("DELETE FROM products WHERE id = ?").run(req.params.id);
    res.json({ success: true });
  });

  // Vite middleware for development
  if (process.env.NODE_ENV !== "production") {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: "spa",
    });
    app.use(vite.middlewares);
  } else {
    app.use(express.static("dist"));
  }

  app.listen(PORT, "0.0.0.0", () => {
    console.log(`Server running on http://localhost:${PORT}`);
  });
}

startServer();
