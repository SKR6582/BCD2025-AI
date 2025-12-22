// 리더보드 자동 갱신 스크립트 (10초 간격)
// 템플릿의 인라인 폴백과 중복 실행을 방지하기 위한 플래그
window.__leaderboardLoaded = true;
(function () {
  const api = '/api/leaderboard';
  const $err = document.getElementById('error');

  // ---- Auto Scroll Manager ----
  const SCROLL_PX_PER_SEC = 40; // px/s
  const BOTTOM_PAUSE_MS = 1200;
  const TOP_PAUSE_MS = 400;
  const stateMap = new WeakMap();
  let allContainers = [];

  function ensureState(el) {
    let st = stateMap.get(el);
    if (!st) {
      st = { raf: 0, paused: false, lastTs: 0, phase: 'run', pendingTimer: 0 };
      stateMap.set(el, st);
      el.addEventListener('mouseenter', () => pause(el, true));
      el.addEventListener('mouseleave', () => pause(el, false));
      el.addEventListener('focusin', () => pause(el, true));
      el.addEventListener('focusout', () => pause(el, false));
    }
    return st;
  }

  function pause(el, v) {
    const st = ensureState(el);
    st.paused = v;
    if (v && st.raf) { cancelAnimationFrame(st.raf); st.raf = 0; }
    if (!v && !st.raf) { st.lastTs = 0; st.raf = requestAnimationFrame(ts => tick(el, ts)); }
  }

  function stop(el) {
    const st = ensureState(el);
    if (st.raf) { cancelAnimationFrame(st.raf); st.raf = 0; }
    if (st.pendingTimer) { clearTimeout(st.pendingTimer); st.pendingTimer = 0; }
    st.lastTs = 0; st.phase = 'run';
  }

  function start(el) {
    stop(el);
    // 시작 시 상단으로
    el.scrollTop = 0;
    const st = ensureState(el);
    st.raf = requestAnimationFrame(ts => tick(el, ts));
  }

  function tick(el, ts) {
    const st = ensureState(el);
    if (st.paused) { st.raf = 0; return; }

    if (!st.lastTs) st.lastTs = ts;
    const dt = Math.min(100, ts - st.lastTs); // clamp to avoid jumps
    st.lastTs = ts;

    const maxScroll = el.scrollHeight - el.clientHeight;
    if (maxScroll <= 0) { st.raf = 0; return; }

    if (st.phase === 'run') {
      el.scrollTop = Math.min(maxScroll, el.scrollTop + (SCROLL_PX_PER_SEC * (dt / 1000)));
      if (el.scrollTop >= maxScroll - 1) {
        st.phase = 'bottom-pause';
        st.pendingTimer = setTimeout(() => {
          st.pendingTimer = 0;
          el.scrollTop = 0; // jump to top; could animate if desired
          st.phase = 'top-pause';
          st.pendingTimer = setTimeout(() => { st.pendingTimer = 0; st.phase = 'run'; st.raf = requestAnimationFrame(ts2 => tick(el, ts2)); }, TOP_PAUSE_MS);
        }, BOTTOM_PAUSE_MS);
        st.raf = 0;
        return;
      }
    }

    st.raf = requestAnimationFrame(ts2 => tick(el, ts2));
  }

  function refreshAllAutoScroll() {
    allContainers = Array.from(document.querySelectorAll('.table-scroll'));
    allContainers.forEach(el => {
      stop(el);
      if (el.scrollHeight > el.clientHeight) {
        start(el);
      } else {
        el.scrollTop = 0; // ensure reset when not scrollable
      }
    });
  }

  document.addEventListener('visibilitychange', () => {
    allContainers.forEach(el => pause(el, document.hidden));
  });

  // 노출: 다른 스크립트(인라인 폴백)도 사용할 수 있게
  window.__autoScrollMgr = {
    refreshAll: refreshAllAutoScroll,
    stopAll: () => allContainers.forEach(stop)
  };

  // ---- Rendering & Refresh ----
  function renderSection(tbodyId, data) {
    const $tbody = document.getElementById(tbodyId);
    $tbody.innerHTML = '';
    data.forEach((row, idx) => {
      const tr = document.createElement('tr');
      tr.innerHTML = `<td>${idx + 1}</td><td>${row.class_id ?? ''}</td><td>${row.score ?? ''}</td>`;
      $tbody.appendChild(tr);
    });
  }

  async function refresh() {
    try {
      if ($err) $err.style.display = 'none';
      const res = await fetch(api, { cache: 'no-store' });
      if (!res.ok) throw new Error('HTTP ' + res.status);
      const json = await res.json();
      if (json.error) throw new Error(json.error);
      renderSection('tbody-easy', json.easy || []);
      renderSection('tbody-normal', json.normal || []);
      renderSection('tbody-hard', json.hard || []);
      // 데이터가 갱신된 뒤 자동 스크롤 초기화
      if (window.__autoScrollMgr) window.__autoScrollMgr.refreshAll();
    } catch (e) {
      if ($err) {
        $err.textContent = '리더보드를 불러오지 못했습니다: ' + (e && e.message ? e.message : e);
        $err.style.display = 'block';
      }
      console.error(e);
      if (window.__autoScrollMgr) window.__autoScrollMgr.stopAll();
    }
  }

  refresh();
  setInterval(refresh, 10000);
})();
