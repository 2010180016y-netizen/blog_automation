import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { 
  Plus, 
  History, 
  Settings, 
  Sparkles, 
  ExternalLink, 
  ShieldCheck, 
  BarChart3, 
  ChevronRight,
  Loader2,
  CheckCircle2,
  AlertCircle,
  Search,
  Zap,
  FileText,
  Trash2,
  TrendingUp,
  Package,
  Database as DbIcon,
  Tag,
  AlertTriangle,
  Clock,
  XCircle,
  X
} from 'lucide-react';
import Markdown from 'react-markdown';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface Blog {
  id: number;
  topic: string;
  content: string;
  meta_description: string;
  product_link: string;
  platform: 'wordpress' | 'naver';
  quality_notes?: string;
  hashtags?: string;
  disclaimer?: string;
  audit_score?: number;
  audit_fails?: string;
  audit_warns?: string;
  audit_checklist?: string;
  disclosure_type?: string;
  video_link?: string;
  page_type?: string;
  personal_data?: string;
  category?: string;
  performance_score?: number;
  is_winning_template?: number;
  status: 'published' | 'scheduled' | 'draft';
  created_at: string;
}

interface Keyword {
  id: number;
  keyword: string;
  volume: number;
  competition_ratio: number;
  status: 'sourced' | 'planned' | 'generated';
  outline?: string;
  created_at: string;
}

interface Product {
  id: number;
  sku: string;
  name: string;
  usp: string;
  target: string;
  price: number;
  shipping: string;
  usage: string;
  precautions: string;
  faq: string;
  product_link: string;
  options?: string;
  as_info?: string;
  prohibited_expressions?: string;
  mandatory_disclaimer?: string;
  evidence_data?: string;
  created_at: string;
}

