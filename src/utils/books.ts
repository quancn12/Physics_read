import fs from 'node:fs';
import path from 'node:path';

export interface Subsection {
  title: string;
  orig_page?: number;
  pdf_page: number;
  uncertain?: boolean;
}

export interface Section {
  code: string;
  title: string;
  orig_page?: number;
  type?: string;
  pdf_page: number;
  subsections?: Subsection[];
}

export interface ChapterMeta {
  number: number;
  slug: string;
  title: string;
  titleEn: string;
  fileName: string;
  pageCount: number;
  sizeBytes: number;
  answersPage: number;
  sections: Section[];
}

export interface AppendixItem {
  code: string;
  title: string;
  page: number;
}

export interface BookMetadata {
  slug: string;
  title: string;
  subtitle: string;
  description: string;
  totalPages: number;
  totalChapters: number;
  chapters: ChapterMeta[];
  answers: {
    fileName: string;
    totalPages: number;
    mapping: Record<string, number>;
  };
  appendix: {
    fileName: string;
    totalPages: number;
    items: AppendixItem[];
  };
  tableOfContents: {
    fileName: string;
    totalPages: number;
  };
}

export function getBookMetadata(slug: string = 'co-so-vat-ly-tap-1'): BookMetadata {
  const metaPath = path.resolve(process.cwd(), 'public', 'books', slug, 'metadata.json');
  if (!fs.existsSync(metaPath)) {
    throw new Error(`Metadata file not found: ${metaPath}`);
  }
  const raw = fs.readFileSync(metaPath, 'utf-8');
  return JSON.parse(raw);
}

export function getAllBooks(): { slug: string; title: string; subtitle: string; totalChapters: number; totalPages: number }[] {
  // Sẵn sàng hỗ trợ nhiều cuốn sách sau này
  const book = getBookMetadata('co-so-vat-ly-tap-1');
  return [
    {
      slug: book.slug,
      title: book.title,
      subtitle: book.subtitle,
      totalChapters: book.totalChapters,
      totalPages: book.totalPages
    }
  ];
}
