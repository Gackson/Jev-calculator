(() => {
  const modeNames = {enumeration: '枚举法', monte_carlo: '蒙特卡洛法', ballpoint: '圆珠笔'};
  const descriptions = {
    enumeration: '从左上到右下，用 Noul 逐格判断画黑或留白。',
    monte_carlo: '每次选择一个格子或结束；画满或连续三次选择同一点时停止。',
    ballpoint: '落笔后沿相邻八方向移动，也可抬笔重选；画满或落笔与移动次数超过格子总数时停止。'
  };
  const statuses = {ready: '准备好了，慢慢画。', continue: '正在绘画…', complete: '绘画完成',
    full: '画布已画满，已结束', repeated: '连续三次选择同一点，已结束', limit: '绘制步数超过格子总数，已结束',
    stopped: '已停止 · 已保留画布和判断', error: '请求失败 · 已保留画布和判断'};
  const actionNames = {PAINT: '画黑', SKIP: '留白', END: '结束绘画', LIFT: '结束这一笔',
    N: '↑ 上', NE: '↗ 右上', E: '→ 右', SE: '↘ 右下', S: '↓ 下', SW: '↙ 左下', W: '← 左', NW: '↖ 左上'};
  const phaseNames = {pixel: '逐格判断', place: '选择落点', move: '移动 / 抬笔'};
  let drawMode = 'enumeration', size = 8, pixels = '0'.repeat(64), marks = 0, scan = 0;
  let running = false, stopping = false, controller = null, status = 'ready', selected = null;
  let tokens = 0, elapsed = 0, errorMessage = '';
  const judgments = [], cells = [], rows = [];
  const otherBusy = () => busy || document.body.dataset.chatBusy === 'true';
  const label = (value) => actionNames[value] ? t(actionNames[value]) : `(${value})`;

  function controls() {
    document.body.dataset.drawBusy = String(running);
    updateProviderControls();
    $('draw-start').hidden = running; $('draw-start').disabled = otherBusy();
    $('draw-stop').hidden = !running; $('draw-stop').disabled = stopping;
    $('draw-prompt').readOnly = running; $('draw-size').disabled = running;
    document.querySelectorAll('[data-draw-mode]').forEach(button => {
      button.disabled = running;
      button.setAttribute('aria-pressed', String(button.dataset.drawMode === drawMode));
    });
    $('submit').disabled = running || otherBusy();
    $('chat-send').disabled = running || otherBusy();
    $('connection').disabled = running || otherBusy();
  }
  function showStatus() {
    $('draw-status').textContent = t(statuses[status]);
    $('draw-meta').textContent = `${t('{n} 次判断', {n: judgments.length})}${judgments.length ? ` · ${(elapsed / 1000).toFixed(2)} s · ${tokens} tokens` : ''}`;
    const count = pixels.split('1').length - 1;
    $('draw-progress').textContent = `${t('已画黑 {n} / {total} 格', {n: count, total: size * size})} · ${drawMode === 'enumeration' ? t('已扫描 {n} 格', {n: scan}) : t('绘制 {n} 步', {n: marks})}`;
    $('draw-canvas').setAttribute('aria-label', `${size} × ${size} · ${t('已画黑 {n} / {total} 格', {n: count, total: size * size})}`);
    $('draw-error').hidden = !errorMessage;
    $('draw-error').textContent = errorText(errorMessage);
  }
  function renderCanvas() {
    if (cells.length !== size * size) {
      cells.length = 0;
      $('draw-canvas').replaceChildren();
      $('draw-canvas').style.setProperty('--draw-size', size);
      for (let i = 0; i < size * size; i++) {
        const cell = node('span', 'draw-pixel');
        cell.setAttribute('aria-hidden', 'true'); cells.push(cell);
      }
      $('draw-canvas').append(...cells);
    }
    const target = selected === null ? null : judgments[selected]?.target;
    cells.forEach((cell, i) => {
      cell.classList.toggle('black', pixels[i] === '1');
      cell.classList.toggle('selected', target === `${i % size},${Math.floor(i / size)}`);
    });
    $('draw-canvas-size').textContent = `${size} × ${size}`;
  }
  function select(index) {
    selected = index;
    const step = judgments[index];
    rows.forEach((row, i) => { row.classList.toggle('selected', i === index); row.setAttribute('aria-pressed', String(i === index)); });
    $('draw-detail-empty').hidden = true; $('draw-detail').hidden = false;
    $('draw-position').textContent = t('第 {n} 次判断', {n: step.index});
    $('draw-choice').textContent = label(step.choice);
    $('draw-question').textContent = `${t(modeNames[drawMode])} · ${t(phaseNames[step.phase])}${step.target ? ` · (${step.target})` : ''}`;
    const noul = step.type === 'noul';
    $('draw-confidence-label').textContent = t(noul ? '所选判断概率' : '判断置信度');
    $('draw-confidence').textContent = percent(noul ? step.decision_probability : step.confidence);
    const options = noul ? [['PAINT', step.noul], ['SKIP', 1 - step.noul]] : Object.entries(step.probabilities).sort((a, b) => b[1] - a[1]);
    $('draw-candidates').replaceChildren(...options.map(([option, probability]) => {
      const row = node('div', `candidate${option === step.choice ? ' chosen' : ''}`);
      const bar = node('div', 'bar'), fill = node('div', 'fill');
      fill.style.width = `${probability * 100}%`; bar.append(fill);
      row.append(node('span', '', label(option)), bar, node('span', 'prob', percent(probability)));
      return row;
    }));
    $('draw-detail-meta').textContent = `${step.model} · ${step.latency_ms} ms · ${step.tokens} tokens`;
    $('draw-footnote').textContent = t(noul ? 'Noul 无独立置信度；概率 ≥ 50% 判为“是”。' : '置信度不等于正确率。');
    renderRequestInput('draw', step.request);
    renderCanvas();
  }
  function appendStep(step) {
    const index = judgments.length, follow = selected === null || selected === index - 1;
    judgments.push(step);
    if (index === 0) $('draw-trace').replaceChildren();
    const row = node('button', 'judgment-row draw-judgment'); row.type = 'button';
    row.setAttribute('aria-pressed', 'false');
    const description = node('span', 'step-description');
    description.append(node('strong', '', t(phaseNames[step.phase])), node('small', '', step.target ? `(${step.target})` : t(modeNames[drawMode])));
    row.append(node('span', 'step-index', String(step.index).padStart(2, '0')), description,
      node('span', 'step-answer', label(step.choice)), node('span', 'step-probability', `P ${percent(step.type === 'noul' ? step.decision_probability : step.probabilities[step.choice])}`));
    row.addEventListener('click', () => select(index));
    rows.push(row); $('draw-trace').append(row);
    $('draw-step-count').textContent = String(judgments.length).padStart(2, '0');
    if (follow) { select(index); $('draw-trace').scrollTop = $('draw-trace').scrollHeight; }
  }
  function settings() {
    $('draw-description').textContent = t(descriptions[drawMode]);
    $('draw-resolution').textContent = `${size} × ${size}`;
    $('draw-size').setAttribute('aria-valuetext', `${size} × ${size}`);
    controls();
  }
  function reset() {
    pixels = '0'.repeat(size * size); marks = 0; scan = 0; tokens = 0; elapsed = 0;
    judgments.length = 0; rows.length = 0; selected = null; status = 'ready'; errorMessage = '';
    $('draw-step-count').textContent = '00';
    $('draw-trace').replaceChildren(node('p', 'trace-empty', t('Jev的每次判断记录在这里')));
    $('draw-detail').hidden = true; $('draw-detail-empty').hidden = false; $('draw-request').open = false;
    renderCanvas(); showStatus();
  }
  $('draw-form').addEventListener('submit', async event => {
    event.preventDefault();
    if (running || otherBusy()) return;
    const prompt = $('draw-prompt').value.trim();
    if (!prompt) return;
    if (!await configReady) { errorMessage = '无法连接计算服务，请刷新页面或稍后重试。'; showStatus(); return; }
    if (running || otherBusy()) return;
    if (needsApiKey()) { openKeyDialog(); return; }
    const notes = globalNotes();
    reset(); running = true; stopping = false; status = 'continue'; controls(); showStatus();
    const started = performance.now();
    let cursor = null;
    try {
      do {
        controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 125000);
        let data;
        try {
          const response = await fetch('/api/draw', {method: 'POST', signal: controller.signal,
            headers: inferenceHeaders(),
            body: JSON.stringify({prompt, size, mode: drawMode, cursor, notes})});
          if (!(response.headers.get('content-type') || '').includes('application/json')) throw new Error('服务暂时不可用，请稍后重试。');
          data = await response.json();
          if (!response.ok) throw new Error(data.error || '请求失败');
        } finally { clearTimeout(timeout); }
        if (stopping) break;
        if (!Array.isArray(data.steps) || !data.steps.length || typeof data.pixels !== 'string' || data.pixels.length !== size * size || /[^01]/.test(data.pixels) || !Object.hasOwn(statuses, data.status) || (data.status === 'continue' && !data.cursor)) throw new Error('服务返回了无效结果。');
        pixels = data.pixels; marks = data.marks; scan = data.scan; tokens += data.tokens;
        elapsed = performance.now() - started; status = data.status; cursor = data.cursor;
        data.steps.forEach(step => appendStep({...step, tokens: data.tokens, latency_ms: data.latency_ms}));
        renderCanvas(); showStatus();
      } while (status === 'continue' && !stopping);
      if (stopping) status = 'stopped';
    } catch (error) {
      status = stopping ? 'stopped' : 'error';
      if (!stopping) errorMessage = error.name === 'AbortError' ? '本轮请求超时，请稍后重试。' : error instanceof TypeError ? '网络连接失败，请检查网络后重试。' : error.message;
    } finally {
      elapsed = performance.now() - started; running = false; controller = null; controls(); showStatus();
    }
  });
  $('draw-stop').addEventListener('click', () => { stopping = true; controller?.abort(); controls(); });
  $('draw-size').addEventListener('input', () => { if (running) return; size = Number($('draw-size').value); settings(); reset(); });
  document.querySelectorAll('[data-draw-mode]').forEach(button => button.addEventListener('click', () => {
    if (running || drawMode === button.dataset.drawMode) return;
    drawMode = button.dataset.drawMode; settings(); reset();
  }));
  document.addEventListener('jev:busy', controls);
  document.addEventListener('jev:chat-busy', controls);
  document.addEventListener('jev:language', () => {
    settings(); showStatus();
    const saved = judgments.slice(), oldSelection = selected;
    judgments.length = 0; rows.length = 0; selected = null;
    $('draw-trace').replaceChildren(node('p', 'trace-empty', t('Jev的每次判断记录在这里')));
    saved.forEach(appendStep);
    if (oldSelection !== null) select(oldSelection);
  });
  $('draw-size').value = size;
  settings(); reset();
})();
