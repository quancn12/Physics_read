/**
 * Quản lý Trạng thái Cá nhân hóa của Cuna (LocalStorage với try/catch an toàn)
 * Hỗ trợ lưu vị trí đọc, tiến độ từng chương, ghim sidebar, mức thu phóng,
 * export/import dữ liệu chuyển máy, và chế độ sáng/tối.
 */

export interface ReadingPosition {
  bookSlug: string;
  chapterSlug: string;
  chapterNumber?: number;
  chapterTitle?: string;
  page: number;
  scrollPercent?: number;
  timestamp: number;
}

export interface ChapterProgress {
  readPages: number[];
  totalPages: number;
  isCompleted: boolean;
  lastPage: number;
  updatedAt: number;
}

export interface SidebarConfig {
  tocPinned: boolean;
  answersPinned: boolean;
  answersWidth: number; // in px, default 480
}

export interface UserPreferences {
  theme: 'light' | 'dark';
  chapterZoom: number; // default 1.0
  answersZoom: number; // default 1.0
}

const STORAGE_KEYS = {
  LAST_READ: 'cuna_last_read_v1',
  READING_HISTORY: 'cuna_reading_history_v1',
  PROGRESS_PREFIX: 'cuna_prog_',
  SIDEBAR_CONFIG: 'cuna_sidebar_config_v1',
  PREFERENCES: 'cuna_preferences_v1'
};

function safeGetItem(key: string): string | null {
  try {
    if (typeof window !== 'undefined' && window.localStorage) {
      return window.localStorage.getItem(key);
    }
  } catch (e) {
    console.warn(`[Cuna Storage] Không thể đọc key "${key}":`, e);
  }
  return null;
}

function safeSetItem(key: string, value: string): boolean {
  try {
    if (typeof window !== 'undefined' && window.localStorage) {
      window.localStorage.setItem(key, value);
      return true;
    }
  } catch (e) {
    console.warn(`[Cuna Storage] Không thể ghi key "${key}":`, e);
  }
  return false;
}

// 1. Vị trí đọc gần nhất toàn site
export function getLastRead(): ReadingPosition | null {
  const raw = safeGetItem(STORAGE_KEYS.LAST_READ);
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export function setLastRead(pos: Omit<ReadingPosition, 'timestamp'>): void {
  const full: ReadingPosition = {
    ...pos,
    timestamp: Date.now()
  };
  safeSetItem(STORAGE_KEYS.LAST_READ, JSON.stringify(full));
}

// 2. Tiến độ theo từng chương
export function getChapterProgress(bookSlug: string, chapterSlug: string): ChapterProgress | null {
  const key = `${STORAGE_KEYS.PROGRESS_PREFIX}${bookSlug}_${chapterSlug}`;
  const raw = safeGetItem(key);
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export function saveChapterProgress(
  bookSlug: string,
  chapterSlug: string,
  page: number,
  totalPages: number
): void {
  const current = getChapterProgress(bookSlug, chapterSlug) || {
    readPages: [],
    totalPages,
    isCompleted: false,
    lastPage: 1,
    updatedAt: Date.now()
  };

  const setPages = new Set(current.readPages);
  setPages.add(page);
  const readPages = Array.from(setPages).sort((a, b) => a - b);
  const isCompleted = readPages.length >= totalPages || current.isCompleted;

  const updated: ChapterProgress = {
    readPages,
    totalPages,
    isCompleted,
    lastPage: page,
    updatedAt: Date.now()
  };

  const key = `${STORAGE_KEYS.PROGRESS_PREFIX}${bookSlug}_${chapterSlug}`;
  safeSetItem(key, JSON.stringify(updated));
}

export function toggleChapterCompleted(bookSlug: string, chapterSlug: string, totalPages: number): boolean {
  const current = getChapterProgress(bookSlug, chapterSlug);
  const newState = !current?.isCompleted;
  
  const updated: ChapterProgress = {
    readPages: current?.readPages || [],
    totalPages,
    isCompleted: newState,
    lastPage: current?.lastPage || 1,
    updatedAt: Date.now()
  };

  const key = `${STORAGE_KEYS.PROGRESS_PREFIX}${bookSlug}_${chapterSlug}`;
  safeSetItem(key, JSON.stringify(updated));
  return newState;
}

// 3. Cấu hình Sidebars
export function getSidebarConfig(): SidebarConfig {
  const raw = safeGetItem(STORAGE_KEYS.SIDEBAR_CONFIG);
  if (raw) {
    try {
      return JSON.parse(raw);
    } catch {}
  }
  return {
    tocPinned: true,
    answersPinned: true,
    answersWidth: 480
  };
}

export function setSidebarConfig(cfg: Partial<SidebarConfig>): void {
  const current = getSidebarConfig();
  safeSetItem(STORAGE_KEYS.SIDEBAR_CONFIG, JSON.stringify({ ...current, ...cfg }));
}

// 4. Tuỳ chọn Giao diện (Theme, Zoom)
export function getPreferences(): UserPreferences {
  const raw = safeGetItem(STORAGE_KEYS.PREFERENCES);
  if (raw) {
    try {
      return JSON.parse(raw);
    } catch {}
  }
  return {
    theme: 'light',
    chapterZoom: 1.0,
    answersZoom: 1.0
  };
}

export function setPreferences(prefs: Partial<UserPreferences>): void {
  const current = getPreferences();
  safeSetItem(STORAGE_KEYS.PREFERENCES, JSON.stringify({ ...current, ...prefs }));
}

// 5. Export / Import Dữ liệu Toàn site
export function exportCunaData(): string {
  const data: Record<string, any> = {};
  try {
    for (let i = 0; i < localStorage.length; i++) {
      const k = localStorage.key(i);
      if (k && k.startsWith('cuna_')) {
        data[k] = localStorage.getItem(k);
      }
    }
  } catch (e) {
    console.error('[Cuna Export] Lỗi đọc:', e);
  }
  return JSON.stringify({
    app: 'Cuna Physics Read',
    exportedAt: new Date().toISOString(),
    version: '1.0',
    data
  }, null, 2);
}

export function importCunaData(jsonStr: string): boolean {
  try {
    const parsed = JSON.parse(jsonStr);
    if (!parsed || !parsed.data) return false;
    for (const [k, v] of Object.entries(parsed.data)) {
      if (typeof v === 'string') {
        localStorage.setItem(k, v);
      }
    }
    return true;
  } catch (e) {
    console.error('[Cuna Import] Lỗi import:', e);
    return false;
  }
}

export function resetAllCunaData(): void {
  try {
    const toRemove: string[] = [];
    for (let i = 0; i < localStorage.length; i++) {
      const k = localStorage.key(i);
      if (k && k.startsWith('cuna_')) {
        toRemove.push(k);
      }
    }
    toRemove.forEach(k => localStorage.removeItem(k));
  } catch (e) {
    console.error('[Cuna Reset] Lỗi xoá:', e);
  }
}
