import MiniSearch from 'minisearch';

export function removeVietnameseTones(str: string): string {
  if (!str) return '';
  return str
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/đ/g, 'd')
    .replace(/Đ/g, 'D')
    .toLowerCase();
}

export interface SearchDoc {
  id: string;
  bookSlug: string;
  docPrefix: string;
  title: string;
  page: number;
  content: string;
  normalized?: string;
}

export interface SearchResultItem {
  id: string;
  bookSlug: string;
  docPrefix: string;
  title: string;
  page: number;
  snippet: string;
  score: number;
}

let miniSearchInstance: MiniSearch<SearchDoc> | null = null;
let isLoadingIndex = false;

export async function getSearchEngine(basePath: string = ''): Promise<MiniSearch<SearchDoc>> {
  if (miniSearchInstance) return miniSearchInstance;

  isLoadingIndex = true;
  try {
    const cleanBase = basePath.replace(/\/$/, '');
    const indexUrl = `${cleanBase}/books/co-so-vat-ly-tap-1/search-index.json`;
    const res = await fetch(indexUrl);
    if (!res.ok) {
      throw new Error(`Không thể tải search-index.json: status ${res.status}`);
    }
    const docs: SearchDoc[] = await res.json();

    // Thêm trường normalized để tìm không dấu
    docs.forEach(doc => {
      doc.normalized = removeVietnameseTones(doc.content);
    });

    miniSearchInstance = new MiniSearch<SearchDoc>({
      fields: ['title', 'content', 'normalized'],
      storeFields: ['id', 'bookSlug', 'docPrefix', 'title', 'page', 'content'],
      searchOptions: {
        boost: { title: 3, content: 1.5, normalized: 1 },
        fuzzy: 0.2,
        prefix: true
      }
    });

    miniSearchInstance.addAll(docs);
    return miniSearchInstance;
  } finally {
    isLoadingIndex = false;
  }
}

export function performSearch(
  engine: MiniSearch<SearchDoc>,
  query: string,
  limit: number = 20
): SearchResultItem[] {
  if (!query || query.trim().length === 0) return [];
  const trimmed = query.trim();
  const normalizedQuery = removeVietnameseTones(trimmed);

  // Tìm kết hợp cả từ gốc và từ bỏ dấu
  const searchTerms = `${trimmed} ${normalizedQuery}`;
  const results = engine.search(searchTerms);

  return results.slice(0, limit).map(res => {
    const doc = res as any;
    const snippet = createSnippet(doc.content || '', trimmed, normalizedQuery);
    return {
      id: doc.id,
      bookSlug: doc.bookSlug,
      docPrefix: doc.docPrefix,
      title: doc.title,
      page: doc.page,
      snippet,
      score: res.score
    };
  });
}

function createSnippet(text: string, query: string, normalizedQuery: string, maxLen: number = 180): string {
  if (!text) return '';
  const normText = removeVietnameseTones(text);
  const qWords = normalizedQuery.split(/\s+/).filter(w => w.length > 2);
  
  let matchIndex = -1;
  // Tìm vị trí xuất hiện đầu tiên của từ khoá
  if (qWords.length > 0) {
    matchIndex = normText.indexOf(qWords[0]);
  }
  if (matchIndex === -1) {
    matchIndex = normText.indexOf(normalizedQuery);
  }

  let start = 0;
  if (matchIndex > 60) {
    start = matchIndex - 50;
  }
  let end = Math.min(text.length, start + maxLen);
  let snippet = text.slice(start, end);

  if (start > 0) snippet = '...' + snippet;
  if (end < text.length) snippet = snippet + '...';

  return snippet;
}
