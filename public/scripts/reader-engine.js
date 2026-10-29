/**
 * CUNA PHYSICS — ADVANCED VIRTUALIZED PDF.JS READER ENGINE
 * - Virtualized canvas rendering (chỉ render trang gần viewport, giải phóng canvas ở xa)
 * - Render sắc nét theo window.devicePixelRatio
 * - Đồng bộ Scroll Spy ➔ Cập nhật URL ?page=N và highlight Mục lục
 * - Lưu tiến độ đọc vào localStorage với try/catch
 * - Render đồng thời file đáp án (dap-an.pdf) cuộn độc lập, tự động nhảy trang đáp án
 * - Kéo thay đổi độ rộng sidebar đáp án, ghim / bỏ ghim, phím tắt [, ], /, +, -
 */

async function initReader() {
  const config = window.CUNA_READER_CONFIG;
  if (!config) return;

  const baseUrl = config.baseUrl.replace(/\/$/, '');

  // 1. Nhập PDF.js từ vendor static
  let pdfjsLib;
  try {
    pdfjsLib = await import(`${baseUrl}/vendor/pdfjs/pdf.min.mjs`);
    pdfjsLib.GlobalWorkerOptions.workerSrc = `${baseUrl}/vendor/pdfjs/pdf.worker.min.mjs`;
  } catch (err) {
    console.error('Không thể tải PDF.js:', err);
    return;
  }

  // 2. Tham chiếu DOM
  const scrollContainer = document.getElementById('pdf-scroll-container');
  const pagesStack = document.getElementById('pdf-pages-stack');
  const initialLoading = document.getElementById('pdf-initial-loading');
  const pageInput = document.getElementById('page-num-input');
  const mobilePageText = document.getElementById('mobile-page-text');

  const tocSidebar = document.getElementById('toc-sidebar');
  const answersSidebar = document.getElementById('answers-sidebar');
  const resizerHandle = document.getElementById('resizer-handle');

  const toggleTocBtn = document.getElementById('toggle-toc-btn');
  const toggleAnsBtn = document.getElementById('toggle-answers-btn');
  const pinTocBtn = document.getElementById('pin-toc-btn');
  const pinAnsBtn = document.getElementById('pin-answers-btn');
  const closeTocBtn = document.getElementById('close-toc-btn');
  const closeAnsBtn = document.getElementById('close-answers-btn');

  const zoomInBtn = document.getElementById('zoom-in-btn');
  const zoomOutBtn = document.getElementById('zoom-out-btn');
  const zoomFitBtn = document.getElementById('zoom-fit-btn');

  const answersContainer = document.getElementById('answers-pdf-container');
  const answersSelect = document.getElementById('answers-chapter-jump');
  const ansZoomIn = document.getElementById('ans-zoom-in');
  const ansZoomOut = document.getElementById('ans-zoom-out');

  const mobileTocBtn = document.getElementById('mobile-toc-btn');
  const mobileAnsBtn = document.getElementById('mobile-answers-btn');

  // Trạng thái cục bộ
  let currentZoomScale = 1.0;
  let isFitWidth = true;
  let answersZoomScale = 0.9;
  let pdfDoc = null;
  let answersDoc = null;

  const renderedPages = new Map(); // pageNum -> { canvas, renderTask }
  const pageViewports = new Map();

  // Đọc cấu hình từ localStorage
  function loadPersistedState() {
    try {
      const rawCfg = localStorage.getItem('cuna_sidebar_config_v1');
      if (rawCfg) {
        const cfg = JSON.parse(rawCfg);
        if (!cfg.tocPinned && tocSidebar) {
          tocSidebar.classList.remove('pinned');
          tocSidebar.classList.add('collapsed');
          if (pinTocBtn) pinTocBtn.classList.remove('active');
          if (toggleTocBtn) toggleTocBtn.classList.remove('active-pill');
        }
        if (!cfg.answersPinned && answersSidebar) {
          answersSidebar.classList.remove('pinned');
          answersSidebar.classList.add('collapsed');
          if (pinAnsBtn) pinAnsBtn.classList.remove('active');
          if (toggleAnsBtn) toggleAnsBtn.classList.remove('active-pill');
        }
        if (cfg.answersWidth && answersSidebar && window.innerWidth > 900) {
          answersSidebar.style.width = `${cfg.answersWidth}px`;
        }
      }

      const rawPrefs = localStorage.getItem('cuna_preferences_v1');
      if (rawPrefs) {
        const prefs = JSON.parse(rawPrefs);
        if (prefs.chapterZoom && prefs.chapterZoom !== 1.0) {
          currentZoomScale = prefs.chapterZoom;
          isFitWidth = false;
        }
      }
    } catch (e) {}
  }
  loadPersistedState();

  // 3. Tải PDF Chương hiện tại
  try {
    pdfDoc = await pdfjsLib.getDocument({
      url: config.pdfUrl,
      cMapUrl: `${baseUrl}/vendor/pdfjs/cmaps/`,
      cMapPacked: true
    }).promise;

    if (initialLoading) initialLoading.style.display = 'none';
  } catch (err) {
    console.error('Lỗi tải chương PDF:', err);
    if (initialLoading) {
      initialLoading.innerHTML = `
        <p style="color: #EF4444; font-weight: bold;">Không thể tải tệp PDF.</p>
        <p style="font-size: 0.85rem; color: #64748B;">Vui lòng kiểm tra lại đường dẫn: ${config.pdfUrl}</p>
      `;
    }
    return;
  }

  // Khởi tạo các khung trang rỗng (placeholders)
  const numPages = pdfDoc.numPages;
  const firstPage = await pdfDoc.getPage(1);
  const baseVp = firstPage.getViewport({ scale: 1.0 });
  const aspectRatio = baseVp.height / baseVp.width;

  function calculateTargetWidth() {
    if (!isFitWidth) {
      return baseVp.width * currentZoomScale;
    }
    const containerWidth = scrollContainer.clientWidth - 48; // padding
    return Math.min(1000, Math.max(340, containerWidth));
  }

  let currentWidth = calculateTargetWidth();
  let currentHeight = currentWidth * aspectRatio;

  for (let i = 1; i <= numPages; i++) {
    const wrapper = document.createElement('div');
    wrapper.className = 'pdf-page-wrapper';
    wrapper.id = `page-wrapper-${i}`;
    wrapper.dataset.page = String(i);
    wrapper.style.width = `${currentWidth}px`;
    wrapper.style.height = `${currentHeight}px`;

    // Nhãn số trang mờ ở góc
    const pgLabel = document.createElement('div');
    pgLabel.style.position = 'absolute';
    pgLabel.style.top = '10px';
    pgLabel.style.right = '10px';
    pgLabel.style.fontSize = '11px';
    pgLabel.style.color = '#94A3B8';
    pgLabel.style.fontWeight = '700';
    pgLabel.textContent = `Trang ${i}`;
    wrapper.appendChild(pgLabel);

    pagesStack.appendChild(wrapper);
  }

  // 4. Render Trang PDF bằng Canvas
  async function renderPage(pageNum) {
    if (renderedPages.has(pageNum)) return;
    const wrapper = document.getElementById(`page-wrapper-${pageNum}`);
    if (!wrapper) return;

    try {
      const page = await pdfDoc.getPage(pageNum);
      const width = wrapper.clientWidth || currentWidth;
      const scale = width / baseVp.width;
      const dpr = window.devicePixelRatio || 1.5;

      const viewport = page.getViewport({ scale: scale * dpr });
      pageViewports.set(pageNum, viewport);

      const canvas = document.createElement('canvas');
      canvas.className = 'pdf-page-canvas';
      canvas.width = viewport.width;
      canvas.height = viewport.height;
      canvas.style.width = `${width}px`;
      canvas.style.height = `${width * aspectRatio}px`;

      wrapper.innerHTML = '';
      wrapper.appendChild(canvas);

      const ctx = canvas.getContext('2d', { alpha: false });
      const renderTask = page.render({
        canvasContext: ctx,
        viewport: viewport
      });

      renderedPages.set(pageNum, { canvas, renderTask });
      await renderTask.promise;
    } catch (e) {
      if (e?.name !== 'RenderingCancelledException') {
        console.warn(`Lỗi render trang ${pageNum}:`, e);
      }
    }
  }

  function destroyPage(pageNum) {
    const info = renderedPages.get(pageNum);
    if (info) {
      try {
        info.renderTask.cancel();
      } catch (e) {}
      renderedPages.delete(pageNum);
      const wrapper = document.getElementById(`page-wrapper-${pageNum}`);
      if (wrapper) {
        wrapper.innerHTML = `
          <div style="position:absolute; top:10px; right:10px; font-size:11px; color:#94A3B8; font-weight:700;">
            Trang ${pageNum}
          </div>
        `;
      }
    }
  }

  // 5. Virtualization với IntersectionObserver
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      const pageNum = parseInt(entry.target.dataset.page || '1', 10);
      if (entry.isIntersecting) {
        renderPage(pageNum);
        // Pre-render các trang liền kề
        if (pageNum > 1) renderPage(pageNum - 1);
        if (pageNum < numPages) renderPage(pageNum + 1);
      } else {
        // Chỉ huỷ nếu cách xa hơn 3 trang để cuộn mượt
        const curPage = getCurrentVisiblePage();
        if (Math.abs(pageNum - curPage) > 3) {
          destroyPage(pageNum);
        }
      }
    });
  }, {
    root: scrollContainer,
    rootMargin: '400px 0px 400px 0px',
    threshold: 0.01
  });

  document.querySelectorAll('.pdf-page-wrapper').forEach((el) => observer.observe(el));

  // 6. Scroll Spy: Xác định trang hiện tại & Cập nhật URL, Mục lục, LocalStorage
  let lastRecordedPage = 1;

  function getCurrentVisiblePage() {
    const wrappers = document.querySelectorAll('.pdf-page-wrapper');
    const containerTop = scrollContainer.scrollTop;
    const containerCenter = containerTop + scrollContainer.clientHeight / 3;

    for (const w of wrappers) {
      const top = (w as HTMLElement).offsetTop;
      const height = (w as HTMLElement).offsetHeight;
      if (containerCenter >= top && containerCenter <= top + height) {
        return parseInt(w.dataset.page || '1', 10);
      }
    }
    return 1;
  }

  function highlightTocSection(page) {
    const secAnchors = document.querySelectorAll('.toc-sec-anchor, .toc-subsec-anchor');
    let activeAnchor = null;

    secAnchors.forEach((a) => {
      const p = parseInt(a.getAttribute('data-page') || '1', 10);
      if (p <= page) {
        activeAnchor = a;
      }
      a.classList.remove('active');
    });

    if (activeAnchor) {
      activeAnchor.classList.add('active');
      activeAnchor.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
    }
  }

  function saveProgress(page) {
    try {
      // 1. Lưu vị trí gần nhất
      const lastReadData = {
        bookSlug: config.bookSlug,
        chapterSlug: config.chapterSlug,
        page: page,
        timestamp: Date.now()
      };
      localStorage.setItem('cuna_last_read_v1', JSON.stringify(lastReadData));

      // 2. Lưu tiến độ chương
      const progKey = `cuna_prog_${config.bookSlug}_${config.chapterSlug}`;
      const curProg = JSON.parse(localStorage.getItem(progKey) || '{"readPages":[]}');
      const setPages = new Set(curProg.readPages || []);
      setPages.add(page);
      curProg.readPages = Array.from(setPages);
      curProg.totalPages = config.pageCount;
      curProg.lastPage = page;
      curProg.isCompleted = curProg.readPages.length >= config.pageCount;
      curProg.updatedAt = Date.now();
      localStorage.setItem(progKey, JSON.stringify(curProg));
    } catch (e) {}
  }

  scrollContainer.addEventListener('scroll', () => {
    const curPage = getCurrentVisiblePage();
    if (curPage !== lastRecordedPage) {
      lastRecordedPage = curPage;

      // Cập nhật input trang
      if (pageInput) pageInput.value = String(curPage);
      if (mobilePageText) mobilePageText.textContent = `${curPage} / ${config.pageCount}`;

      // Cập nhật URL ?page=N mà không reload
      const url = new URL(window.location.href);
      url.searchParams.set('page', String(curPage));
      window.history.replaceState(null, '', url.toString());

      // Highlight Mục lục
      highlightTocSection(curPage);

      // Lưu LocalStorage
      saveProgress(curPage);
    }
  }, { passive: true });

  // Nhảy trang khi người dùng nhập số trang
  pageInput?.addEventListener('change', () => {
    const p = Math.max(1, Math.min(numPages, parseInt(pageInput.value || '1', 10)));
    scrollToPage(p);
  });

  function scrollToPage(pageNum) {
    const target = document.getElementById(`page-wrapper-${pageNum}`);
    if (target) {
      target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }

  // Nhảy tới trang ban đầu nếu có URL ?page=N
  const initialUrlPage = parseInt(new URLSearchParams(window.location.search).get('page') || '1', 10);
  if (initialUrlPage > 1 && initialUrlPage <= numPages) {
    setTimeout(() => scrollToPage(initialUrlPage), 200);
  }

  // 7. Thu phóng (Zoom)
  function applyZoom(newScale, fit = false) {
    isFitWidth = fit;
    currentZoomScale = newScale;
    currentWidth = calculateTargetWidth();
    currentHeight = currentWidth * aspectRatio;

    document.querySelectorAll('.pdf-page-wrapper').forEach((w) => {
      (w as HTMLElement).style.width = `${currentWidth}px`;
      (w as HTMLElement).style.height = `${currentHeight}px`;
    });

    // Xoá cache để render lại theo kích thước mới
    renderedPages.forEach((val, pageNum) => destroyPage(pageNum));
    const curPage = getCurrentVisiblePage();
    renderPage(curPage);
    if (curPage > 1) renderPage(curPage - 1);
    if (curPage < numPages) renderPage(curPage + 1);

    if (zoomFitBtn) {
      zoomFitBtn.textContent = fit ? 'Fit' : `${Math.round(currentZoomScale * 100)}%`;
    }

    try {
      const prefs = JSON.parse(localStorage.getItem('cuna_preferences_v1') || '{}');
      prefs.chapterZoom = currentZoomScale;
      localStorage.setItem('cuna_preferences_v1', JSON.stringify(prefs));
    } catch (e) {}
  }

  zoomInBtn?.addEventListener('click', () => applyZoom(Math.min(2.5, currentZoomScale + 0.15), false));
  zoomOutBtn?.addEventListener('click', () => applyZoom(Math.max(0.6, currentZoomScale - 0.15), false));
  zoomFitBtn?.addEventListener('click', () => applyZoom(1.0, true));

  // 8. Tải và Render File Đáp Án (dap-an.pdf)
  async function initAnswersViewer() {
    if (!answersContainer) return;
    try {
      answersDoc = await pdfjsLib.getDocument({
        url: config.answersPdfUrl,
        cMapUrl: `${baseUrl}/vendor/pdfjs/cmaps/`,
        cMapPacked: true
      }).promise;

      const totalAnsPages = answersDoc.numPages;
      answersContainer.innerHTML = '';

      for (let i = 1; i <= totalAnsPages; i++) {
        const wrap = document.createElement('div');
        wrap.id = `ans-page-wrapper-${i}`;
        wrap.style.width = '100%';
        wrap.style.maxWidth = '600px';
        wrap.style.boxShadow = '0 2px 8px rgba(0,0,0,0.15)';
        wrap.style.background = '#FFFFFF';
        wrap.style.marginBottom = '12px';
        answersContainer.appendChild(wrap);

        renderAnswerPage(i);
      }

      // Tự động nhảy đến trang đáp án của chương hiện tại
      jumpToAnswerPage(config.answersInitialPage);
    } catch (e) {
      console.warn('Lỗi tải file đáp án:', e);
      if (answersContainer) {
        answersContainer.innerHTML = '<p style="color:#EF4444; padding:1rem;">Không thể mở file đáp án.</p>';
      }
    }
  }

  async function renderAnswerPage(pageNum) {
    if (!answersDoc) return;
    const wrap = document.getElementById(`ans-page-wrapper-${pageNum}`);
    if (!wrap) return;

    try {
      const page = await answersDoc.getPage(pageNum);
      const vp = page.getViewport({ scale: answersZoomScale * 1.4 });
      const canvas = document.createElement('canvas');
      canvas.width = vp.width;
      canvas.height = vp.height;
      canvas.style.width = '100%';
      canvas.style.display = 'block';

      wrap.innerHTML = '';
      wrap.appendChild(canvas);

      const ctx = canvas.getContext('2d');
      await page.render({ canvasContext: ctx, viewport: vp }).promise;
    } catch (e) {}
  }

  function jumpToAnswerPage(pageNum) {
    const wrap = document.getElementById(`ans-page-wrapper-${pageNum}`);
    if (wrap && answersContainer) {
      wrap.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }

  answersSelect?.addEventListener('change', (e) => {
    const p = parseInt((e.target as HTMLSelectElement).value, 10);
    jumpToAnswerPage(p);
  });

  ansZoomIn?.addEventListener('click', () => {
    answersZoomScale = Math.min(1.8, answersZoomScale + 0.15);
    for (let i = 1; i <= (answersDoc?.numPages || 11); i++) renderAnswerPage(i);
  });
  ansZoomOut?.addEventListener('click', () => {
    answersZoomScale = Math.max(0.6, answersZoomScale - 0.15);
    for (let i = 1; i <= (answersDoc?.numPages || 11); i++) renderAnswerPage(i);
  });

  initAnswersViewer();

  // 9. Bật/Tắt & Ghim Sidebars
  function toggleSidebar(sidebar, btn, pinBtn, storageKey) {
    if (!sidebar) return;
    const isCollapsed = sidebar.classList.contains('collapsed');
    if (isCollapsed) {
      sidebar.classList.remove('collapsed');
      btn?.classList.add('active-pill');
    } else {
      sidebar.classList.add('collapsed');
      btn?.classList.remove('active-pill');
    }
    // Cập nhật lại chiều rộng middle viewer
    setTimeout(() => {
      if (isFitWidth) applyZoom(1.0, true);
    }, 220);
  }

  function togglePin(sidebar, pinBtn, storageKey) {
    if (!sidebar || !pinBtn) return;
    const isPinned = sidebar.classList.contains('pinned');
    if (isPinned) {
      sidebar.classList.remove('pinned');
      sidebar.classList.add('unpinned-floating');
      pinBtn.classList.remove('active');
    } else {
      sidebar.classList.remove('unpinned-floating');
      sidebar.classList.add('pinned');
      pinBtn.classList.add('active');
    }
    try {
      const cfg = JSON.parse(localStorage.getItem('cuna_sidebar_config_v1') || '{}');
      cfg[storageKey] = !isPinned;
      localStorage.setItem('cuna_sidebar_config_v1', JSON.stringify(cfg));
    } catch (e) {}
  }

  toggleTocBtn?.addEventListener('click', () => toggleSidebar(tocSidebar, toggleTocBtn, pinTocBtn, 'tocPinned'));
  closeTocBtn?.addEventListener('click', () => toggleSidebar(tocSidebar, toggleTocBtn, pinTocBtn, 'tocPinned'));
  pinTocBtn?.addEventListener('click', () => togglePin(tocSidebar, pinTocBtn, 'tocPinned'));

  toggleAnsBtn?.addEventListener('click', () => toggleSidebar(answersSidebar, toggleAnsBtn, pinAnsBtn, 'answersPinned'));
  closeAnsBtn?.addEventListener('click', () => toggleSidebar(answersSidebar, toggleAnsBtn, pinAnsBtn, 'answersPinned'));
  pinAnsBtn?.addEventListener('click', () => togglePin(answersSidebar, pinAnsBtn, 'answersPinned'));

  // Mobile drawer triggers
  mobileTocBtn?.addEventListener('click', () => {
    tocSidebar?.classList.toggle('collapsed');
  });
  mobileAnsBtn?.addEventListener('click', () => {
    answersSidebar?.classList.toggle('collapsed');
  });

  // 10. Resizer Handle cho Sidebar Đáp án
  let isDragging = false;
  let startX = 0;
  let startWidth = 480;

  resizerHandle?.addEventListener('mousedown', (e) => {
    isDragging = true;
    startX = e.clientX;
    startWidth = answersSidebar?.offsetWidth || 480;
    resizerHandle.classList.add('dragging');
    document.body.style.userSelect = 'none';
    document.body.style.cursor = 'col-resize';
  });

  window.addEventListener('mousemove', (e) => {
    if (!isDragging || !answersSidebar) return;
    const diff = startX - e.clientX;
    const newWidth = Math.max(320, Math.min(window.innerWidth * 0.6, startWidth + diff));
    answersSidebar.style.width = `${newWidth}px`;
  });

  window.addEventListener('mouseup', () => {
    if (isDragging) {
      isDragging = false;
      resizerHandle?.classList.remove('dragging');
      document.body.style.userSelect = '';
      document.body.style.cursor = '';
      if (answersSidebar) {
        try {
          const cfg = JSON.parse(localStorage.getItem('cuna_sidebar_config_v1') || '{}');
          cfg.answersWidth = answersSidebar.offsetWidth;
          localStorage.setItem('cuna_sidebar_config_v1', JSON.stringify(cfg));
        } catch (e) {}
      }
      if (isFitWidth) applyZoom(1.0, true);
    }
  });

  // 11. Bàn phím tắt Desktop: [, ], /, +, -
  window.addEventListener('keydown', (e) => {
    if (document.activeElement?.tagName === 'INPUT' || document.activeElement?.tagName === 'TEXTAREA') {
      return;
    }
    if (e.key === '[') {
      e.preventDefault();
      toggleSidebar(tocSidebar, toggleTocBtn, pinTocBtn, 'tocPinned');
    } else if (e.key === ']') {
      e.preventDefault();
      toggleSidebar(answersSidebar, toggleAnsBtn, pinAnsBtn, 'answersPinned');
    } else if (e.key === '=' || e.key === '+') {
      e.preventDefault();
      applyZoom(Math.min(2.5, currentZoomScale + 0.15), false);
    } else if (e.key === '-') {
      e.preventDefault();
      applyZoom(Math.max(0.6, currentZoomScale - 0.15), false);
    }
  });

  // Window resize ➔ tự động tính lại fit-width
  window.addEventListener('resize', () => {
    if (isFitWidth) {
      applyZoom(1.0, true);
    }
  });

  // Click vào mục trong TOC để cuộn tới trang tương ứng
  document.querySelectorAll('.toc-sec-anchor, .toc-subsec-anchor').forEach((a) => {
    a.addEventListener('click', (e) => {
      e.preventDefault();
      const p = parseInt(a.getAttribute('data-page') || '1', 10);
      scrollToPage(p);
      if (window.innerWidth <= 768) {
        tocSidebar?.classList.add('collapsed');
      }
    });
  });
}

// Chạy reader khi DOM sẵn sàng
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initReader);
} else {
  initReader();
}
