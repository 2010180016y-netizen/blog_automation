import { GoogleGenAI, Type } from "@google/genai";

const RED_LINE_POLICY = `
[건기식 심의 방어 정책 (Red-line Policy)]
- 질병의 '치료', '예방', '완치', '특효', '직효' 등의 단어를 절대 사용하지 마십시오.
- 대신 다음의 대체 워딩을 사용하십시오:
  - "증상 완화에 도움을 줄 수 있음"
  - "식약처 기능성 인정 원료"
  - "건강 유지에 필요한"
  - "영양 보충에 도움"
- 의학적 근거와 영양학적 정보를 바탕으로 신뢰성 있는 톤앤매너를 유지하십시오.
- 독자가 해당 성분의 필요성을 느끼게 한 뒤 자연스럽게 구매를 고려하도록 유도하십시오.
`;

export async function generateBlogPost(topic: string, productLink: string) {
  const ai = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY! });
  const model = "gemini-3.1-pro-preview";

  const prompt = `
주제: ${topic}
이커머스 링크: ${productLink}

위 주제에 대해 워드프레스 정보성 블로그 포스트를 작성해줘. 
이 포스트는 MoFu(설득 단계)용이며, 독자에게 신뢰를 주고 마지막에 제품 구매(BoFu)로 이어지게 해야 해.

구조:
1. 흥미로운 제목
2. 서론: 해당 건강 고민에 대한 공감 및 화두 던지기
3. 본론: 성분의 의학적/영양학적 근거 (신뢰도 확보)
4. 결론: 해당 성분 섭취의 중요성 강조
5. CTA: 제품 구매 링크를 포함한 매력적인 문구

${RED_LINE_POLICY}
`;

  const response = await ai.models.generateContent({
    model: model,
    contents: [{ parts: [{ text: prompt }] }],
    config: {
      temperature: 0.7,
    },
  });

  return response.text;
}