export default function App() {
  const [activeTab, setActiveTab] = useState<'factory' | 'lab' | 'history' | 'settings' | 'products'>('factory');
  const [topic, setTopic] = useState('');
  const [productLink, setProductLink] = useState('');
  const [selectedProductId, setSelectedProductId] = useState<number | null>(null);
  const [disclosureType, setDisclosureType] = useState<string>('none');
  const [pageType, setPageType] = useState<string>('review');
  const [category, setCategory] = useState<string>('건강/영양제');
  const [videoLink, setVideoLink] = useState('');
  const [personalData, setPersonalData] = useState('');
  const [platform, setPlatform] = useState<'wordpress' | 'naver'>('wordpress');
  const [shouldSchedule, setShouldSchedule] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [blogs, setBlogs] = useState<Blog[]>([]);
  const [keywords, setKeywords] = useState<Keyword[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [isSourcing, setIsSourcing] = useState(false);
  const [isPlanning, setIsPlanning] = useState<number | null>(null);
  const [viewingPackage, setViewingPackage] = useState<Blog | null>(null);
  const [currentBlog, setCurrentBlog] = useState<string | null>(null);
  const [currentQualityNotes, setCurrentQualityNotes] = useState<string | null>(null);
  const [currentHashtags, setCurrentHashtags] = useState<string[]>([]);
  const [currentDisclaimer, setCurrentDisclaimer] = useState<string | null>(null);
  const [currentAudit, setCurrentAudit] = useState<{
    score: number;
    fails: {code: string, detail: string}[];
    warns: {code: string, detail: string}[];
    checklist: string[];
    status: string;
  } | null>(null);
  const [pixelId, setPixelId] = useState('');
  const [gaId, setGaId] = useState('');
  const [wpUrl, setWpUrl] = useState('');
  const [wpUser, setWpUser] = useState('');
  const [wpPass, setWpPass] = useState('');
  const [isPublishing, setIsPublishing] = useState<number | null>(null);

  // Product Form State
  const [newProduct, setNewProduct] = useState<Partial<Product>>({
    sku: '', name: '', usp: '', target: '', price: 0, shipping: '', usage: '', precautions: '', faq: '', product_link: '',
    options: '', as_info: '', prohibited_expressions: '', mandatory_disclaimer: '', evidence_data: ''
  });

  useEffect(() => {
    fetchBlogs();
    fetchKeywords();
    fetchProducts();
  }, []);

  const fetchBlogs = async () => {
    try {
      const res = await fetch('/api/blogs');
      const data = await res.json();
      setBlogs(data);
    } catch (err) {
      console.error('Failed to fetch blogs:', err);
    }
  };

  const fetchKeywords = async () => {
    try {
      const res = await fetch('/api/keywords');
      const data = await res.json();
      setKeywords(data);
    } catch (err) {
      console.error('Failed to fetch keywords:', err);
    }
  };

  const fetchProducts = async () => {
    try {
      const res = await fetch('/api/products');
      const data = await res.json();
      setProducts(data);
    } catch (err) {
      console.error('Failed to fetch products:', err);
    }
  };

  const handleSourceKeywords = async () => {
    setIsSourcing(true);
    try {
      await fetch('/api/keywords/source', { method: 'POST' });
      fetchKeywords();
    } catch (err) {
      console.error('Sourcing failed:', err);
    } finally {
      setIsSourcing(false);
    }
  };

  const handlePlanKeyword = async (id: number) => {
    setIsPlanning(id);
    try {
      await fetch('/api/keywords/plan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id }),
      });
      fetchKeywords();
    } catch (err) {
      console.error('Planning failed:', err);
    } finally {
      setIsPlanning(null);
    }
  };

  const handleDeleteKeyword = async (id: number) => {
    try {
      await fetch(`/api/keywords/${id}`, { method: 'DELETE' });
      fetchKeywords();
    } catch (err) {
      console.error('Delete failed:', err);
    }
  };

  const handlePublish = async (id: number, status: 'publish' | 'future' | 'draft' = 'future') => {
    if (!wpUrl || !wpUser || !wpPass) {
      alert('워드프레스 설정을 먼저 완료해주세요.');
      setActiveTab('settings');
      return;
    }

    setIsPublishing(id);
    try {
      const res = await fetch('/api/blogs/publish', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id, wpUrl, wpUser, wpPass, status }),
      });
      const data = await res.json();
      if (data.error) throw new Error(data.error);
      
      alert(`워드프레스 ${status === 'draft' ? '임시저장' : '발행'} 성공!`);
      fetchBlogs();
    } catch (err: any) {
      console.error('Publish failed:', err);
      alert(`발행 실패: ${err.message}`);
    } finally {
      setIsPublishing(null);
    }
  };
  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!topic || !productLink) return;

    setIsGenerating(true);
    try {
      const res = await fetch('/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          topic, 
          productLink, 
          productId: selectedProductId,
          platform, 
          disclosureType,
          pageType,
          category,
          videoLink,
          personalData,
          schedule: shouldSchedule 
        }),
      });
      const data = await res.json();
      if (data.error) throw new Error(data.error);
      
      setCurrentBlog(data.content);
      setCurrentQualityNotes(data.quality_notes);
      setCurrentHashtags(data.hashtags || []);
      setCurrentDisclaimer(data.disclaimer);
      setCurrentAudit({
        score: data.audit.score,
        fails: data.audit.fail,
        warns: data.audit.warn,
        checklist: data.audit.fix_suggestions,
        status: data.audit.status
      });
      fetchBlogs();
    } catch (err) {
      console.error('Generation failed:', err);
      alert('생성에 실패했습니다. API 키를 확인해주세요.');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleAddProduct = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await fetch('/api/products', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newProduct),
      });
      if (res.ok) {
        setNewProduct({ 
          sku: '', name: '', usp: '', target: '', price: 0, shipping: '', usage: '', precautions: '', faq: '', product_link: '',
          options: '', as_info: '', prohibited_expressions: '', mandatory_disclaimer: '', evidence_data: ''
        });
        fetchProducts();
        alert('상품이 추가되었습니다.');
      }
    } catch (err) {
      console.error('Add product failed:', err);
    }
  };

  const handleDeleteProduct = async (id: number) => {
    if (!confirm('정말 삭제하시겠습니까?')) return;
    try {
      await fetch(`/api/products/${id}`, { method: 'DELETE' });
      fetchProducts();
    } catch (err) {
      console.error('Delete product failed:', err);
    }
  };

  return (
    <div className="min-h-screen bg-[#F5F5F0] text-zinc-900 font-sans">
      {/* Sidebar Navigation */}
      <nav className="fixed left-0 top-0 h-full w-20 bg-white border-r border-black/5 flex flex-col items-center py-8 gap-8 z-50">
        <div className="w-12 h-12 bg-emerald-600 rounded-2xl flex items-center justify-center text-white shadow-lg shadow-emerald-200">
          <Sparkles size={24} />
        </div>
        
        <div className="flex flex-col gap-4">
          <NavButton 
            active={activeTab === 'factory'} 
            onClick={() => setActiveTab('factory')}
            icon={<Plus size={24} />}
            label="Factory"
          />
          <NavButton 
            active={activeTab === 'lab'} 
            onClick={() => setActiveTab('lab')}
            icon={<Search size={24} />}
            label="Keyword Lab"
          />
          <NavButton 
            active={activeTab === 'products'} 
            onClick={() => setActiveTab('products')}
            icon={<Package size={24} />}
            label="Product DB"
          />
          <NavButton 
            active={activeTab === 'history'} 
            onClick={() => setActiveTab('history')}
            icon={<History size={24} />}
            label="History"
          />
          <NavButton 
            active={activeTab === 'settings'} 
            onClick={() => setActiveTab('settings')}
            icon={<Settings size={24} />}
            label="Settings"
          />
        </div>
      </nav>

      {/* Main Content */}
      <main className="pl-20 min-h-screen">
        <div className="max-w-6xl mx-auto px-8 py-12">
          
          <AnimatePresence mode="wait">
            {activeTab === 'factory' && (
              <motion.div
                key="factory"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="space-y-8"
              >
                <header className="flex justify-between items-end">
                  <div>
                    <h1 className="text-4xl font-serif font-bold tracking-tight mb-2">AI Content Factory</h1>
                    <p className="text-zinc-500">건기식 심의 규정을 준수하는 고효율 블로그 포스트를 생성합니다.</p>
                  </div>
                  <div className="flex gap-2">
                    {blogs.filter(b => b.is_winning_template === 1).length > 0 && (
                      <div className="px-4 py-2 bg-purple-50 border border-purple-100 rounded-2xl flex items-center gap-2">
                        <TrendingUp size={16} className="text-purple-600" />
                        <span className="text-xs font-bold text-purple-700">
                          {blogs.filter(b => b.is_winning_template === 1).length}개의 성과 템플릿 학습됨
                        </span>
                      </div>
                    )}
                  </div>
                </header>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                  {/* Input Form */}
                  <div className="lg:col-span-1 space-y-6">
                    <form onSubmit={handleGenerate} className="bg-white p-6 rounded-3xl shadow-sm border border-black/5 space-y-4">
                      <div className="space-y-2">
                        <label className="text-xs font-semibold uppercase tracking-wider text-zinc-400">문제/상황 (Problem/Situation)</label>
                        <input 
                          type="text" 
                          value={topic}
                          onChange={(e) => setTopic(e.target.value)}
                          placeholder="예: 겨울철 건조로 인한 피부 각질"
                          className="w-full px-4 py-3 rounded-xl bg-zinc-50 border border-zinc-200 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all"
                        />
                      </div>
                      
                      <div className="space-y-2">
                        <label className="text-xs font-semibold uppercase tracking-wider text-zinc-400">연관 상품 선택 (Optional)</label>
                        <select
                          value={selectedProductId || ''}
                          onChange={(e) => {
                            const val = e.target.value ? parseInt(e.target.value) : null;
                            setSelectedProductId(val);
                            if (val) {
                              const p = products.find(prod => prod.id === val);
                              if (p) setProductLink(p.product_link);
                            }
                          }}
                          className="w-full px-4 py-3 rounded-xl bg-zinc-50 border border-zinc-200 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all"
                        >
                          <option value="">상품을 선택하세요 (직접 입력 가능)</option>
                          {products.map(p => (
                            <option key={p.id} value={p.id}>{p.name} ({p.sku})</option>
                          ))}
                        </select>
                      </div>

                      <div className="space-y-2">
                        <label className="text-xs font-semibold uppercase tracking-wider text-zinc-400">연관 상품 선택 (Optional)</label>
                        <select
                          value={selectedProductId || ''}
                          onChange={(e) => {
                            const val = e.target.value ? parseInt(e.target.value) : null;
                            setSelectedProductId(val);
                            if (val) {
                              const p = products.find(prod => prod.id === val);
                              if (p) setProductLink(p.product_link);
                            }
                          }}
                          className="w-full px-4 py-3 rounded-xl bg-zinc-50 border border-zinc-200 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all"
                        >
                          <option value="">상품을 선택하세요 (직접 입력 가능)</option>
                          {products.map(p => (
                            <option key={p.id} value={p.id}>{p.name} ({p.sku})</option>
                          ))}
                        </select>
                      </div>

                      <div className="space-y-2">
                        <label className="text-xs font-semibold uppercase tracking-wider text-zinc-400">제품 링크 (BoFu Link)</label>
                        <input 
                          type="url" 
                          value={productLink}
                          onChange={(e) => setProductLink(e.target.value)}
                          placeholder="https://smartstore.naver.com/..."
                          className="w-full px-4 py-3 rounded-xl bg-zinc-50 border border-zinc-200 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all"
                        />
                      </div>

                      <div className="space-y-2">
                        <label className="text-xs font-semibold uppercase tracking-wider text-zinc-400">카테고리 (Category)</label>
                        <select
                          value={category}
                          onChange={(e) => setCategory(e.target.value)}
                          className="w-full px-4 py-3 rounded-xl bg-zinc-50 border border-zinc-200 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all"
                        >
                          <option value="건강/영양제">건강/영양제</option>
                          <option value="리빙/생활">리빙/생활</option>
                          <option value="뷰티/스킨케어">뷰티/스킨케어</option>
                          <option value="다이어트">다이어트</option>
                          <option value="마인드셋">마인드셋</option>
                        </select>
                      </div>

                      <div className="space-y-2">
                        <label className="text-xs font-semibold uppercase tracking-wider text-zinc-400">페이지 타입 (Page Type)</label>
                        <select
                          value={pageType}
                          onChange={(e) => setPageType(e.target.value)}
                          className="w-full px-4 py-3 rounded-xl bg-zinc-50 border border-zinc-200 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all"
                        >
                          <option value="info">정보성 (Information)</option>
                          <option value="review">리뷰 (Review)</option>
                          <option value="comparison">비교 (Comparison)</option>
                          <option value="guide">가이드 (Guide)</option>
                          <option value="story">스토리 (Storytelling)</option>
                        </select>
                      </div>

                      <div className="space-y-2">
                        <label className="text-xs font-semibold uppercase tracking-wider text-zinc-400">참고 영상 링크 (Video Source)</label>
                        <input 
                          type="url" 
                          value={videoLink}
                          onChange={(e) => setVideoLink(e.target.value)}
                          placeholder="https://youtube.com/watch?v=..."
                          className="w-full px-4 py-3 rounded-xl bg-zinc-50 border border-zinc-200 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all"
                        />
                      </div>

                      <div className="space-y-2">
                        <label className="text-xs font-semibold uppercase tracking-wider text-zinc-400">나만의 데이터 (My Data / Experience)</label>
                        <textarea 
                          value={personalData}
                          onChange={(e) => setPersonalData(e.target.value)}
                          placeholder="예: 2주간 직접 복용해본 결과 아침에 일어날 때 몸이 훨씬 가벼웠습니다. (실제 경험/측정값)"
                          className="w-full px-4 py-3 rounded-xl bg-zinc-50 border border-zinc-200 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all h-24"
                        />
                        <p className="text-[10px] text-zinc-400 leading-relaxed">
                          * 직접 촬영 사진, 전/후 비교, 실제 사용 시간 등 나만의 데이터를 한 줄이라도 넣으면 AI 느낌이 크게 줄어듭니다.
                        </p>
                      </div>

                      <div className="space-y-2">
                        <label className="text-xs font-semibold uppercase tracking-wider text-zinc-400">경제적 이해관계 표시 (Disclosure)</label>
                        <select
                          value={disclosureType}
                          onChange={(e) => setDisclosureType(e.target.value)}
                          className="w-full px-4 py-3 rounded-xl bg-zinc-50 border border-zinc-200 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all"
                        >
                          <option value="none">표시 없음 (정보성)</option>
                          <option value="ad">광고 (원고료 제공)</option>
                          <option value="sponsor">협찬 (제품 제공)</option>
                          <option value="affiliate">제휴 (수수료 발생)</option>
                        </select>
                        <p className="text-[10px] text-zinc-400 leading-relaxed">
                          * 2024년 12월 시행령에 따라 본문 맨 앞에 명확히 표시됩니다.
                        </p>
                      </div>

                      <div className="space-y-2">
                        <label className="text-xs font-semibold uppercase tracking-wider text-zinc-400">대상 플랫폼 (Platform)</label>
                        <div className="grid grid-cols-2 gap-2">
                          <button
                            type="button"
                            onClick={() => setPlatform('wordpress')}
                            className={cn(
                              "py-2 px-4 rounded-xl text-sm font-bold border transition-all",
                              platform === 'wordpress' ? "bg-zinc-900 text-white border-zinc-900" : "bg-white text-zinc-500 border-zinc-200 hover:border-zinc-300"
                            )}
                          >
                            WordPress
                          </button>
                          <button
                            type="button"
                            onClick={() => setPlatform('naver')}
                            className={cn(
                              "py-2 px-4 rounded-xl text-sm font-bold border transition-all",
                              platform === 'naver' ? "bg-emerald-600 text-white border-emerald-600" : "bg-white text-zinc-500 border-zinc-200 hover:border-zinc-300"
                            )}
                          >
                            Naver Blog
                          </button>
                        </div>
                      </div>

                      {platform === 'wordpress' && (
                        <div className="space-y-4">
                          <div className="flex items-center gap-2 py-2">
                            <input 
                              type="checkbox" 
                              id="schedule"
                              checked={shouldSchedule}
                              onChange={(e) => setShouldSchedule(e.target.checked)}
                              className="w-4 h-4 rounded border-zinc-300 text-emerald-600 focus:ring-emerald-500"
                            />
                            <label htmlFor="schedule" className="text-sm text-zinc-600 cursor-pointer">
                              예약 발행 (Future Post)
                            </label>
                          </div>
                          
                          <div className="p-4 bg-blue-50 rounded-2xl border border-blue-100 flex gap-3">
                            <AlertCircle className="text-blue-600 shrink-0" size={20} />
                            <p className="text-xs text-blue-700 leading-relaxed">
                              워드프레스는 자동 발행이 가능합니다. 초안(Draft)으로 먼저 저장하고 검수 후 발행하는 것을 권장합니다.
                            </p>
                          </div>
                        </div>
                      )}

                      {platform === 'naver' && (
                        <div className="p-4 bg-amber-50 rounded-2xl border border-amber-100 flex gap-3">
                          <AlertCircle className="text-amber-600 shrink-0" size={20} />
                          <p className="text-xs text-amber-700 leading-relaxed">
                            네이버 블로그는 자동 발행 API가 지원되지 않습니다. 생성된 '발행 패키지'를 복사하여 직접 붙여넣어주세요.
                          </p>
                        </div>
                      )}

                      <button 
                        type="submit"
                        disabled={isGenerating || !topic || !productLink}
                        className="w-full py-4 bg-zinc-900 text-white rounded-xl font-semibold flex items-center justify-center gap-2 hover:bg-zinc-800 disabled:opacity-50 disabled:cursor-not-allowed transition-all mt-8"
                      >
                        {isGenerating ? <Loader2 className="animate-spin" size={20} /> : <Sparkles size={20} />}
                        {isGenerating ? '생성 중...' : '포스트 생성하기'}
                      </button>
                      <p className="text-[10px] text-zinc-400 text-center mt-2">
                        * AdSense Compliance: 버튼 주변 32px 이상의 Safe Zone이 확보되었습니다.
                      </p>
                    </form>

                    <div className="bg-emerald-50 p-6 rounded-3xl border border-emerald-100 space-y-4">
                      <div className="flex items-center gap-2 text-emerald-700 font-semibold">
                        <ShieldCheck size={20} />
                        <span>Policy & Layout Engine</span>
                      </div>
                      <ul className="text-sm text-emerald-600/80 space-y-2">
                        <li className="flex gap-2">
                          <CheckCircle2 size={14} className="mt-0.5 shrink-0" />
                          <span>치료, 예방, 완치 단어 자동 필터링</span>
                        </li>
                        <li className="flex gap-2">
                          <CheckCircle2 size={14} className="mt-0.5 shrink-0" />
                          <span>AdSense 우발 클릭 방지 레이아웃 (Safe Zone)</span>
                        </li>
                        <li className="flex gap-2">
                          <CheckCircle2 size={14} className="mt-0.5 shrink-0" />
                          <span>신뢰 섹션(FAQ/주의점) 우선 배치 룰</span>
                        </li>
                        {platform === 'wordpress' && (
                          <>
                            <li className="flex gap-2">
                              <CheckCircle2 size={14} className="mt-0.5 shrink-0" />
                              <span>고유 H1 및 기술 SEO 최적화 (WP 전용)</span>
                            </li>
                            <li className="flex gap-2">
                              <CheckCircle2 size={14} className="mt-0.5 shrink-0" />
                              <span>Product/Review 구조화 데이터 제안</span>
                            </li>
                          </>
                        )}
                        <li className="flex gap-2">
                          <CheckCircle2 size={14} className="mt-0.5 shrink-0" />
                          <span>Scaled Content Abuse 방지 (원본 데이터 필수)</span>
                        </li>
                        <li className="flex gap-2">
                          <CheckCircle2 size={14} className="mt-0.5 shrink-0" />
                          <span>Thin Content 및 키워드 도배(스팸) 방지</span>
                        </li>
                        <li className="flex gap-2">
                          <CheckCircle2 size={14} className="mt-0.5 shrink-0" />
                          <span>YMYL 위험 표현(무조건, 완치 등) 차단</span>
                        </li>
                        <li className="flex gap-2">
                          <CheckCircle2 size={14} className="mt-0.5 shrink-0" />
                          <span>수익 자동화: 링크/전환 트래킹(UTM) 자동 생성</span>
                        </li>
                      </ul>
                    </div>
                  </div>

                  {/* Preview Area */}
                  <div className="lg:col-span-2">
                    <div className="bg-white rounded-3xl shadow-sm border border-black/5 min-h-[600px] overflow-hidden flex flex-col">
                      <div className="px-6 py-4 border-b border-black/5 flex items-center justify-between bg-zinc-50/50">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-medium text-zinc-500">Preview</span>
                          {currentQualityNotes && (
                            <span className="text-[10px] bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded-full font-bold flex items-center gap-1">
                              <ShieldCheck size={10} /> Quality Passed
                            </span>
                          )}
                        </div>
                        <div className="flex gap-2">
                          {currentBlog && platform === 'naver' && (
                            <button
                              onClick={() => {
                                navigator.clipboard.writeText(currentBlog);
                                alert('클립보드에 복사되었습니다. 네이버 블로그에 붙여넣으세요!');
                              }}
                              className="text-[10px] font-bold text-emerald-600 hover:text-emerald-700 flex items-center gap-1"
                            >
                              <FileText size={12} /> Copy for Naver
                            </button>
                          )}
                          <div className="w-3 h-3 rounded-full bg-red-400" />
                          <div className="w-3 h-3 rounded-full bg-amber-400" />
                          <div className="w-3 h-3 rounded-full bg-emerald-400" />
                        </div>
                      </div>
                      
                      <div className="flex-1 p-8 md:p-12 overflow-y-auto max-h-[800px]">
                        {currentBlog ? (
                          <div className="markdown-body">
                            {currentQualityNotes && (
                              <div className="mb-8 p-4 bg-zinc-50 rounded-2xl border border-black/5 text-xs text-zinc-500 italic">
                                <strong>Quality Gate Notes:</strong> {currentQualityNotes}
                              </div>
                            )}
                            
                            {currentAudit && (
                              <div className={cn(
                                "mb-8 p-6 rounded-3xl border space-y-4",
                                currentAudit.status === 'draft' ? "bg-red-50 border-red-100" : "bg-zinc-50 border-zinc-100"
                              )}>
                                <div className="flex items-center justify-between">
                                  <h4 className={cn(
                                    "font-bold flex items-center gap-2",
                                    currentAudit.status === 'draft' ? "text-red-800" : "text-zinc-800"
                                  )}>
                                    <ShieldCheck size={18} /> Quality Audit Result
                                  </h4>
                                  <div className="flex items-center gap-2">
                                    <span className="text-xs font-bold text-zinc-400 uppercase">Score</span>
                                    <span className={cn(
                                      "text-2xl font-serif font-bold",
                                      currentAudit.score >= 80 ? "text-emerald-600" : currentAudit.score >= 60 ? "text-amber-600" : "text-red-600"
                                    )}>{currentAudit.score}</span>
                                  </div>
                                </div>

                                {currentAudit.fails.length > 0 && (
                                  <div className="space-y-2">
                                    <p className="text-[10px] font-bold text-red-600 uppercase">Critical Fails (Draft Only)</p>
                                    <ul className="space-y-1">
                                      {currentAudit.fails.map((f, i) => (
                                        <li key={i} className="text-sm text-red-700 flex items-start gap-2">
                                          <AlertCircle size={14} className="mt-0.5 shrink-0" />
                                          <div>
                                            <span className="font-bold text-xs bg-red-100 px-1 rounded mr-1">{f.code}</span>
                                            {f.detail}
                                          </div>
                                        </li>
                                      ))}
                                    </ul>
                                  </div>
                                )}

                                {currentAudit.warns.length > 0 && (
                                  <div className="space-y-2">
                                    <p className="text-[10px] font-bold text-amber-600 uppercase">Warnings</p>
                                    <ul className="space-y-1">
                                      {currentAudit.warns.map((w, i) => (
                                        <li key={i} className="text-sm text-amber-700 flex items-start gap-2">
                                          <AlertTriangle size={14} className="mt-0.5 shrink-0" />
                                          <div>
                                            <span className="font-bold text-xs bg-amber-100 px-1 rounded mr-1">{w.code}</span>
                                            {w.detail}
                                          </div>
                                        </li>
                                      ))}
                                    </ul>
                                  </div>
                                )}

                                {currentAudit.checklist.length > 0 && (
                                  <div className="space-y-2 pt-2 border-t border-black/5">
                                    <p className="text-[10px] font-bold text-zinc-400 uppercase">Final Checklist</p>
                                    <ul className="space-y-1">
                                      {currentAudit.checklist.map((c, i) => (
                                        <li key={i} className="text-sm text-zinc-600 flex items-center gap-2">
                                          <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 shrink-0" /> {c}
                                        </li>
                                      ))}
                                    </ul>
                                  </div>
                                )}
                              </div>
                            )}

                            {platform === 'naver' && (
                              <div className="mb-8 p-6 bg-emerald-50 rounded-3xl border border-emerald-100 space-y-4">
                                <h4 className="font-bold text-emerald-800 flex items-center gap-2">
                                  <FileText size={18} /> Naver Publishing Package
                                </h4>
                                <div className="space-y-3">
                                  <div className="p-3 bg-white rounded-xl border border-emerald-200">
                                    <p className="text-[10px] font-bold text-emerald-600 uppercase mb-1">Hashtags</p>
                                    <p className="text-sm text-zinc-600">{currentHashtags.join(' ')}</p>
                                  </div>
                                  <div className="p-3 bg-white rounded-xl border border-emerald-200">
                                    <p className="text-[10px] font-bold text-emerald-600 uppercase mb-1">Disclaimer</p>
                                    <p className="text-sm text-zinc-600">{currentDisclaimer}</p>
                                  </div>
                                  <button 
                                    onClick={() => {
                                      const fullText = `${currentBlog}\n\n${currentDisclaimer}\n\n${currentHashtags.join(' ')}`;
                                      navigator.clipboard.writeText(fullText);
                                      alert('발행 패키지 전체가 복사되었습니다!');
                                    }}
                                    className="w-full py-2 bg-emerald-600 text-white rounded-xl text-xs font-bold hover:bg-emerald-700 transition-all"
                                  >
                                    전체 복사하기 (본문 + 면책 + 태그)
                                  </button>
                                </div>
                              </div>
                            )}

                            <Markdown>{currentBlog}</Markdown>
                            <div className="mt-12 p-8 bg-zinc-900 rounded-2xl text-center space-y-4">
                              <h4 className="text-white font-serif text-xl">지금 바로 건강한 변화를 시작하세요</h4>
                              <p className="text-zinc-400 text-sm">엄격한 기준으로 선별한 프리미엄 원료만을 담았습니다.</p>
                              <a 
                                href={productLink} 
                                target="_blank" 
                                rel="noopener noreferrer"
                                className="inline-flex items-center gap-2 px-8 py-3 bg-emerald-500 text-white rounded-full font-bold hover:bg-emerald-400 transition-colors"
                              >
                                제품 상세 보기 <ChevronRight size={18} />
                              </a>
                            </div>
                          </div>
                        ) : (
                          <div className="h-full flex flex-col items-center justify-center text-zinc-300 space-y-4">
                            <Sparkles size={48} strokeWidth={1} />
                            <p>주제와 링크를 입력하고 포스트를 생성해보세요.</p>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </motion.div>
            )}

            {activeTab === 'lab' && (
              <motion.div
                key="lab"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="space-y-8"
              >
                <header className="flex justify-between items-end">
                  <div>
                    <h1 className="text-4xl font-serif font-bold tracking-tight mb-2">Keyword Lab</h1>
                    <p className="text-zinc-500">데이터 기반 황금 키워드 소싱 및 콘텐츠 기획</p>
                  </div>
                  <button 
                    onClick={handleSourceKeywords}
                    disabled={isSourcing}
                    className="px-6 py-3 bg-zinc-900 text-white rounded-xl font-semibold flex items-center gap-2 hover:bg-zinc-800 disabled:opacity-50 transition-all"
                  >
                    {isSourcing ? <Loader2 className="animate-spin" size={18} /> : <Zap size={18} />}
                    황금 키워드 소싱하기
                  </button>
                </header>

                <div className="grid grid-cols-1 gap-6">
                  {keywords.map((k) => (
                    <div key={k.id} className="bg-white rounded-3xl border border-black/5 overflow-hidden shadow-sm">
                      <div className="p-6 flex flex-wrap items-center justify-between gap-6">
                        <div className="flex items-center gap-4">
                          <div className="w-12 h-12 bg-zinc-50 rounded-2xl flex items-center justify-center text-zinc-400">
                            <TrendingUp size={24} />
                          </div>
                          <div>
                            <h3 className="text-xl font-bold">{k.keyword}</h3>
                            <div className="flex items-center gap-4 mt-1">
                              <span className="text-xs text-zinc-400 flex items-center gap-1">
                                <BarChart3 size={12} /> 월 검색량: {k.volume.toLocaleString()}
                              </span>
                              <span className={cn(
                                "text-xs font-bold px-2 py-0.5 rounded-full",
                                k.competition_ratio < 0.5 ? "bg-emerald-50 text-emerald-600" : "bg-amber-50 text-amber-600"
                              )}>
                                경쟁 강도: {k.competition_ratio.toFixed(2)}
                              </span>
                            </div>
                          </div>
                        </div>

                        <div className="flex items-center gap-3">
                          {k.status === 'sourced' && (
                            <button 
                              onClick={() => handlePlanKeyword(k.id)}
                              disabled={isPlanning === k.id}
                              className="px-4 py-2 bg-emerald-50 text-emerald-600 rounded-lg text-sm font-bold flex items-center gap-2 hover:bg-emerald-100 transition-colors"
                            >
                              {isPlanning === k.id ? <Loader2 className="animate-spin" size={16} /> : <FileText size={16} />}
                              콘텐츠 기획(AI Handoff)
                            </button>
                          )}
                          {k.status === 'planned' && (
                            <button 
                              onClick={() => {
                                setTopic(k.keyword);
                                setActiveTab('factory');
                              }}
                              className="px-4 py-2 bg-zinc-900 text-white rounded-lg text-sm font-bold flex items-center gap-2 hover:bg-zinc-800 transition-colors"
                            >
                              <Sparkles size={16} />
                              포스트 생성하기
                            </button>
                          )}
                          <button 
                            onClick={() => handleDeleteKeyword(k.id)}
                            className="p-2 text-zinc-300 hover:text-red-500 transition-colors"
                          >
                            <Trash2 size={18} />
                          </button>
                        </div>
                      </div>

                      {k.outline && (
                        <div className="px-6 pb-6 pt-2 border-t border-black/5 bg-zinc-50/30">
                          <div className="flex items-center gap-2 mb-3 text-xs font-bold text-zinc-400 uppercase tracking-widest">
                            <FileText size={14} /> AI Content Outline
                          </div>
                          <div className="prose prose-sm max-w-none text-zinc-600">
                            <Markdown>{k.outline}</Markdown>
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                  {keywords.length === 0 && (
                    <div className="py-20 text-center text-zinc-400 border-2 border-dashed border-zinc-200 rounded-3xl">
                      소싱된 키워드가 없습니다. 상단 버튼을 눌러 소싱을 시작하세요.
                    </div>
                  )}
                </div>
              </motion.div>
            )}

            {activeTab === 'history' && (
              <motion.div
                key="history"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="space-y-8"
              >
                <header>
                  <h1 className="text-4xl font-serif font-bold tracking-tight mb-2">Content History</h1>
                  <p className="text-zinc-500">지금까지 생성된 모든 콘텐츠를 관리합니다.</p>
                </header>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {blogs.map((blog) => (
                    <div key={blog.id} className="bg-white p-6 rounded-3xl border border-black/5 hover:border-emerald-500/30 transition-all group">
                      <div className="flex justify-between items-start mb-4">
                        <div className="flex flex-col gap-1">
                          <span className="text-[10px] font-bold uppercase tracking-widest text-zinc-400">
                            {new Date(blog.created_at).toLocaleDateString()}
                          </span>
                          <span className={cn(
                            "text-[10px] font-bold px-2 py-0.5 rounded-full w-fit flex items-center gap-1",
                            blog.status === 'published' ? "bg-emerald-50 text-emerald-600" : 
                            blog.status === 'scheduled' ? "bg-blue-50 text-blue-600" : 
                            "bg-red-50 text-red-600"
                          )}>
                            {blog.status === 'published' ? <CheckCircle2 size={10} /> : 
                             blog.status === 'scheduled' ? <Clock size={10} /> : 
                             <XCircle size={10} />}
                            {blog.status.toUpperCase()}
                          </span>
                          <div className="flex items-center gap-2">
                            <span className={cn(
                              "text-[10px] font-bold px-2 py-0.5 rounded-full w-fit",
                              blog.platform === 'naver' ? "bg-green-50 text-green-600" : "bg-zinc-100 text-zinc-600"
                            )}>
                              {blog.platform.toUpperCase()}
                            </span>
                            {blog.disclosure_type && blog.disclosure_type !== 'none' && (
                              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full w-fit bg-amber-50 text-amber-600">
                                {blog.disclosure_type.toUpperCase()}
                              </span>
                            )}
                            {blog.audit_score !== undefined && (
                              <span className={cn(
                                "text-[10px] font-bold px-2 py-0.5 rounded-full w-fit",
                                blog.audit_score >= 80 ? "bg-emerald-50 text-emerald-600" : 
                                blog.audit_score >= 60 ? "bg-amber-50 text-amber-600" : 
                                "bg-red-50 text-red-600"
                              )}>
                                SCORE: {blog.audit_score}
                              </span>
                            )}
                            {blog.is_winning_template === 1 && (
                              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full w-fit bg-purple-50 text-purple-600 flex items-center gap-1">
                                <TrendingUp size={10} /> WINNING
                              </span>
                            )}
                          </div>
                          {blog.status === 'draft' && blog.audit_fails && JSON.parse(blog.audit_fails).length > 0 && (
                            <div className="mt-2 p-2 bg-red-50 rounded-lg border border-red-100">
                              <p className="text-[9px] font-bold text-red-600 uppercase mb-1 flex items-center gap-1">
                                <AlertCircle size={10} /> QA 결함 발견 (발행 제한됨)
                              </p>
                              <ul className="text-[9px] text-red-500 list-disc list-inside">
                                {JSON.parse(blog.audit_fails).map((fail: string, i: number) => (
                                  <li key={i}>{fail}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>
                        <div className="flex flex-col gap-2">
                          <button 
                            onClick={() => {
                              setCurrentBlog(blog.content);
                              setCurrentQualityNotes(blog.quality_notes || null);
                              setCurrentHashtags(blog.hashtags ? JSON.parse(blog.hashtags) : []);
                              setCurrentDisclaimer(blog.disclaimer || null);
                              setCurrentAudit(blog.audit_score ? {
                                score: blog.audit_score,
                                fails: blog.audit_fails ? JSON.parse(blog.audit_fails) : [],
                                warns: blog.audit_warns ? JSON.parse(blog.audit_warns) : [],
                                checklist: blog.audit_checklist ? JSON.parse(blog.audit_checklist) : [],
                                status: blog.status
                              } : null);
                              setDisclosureType(blog.disclosure_type || 'none');
                              setPageType(blog.page_type || 'review');
                              setCategory(blog.category || '건강/영양제');
                              setProductLink(blog.product_link);
                              setPlatform(blog.platform);
                              setActiveTab('factory');
                            }}
                            className="text-emerald-600 opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1 text-xs font-semibold"
                          >
                            불러오기 <ChevronRight size={14} />
                          </button>
                          {blog.platform === 'wordpress' && (
                            <div className="flex flex-col gap-1">
                              <button 
                                onClick={() => handlePublish(blog.id, 'publish')}
                                disabled={isPublishing === blog.id}
                                className="text-blue-600 opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1 text-[10px] font-bold disabled:opacity-50 hover:underline"
                              >
                                {isPublishing === blog.id ? <Loader2 className="animate-spin" size={10} /> : <ExternalLink size={10} />}
                                WP 즉시 발행
                              </button>
                              <button 
                                onClick={() => handlePublish(blog.id, 'future')}
                                disabled={isPublishing === blog.id}
                                className="text-indigo-600 opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1 text-[10px] font-bold disabled:opacity-50 hover:underline"
                              >
                                <Clock size={10} /> WP 예약 발행
                              </button>
                              <button 
                                onClick={() => handlePublish(blog.id, 'draft')}
                                disabled={isPublishing === blog.id}
                                className="text-zinc-500 opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1 text-[10px] font-bold disabled:opacity-50 hover:underline"
                              >
                                <FileText size={10} /> WP 임시저장
                              </button>
                            </div>
                          )}
                          {blog.platform === 'naver' && (
                            <button 
                              onClick={() => setViewingPackage(blog)}
                              className="text-green-600 opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1 text-xs font-semibold"
                            >
                              <FileText size={12} /> 발행 패키지 보기
                            </button>
                          )}
                          <button 
                            onClick={async () => {
                              try {
                                const res = await fetch(`/api/blogs/${blog.id}/winning`, { method: 'POST' });
                                if (res.ok) {
                                  const updated = await res.json();
                                  setBlogs(blogs.map(b => b.id === blog.id ? { ...b, is_winning_template: updated.is_winning_template } : b));
                                }
                              } catch (e) { console.error(e); }
                            }}
                            className={cn(
                              "text-[10px] font-bold transition-opacity flex items-center gap-1 opacity-0 group-hover:opacity-100",
                              blog.is_winning_template === 1 ? "text-purple-600" : "text-zinc-400 hover:text-purple-600"
                            )}
                          >
                            <TrendingUp size={10} /> {blog.is_winning_template === 1 ? '성과 해제' : '성과 등록'}
                          </button>
                        </div>
                      </div>
                      <h3 className="text-xl font-serif font-bold mb-2 line-clamp-1">{blog.topic}</h3>
                      <p className="text-zinc-400 text-[10px] font-medium mb-2 italic line-clamp-2">SEO: {blog.meta_description}</p>
                      <p className="text-zinc-500 text-sm line-clamp-3 mb-4">{blog.content.substring(0, 150)}...</p>
                      <div className="flex items-center gap-2 text-xs text-zinc-400">
                        <ExternalLink size={12} />
                        <span className="truncate">{blog.product_link}</span>
                      </div>
                    </div>
                  ))}
                  {blogs.length === 0 && (
                    <div className="col-span-full py-20 text-center text-zinc-400 border-2 border-dashed border-zinc-200 rounded-3xl">
                      생성된 콘텐츠가 없습니다.
                    </div>
                  )}
                </div>
              </motion.div>
            )}

            {activeTab === 'products' && (
              <motion.div 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="space-y-8"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-3xl font-serif font-bold text-zinc-900">Product DB</h2>
                    <p className="text-zinc-500">상품 원천 데이터를 관리하여 AI 생성 품질을 높입니다.</p>
                  </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                  <div className="lg:col-span-1">
                    <form onSubmit={handleAddProduct} className="bg-white p-6 rounded-3xl shadow-sm border border-black/5 space-y-4 sticky top-8">
                      <h3 className="font-bold border-b pb-2 mb-4">새 상품 등록</h3>
                      <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-1">
                          <label className="text-[10px] font-bold text-zinc-400 uppercase">SKU</label>
                          <input type="text" value={newProduct.sku} onChange={e => setNewProduct({...newProduct, sku: e.target.value})} className="w-full p-2 text-sm bg-zinc-50 border rounded-lg" placeholder="PROD-001" />
                        </div>
                        <div className="space-y-1">
                          <label className="text-[10px] font-bold text-zinc-400 uppercase">가격</label>
                          <input type="number" value={newProduct.price} onChange={e => setNewProduct({...newProduct, price: parseInt(e.target.value)})} className="w-full p-2 text-sm bg-zinc-50 border rounded-lg" placeholder="29000" />
                        </div>
                      </div>
                      <div className="space-y-1">
                        <label className="text-[10px] font-bold text-zinc-400 uppercase">상품명</label>
                        <input type="text" value={newProduct.name} onChange={e => setNewProduct({...newProduct, name: e.target.value})} className="w-full p-2 text-sm bg-zinc-50 border rounded-lg" placeholder="식물성 콘드로이친 1200" />
                      </div>
                      <div className="space-y-1">
                        <label className="text-[10px] font-bold text-zinc-400 uppercase">핵심 USP (3가지)</label>
                        <textarea value={newProduct.usp} onChange={e => setNewProduct({...newProduct, usp: e.target.value})} className="w-full p-2 text-sm bg-zinc-50 border rounded-lg h-20" placeholder="1. 100% 식물성 원료&#10;2. 고함량 1200mg&#10;3. 흡수율 최적화 공법" />
                      </div>
                      <div className="space-y-1">
                        <label className="text-[10px] font-bold text-zinc-400 uppercase">타겟 고객</label>
                        <input type="text" value={newProduct.target} onChange={e => setNewProduct({...newProduct, target: e.target.value})} className="w-full p-2 text-sm bg-zinc-50 border rounded-lg" placeholder="4050 무릎 관절 고민 여성" />
                      </div>
                      <div className="space-y-1">
                        <label className="text-[10px] font-bold text-zinc-400 uppercase">상품 링크</label>
                        <input type="url" value={newProduct.product_link} onChange={e => setNewProduct({...newProduct, product_link: e.target.value})} className="w-full p-2 text-sm bg-zinc-50 border rounded-lg" placeholder="https://..." />
                      </div>
                      <div className="space-y-1">
                        <label className="text-[10px] font-bold text-zinc-400 uppercase">옵션 정보</label>
                        <input type="text" value={newProduct.options} onChange={e => setNewProduct({...newProduct, options: e.target.value})} className="w-full p-2 text-sm bg-zinc-50 border rounded-lg" placeholder="예: 30일분, 60일분, 선물세트" />
                      </div>
                      <div className="space-y-1">
                        <label className="text-[10px] font-bold text-zinc-400 uppercase">A/S 및 고객지원</label>
                        <input type="text" value={newProduct.as_info} onChange={e => setNewProduct({...newProduct, as_info: e.target.value})} className="w-full p-2 text-sm bg-zinc-50 border rounded-lg" placeholder="예: 100% 환불 보장, 24시간 상담" />
                      </div>
                      <div className="space-y-1">
                        <label className="text-[10px] font-bold text-zinc-400 uppercase">금지 표현 (심의 방어)</label>
                        <input type="text" value={newProduct.prohibited_expressions} onChange={e => setNewProduct({...newProduct, prohibited_expressions: e.target.value})} className="w-full p-2 text-sm bg-zinc-50 border rounded-lg" placeholder="예: 완치, 특효, 무조건" />
                      </div>
                      <div className="space-y-1">
                        <label className="text-[10px] font-bold text-zinc-400 uppercase">필수 면책 문구</label>
                        <textarea value={newProduct.mandatory_disclaimer} onChange={e => setNewProduct({...newProduct, mandatory_disclaimer: e.target.value})} className="w-full p-2 text-sm bg-zinc-50 border rounded-lg h-16" placeholder="예: 질병의 예방 및 치료를 위한 의약품이 아닙니다." />
                      </div>
                      <div className="space-y-1">
                        <label className="text-[10px] font-bold text-zinc-400 uppercase">증거 데이터 (Evidence Log)</label>
                        <textarea value={newProduct.evidence_data} onChange={e => setNewProduct({...newProduct, evidence_data: e.target.value})} className="w-full p-2 text-sm bg-zinc-50 border rounded-lg h-16" placeholder="예: 2주 사용 후 수분도 15% 상승 테스트 완료" />
                      </div>
                      <button type="submit" className="w-full py-3 bg-emerald-600 text-white rounded-xl font-bold hover:bg-emerald-700 transition-all">
                        상품 저장하기
                      </button>
                    </form>
                  </div>

                  <div className="lg:col-span-2 space-y-4">
                    {products.length === 0 ? (
                      <div className="bg-white p-12 rounded-3xl border border-dashed border-zinc-200 text-center">
                        <Package className="mx-auto text-zinc-300 mb-4" size={48} />
                        <p className="text-zinc-500">등록된 상품이 없습니다. 첫 상품을 등록해보세요.</p>
                      </div>
                    ) : (
                      products.map(product => (
                        <div key={product.id} className="bg-white p-6 rounded-3xl border border-black/5 group hover:border-emerald-500/30 transition-all">
                          <div className="flex justify-between items-start mb-4">
                            <div>
                              <div className="flex items-center gap-2 mb-1">
                                <span className="text-[10px] font-bold bg-zinc-100 px-2 py-0.5 rounded text-zinc-500">{product.sku}</span>
                                <h3 className="font-bold text-lg">{product.name}</h3>
                              </div>
                              <p className="text-xs text-zinc-400">{product.target}</p>
                            </div>
                            <button onClick={() => handleDeleteProduct(product.id)} className="text-zinc-300 hover:text-red-500 transition-colors">
                              <Trash2 size={18} />
                            </button>
                          </div>
                          
                          <div className="grid grid-cols-2 gap-6 text-sm">
                            <div className="space-y-2">
                              <h4 className="text-[10px] font-bold text-zinc-400 uppercase">Core USP</h4>
                              <p className="text-zinc-600 whitespace-pre-line leading-relaxed">{product.usp}</p>
                            </div>
                            <div className="space-y-2">
                              <h4 className="text-[10px] font-bold text-zinc-400 uppercase">Details</h4>
                              <div className="space-y-1 text-xs">
                                <div className="flex justify-between border-b pb-1"><span className="text-zinc-400">Price</span><span>{product.price.toLocaleString()}원</span></div>
                                <div className="flex justify-between border-b pb-1"><span className="text-zinc-400">Options</span><span>{product.options || '-'}</span></div>
                                <div className="flex justify-between border-b pb-1"><span className="text-zinc-400">A/S</span><span>{product.as_info || '-'}</span></div>
                                <div className="flex justify-between border-b pb-1"><span className="text-zinc-400">Link</span><a href={product.product_link} target="_blank" className="text-emerald-600 truncate max-w-[150px]">Store Link</a></div>
                              </div>
                            </div>
                          </div>
                          <div className="mt-4 pt-4 border-t grid grid-cols-3 gap-4 text-[10px]">
                            <div className="space-y-1">
                              <span className="font-bold text-zinc-400 uppercase">Prohibited</span>
                              <p className="text-red-500 line-clamp-1">{product.prohibited_expressions || '-'}</p>
                            </div>
                            <div className="space-y-1">
                              <span className="font-bold text-zinc-400 uppercase">Disclaimer</span>
                              <p className="text-zinc-500 line-clamp-1">{product.mandatory_disclaimer || '-'}</p>
                            </div>
                            <div className="space-y-1">
                              <span className="font-bold text-zinc-400 uppercase">Evidence</span>
                              <p className="text-blue-500 line-clamp-1">{product.evidence_data || '-'}</p>
                            </div>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              </motion.div>
            )}
            {activeTab === 'settings' && (
              <motion.div
                key="settings"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="max-w-2xl space-y-8"
              >
                <header>
                  <h1 className="text-4xl font-serif font-bold tracking-tight mb-2">Settings</h1>
                  <p className="text-zinc-500">트래픽 추적 및 마케팅 픽셀 설정을 관리합니다.</p>
                </header>

                <div className="space-y-6">
                  <div className="bg-white p-8 rounded-3xl border border-black/5 space-y-6">
                    <div className="flex items-center gap-3 pb-4 border-b border-black/5">
                      <div className="w-10 h-10 bg-blue-50 rounded-xl flex items-center justify-center text-blue-600">
                        <BarChart3 size={20} />
                      </div>
                      <div>
                        <h3 className="font-bold">Tracking & Analytics</h3>
                        <p className="text-xs text-zinc-400">리타겟팅 광고를 위한 스크립트 설정</p>
                      </div>
                    </div>

                    <div className="space-y-4">
                      <div className="space-y-2">
                        <label className="text-xs font-semibold uppercase tracking-wider text-zinc-400">Meta Pixel ID</label>
                        <input 
                          type="text" 
                          value={pixelId}
                          onChange={(e) => setPixelId(e.target.value)}
                          placeholder="예: 123456789012345"
                          className="w-full px-4 py-3 rounded-xl bg-zinc-50 border border-zinc-200 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all"
                        />
                      </div>
                      <div className="space-y-2">
                        <label className="text-xs font-semibold uppercase tracking-wider text-zinc-400">GA4 Measurement ID</label>
                        <input 
                          type="text" 
                          value={gaId}
                          onChange={(e) => setGaId(e.target.value)}
                          placeholder="예: G-XXXXXXXXXX"
                          className="w-full px-4 py-3 rounded-xl bg-zinc-50 border border-zinc-200 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all"
                        />
                      </div>
                    </div>

                    <div className="p-4 bg-amber-50 rounded-2xl border border-amber-100 flex gap-3">
                      <AlertCircle className="text-amber-600 shrink-0" size={20} />
                      <p className="text-xs text-amber-700 leading-relaxed">
                        픽셀과 GA4 설정은 워드프레스 헤더에 자동으로 삽입됩니다. 이탈 고객 리타겟팅을 위해 반드시 설정하는 것을 권장합니다.
                      </p>
                    </div>

                    <button className="w-full py-4 bg-zinc-900 text-white rounded-xl font-semibold hover:bg-zinc-800 transition-all">
                      설정 저장하기
                    </button>
                  </div>

                  <div className="bg-white p-8 rounded-3xl border border-black/5 space-y-6">
                    <div className="flex items-center gap-3 pb-4 border-b border-black/5">
                      <div className="w-10 h-10 bg-purple-50 rounded-xl flex items-center justify-center text-purple-600">
                        <ShieldCheck size={20} />
                      </div>
                      <div>
                        <h3 className="font-bold">Quality Audit MVP Specification</h3>
                        <p className="text-xs text-zinc-400">콘텐츠 검수 프로그램 작동 원리 및 기준</p>
                      </div>
                    </div>

                    <div className="space-y-6 text-sm">
                      <div className="space-y-2">
                        <h4 className="font-bold text-zinc-900 flex items-center gap-2">
                          <CheckCircle2 size={16} className="text-emerald-500" />
                          룰 기반 검사 (Deterministic)
                        </h4>
                        <ul className="list-disc pl-5 space-y-1 text-zinc-600 text-xs">
                          <li><b>구조 체크:</b> H2 태그 3개 이상, FAQ 섹션 필수 포함 여부</li>
                          <li><b>키워드 밀도:</b> 주제 키워드가 본문 내 15회 이상 반복 시 경고 (스터핑 방지)</li>
                          <li><b>링크 정책:</b> 외부 링크 5개 초과 시 스팸 의심 경고</li>
                          <li><b>법적 고지:</b> 선택한 고지 문구([광고], [협찬] 등)가 본문 맨 앞에 있는지 확인</li>
                        </ul>
                      </div>

                      <div className="space-y-2">
                        <h4 className="font-bold text-zinc-900 flex items-center gap-2">
                          <Sparkles size={16} className="text-purple-500" />
                          AI 휴리스틱 검사 (LLM-based)
                        </h4>
                        <ul className="list-disc pl-5 space-y-1 text-zinc-600 text-xs">
                          <li><b>정보의 직접성:</b> 유저가 검색 의도에 맞는 답을 즉시 얻을 수 있는가?</li>
                          <li><b>경험/신뢰성:</b> '나만의 데이터'가 자연스럽게 녹아들어 실제 경험처럼 느껴지는가?</li>
                          <li><b>심의 준수:</b> 건기식 심의 위반 소지(치료, 완치 등)가 없는가?</li>
                          <li><b>반복성:</b> AI 특유의 의미 없는 문장 반복이나 패턴이 없는가?</li>
                        </ul>
                      </div>

                      <div className="space-y-2">
                        <h4 className="font-bold text-zinc-900 flex items-center gap-2">
                          <AlertTriangle size={16} className="text-red-500" />
                          자동 차단 (Fail) 조건
                        </h4>
                        <p className="text-xs text-zinc-600 leading-relaxed">
                          다음 조건 중 하나라도 해당되면 <b>'DRAFT(임시저장)'</b> 상태로 저장되며 자동 발행이 차단됩니다:
                        </p>
                        <ul className="list-disc pl-5 space-y-1 text-zinc-600 text-xs">
                          <li>경제적 이해관계 표시(Disclosure)가 누락된 경우</li>
                          <li>AI가 판단한 치명적 결함(LLM Fail)이 1개 이상인 경우</li>
                          <li>종합 점수(Audit Score)가 70점 미만인 경우</li>
                          <li>주의 사항(Warn)이 3개 이상 누적된 경우</li>
                        </ul>
                      </div>
                    </div>
                  </div>

                  <div className="bg-white p-8 rounded-3xl border border-black/5 space-y-6">
                    <div className="flex items-center gap-3 pb-4 border-b border-black/5">
                      <div className="w-10 h-10 bg-emerald-50 rounded-xl flex items-center justify-center text-emerald-600">
                        <ExternalLink size={20} />
                      </div>
                      <div>
                        <h3 className="font-bold">WordPress Integration</h3>
                        <p className="text-xs text-zinc-400">자동 발행을 위한 워드프레스 API 설정</p>
                      </div>
                    </div>

                    <div className="space-y-4">
                      <div className="space-y-2">
                        <label className="text-xs font-semibold uppercase tracking-wider text-zinc-400">WordPress URL</label>
                        <input 
                          type="url" 
                          value={wpUrl}
                          onChange={(e) => setWpUrl(e.target.value)}
                          placeholder="https://your-domain.com"
                          className="w-full px-4 py-3 rounded-xl bg-zinc-50 border border-zinc-200 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all"
                        />
                      </div>
                      <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                          <label className="text-xs font-semibold uppercase tracking-wider text-zinc-400">WP Username</label>
                          <input 
                            type="text" 
                            value={wpUser}
                            onChange={(e) => setWpUser(e.target.value)}
                            placeholder="admin"
                            className="w-full px-4 py-3 rounded-xl bg-zinc-50 border border-zinc-200 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all"
                          />
                        </div>
                        <div className="space-y-2">
                          <label className="text-xs font-semibold uppercase tracking-wider text-zinc-400">Application Password</label>
                          <input 
                            type="password" 
                            value={wpPass}
                            onChange={(e) => setWpPass(e.target.value)}
                            placeholder="xxxx xxxx xxxx xxxx"
                            className="w-full px-4 py-3 rounded-xl bg-zinc-50 border border-zinc-200 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all"
                          />
                        </div>
                      </div>
                    </div>

                    <div className="p-4 bg-emerald-50 rounded-2xl border border-emerald-100 flex gap-3">
                      <AlertCircle className="text-emerald-600 shrink-0" size={20} />
                      <p className="text-xs text-emerald-700 leading-relaxed">
                        워드프레스 관리자 페이지 {'>'} 사용자 {'>'} 프로필에서 '애플리케이션 비밀번호'를 생성하여 입력해주세요. 일반 비밀번호는 작동하지 않습니다.
                      </p>
                    </div>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </main>

      <AnimatePresence>
        {viewingPackage && (
          <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <motion.div 
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-white w-full max-w-3xl max-h-[90vh] rounded-[40px] shadow-2xl overflow-hidden flex flex-col"
            >
              <div className="p-8 border-b flex items-center justify-between bg-zinc-50">
                <div>
                  <h2 className="text-2xl font-serif font-bold">Naver Publishing Package</h2>
                  <p className="text-sm text-zinc-500">네이버 블로그 발행을 위한 최종 패키지입니다.</p>
                </div>
                <button 
                  onClick={() => setViewingPackage(null)}
                  className="w-10 h-10 rounded-full bg-white border flex items-center justify-center text-zinc-400 hover:text-zinc-900 transition-colors"
                >
                  <X size={20} />
                </button>
              </div>

              <div className="flex-1 overflow-y-auto p-8 space-y-8">
                <section className="space-y-3">
                  <div className="flex items-center justify-between">
                    <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-400">1. 제목 (Title)</h3>
                    <button 
                      onClick={() => {
                        navigator.clipboard.writeText(viewingPackage.topic);
                        alert('제목이 복사되었습니다.');
                      }}
                      className="text-[10px] font-bold text-emerald-600 hover:underline"
                    >
                      제목 복사
                    </button>
                  </div>
                  <div className="p-4 bg-zinc-50 rounded-2xl border font-bold text-lg">
                    {viewingPackage.topic}
                  </div>
                </section>

                <section className="space-y-3">
                  <div className="flex items-center justify-between">
                    <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-400">2. 본문 (Content)</h3>
                    <button 
                      onClick={() => {
                        navigator.clipboard.writeText(viewingPackage.content);
                        alert('본문이 복사되었습니다.');
                      }}
                      className="text-[10px] font-bold text-emerald-600 hover:underline"
                    >
                      본문 전체 복사
                    </button>
                  </div>
                  <div className="p-6 bg-zinc-50 rounded-2xl border text-sm leading-relaxed whitespace-pre-wrap max-h-96 overflow-y-auto font-sans text-zinc-700">
                    {viewingPackage.content}
                  </div>
                </section>

                <section className="space-y-3">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-400">3. 해시태그 (Hashtags)</h3>
                  <div className="flex flex-wrap gap-2">
                    {viewingPackage.hashtags && JSON.parse(viewingPackage.hashtags).map((tag: string, i: number) => (
                      <span key={i} className="px-3 py-1 bg-emerald-50 text-emerald-700 rounded-full text-xs font-medium">#{tag}</span>
                    ))}
                  </div>
                </section>

                <div className="p-6 bg-amber-50 rounded-3xl border border-amber-100 flex gap-4">
                  <div className="w-12 h-12 bg-amber-100 rounded-2xl flex items-center justify-center text-amber-600 shrink-0">
                    <AlertCircle size={24} />
                  </div>
                  <div className="space-y-1">
                    <h4 className="font-bold text-amber-900">발행 전 최종 체크</h4>
                    <p className="text-xs text-amber-700 leading-relaxed">
                      본문 내 <span className="font-bold">[사진: ...]</span> 위치에 실제 촬영하신 사진을 삽입해주세요. 
                      네이버는 직접 찍은 사진의 메타데이터를 중요하게 평가합니다.
                    </p>
                  </div>
                </div>
              </div>

              <div className="p-8 bg-zinc-50 border-t flex gap-4">
                <button 
                  onClick={() => {
                    navigator.clipboard.writeText(viewingPackage.content);
                    window.open('https://blog.naver.com/', '_blank');
                  }}
                  className="flex-1 py-4 bg-emerald-600 text-white rounded-2xl font-bold hover:bg-emerald-700 transition-all flex items-center justify-center gap-2"
                >
                  본문 복사 후 네이버 블로그로 이동
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}

function NavButton({ active, onClick, icon, label }: { active: boolean; onClick: () => void; icon: React.ReactNode; label: string }) {
  return (
    <button 
      onClick={onClick}
      className={cn(
        "group relative w-12 h-12 rounded-2xl flex items-center justify-center transition-all duration-300",
        active ? "bg-emerald-50 text-emerald-600" : "text-zinc-400 hover:bg-zinc-50 hover:text-zinc-600"
      )}
    >
      {icon}
      <span className="absolute left-16 px-2 py-1 bg-zinc-900 text-white text-[10px] font-bold rounded opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap uppercase tracking-widest">
        {label}
      </span>
      {active && (
        <motion.div 
          layoutId="nav-indicator"
          className="absolute -left-4 w-1 h-8 bg-emerald-600 rounded-r-full"
        />
      )}
    </button>
  );
}
