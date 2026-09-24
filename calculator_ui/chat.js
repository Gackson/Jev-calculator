(() => {
  let running = false, stopping = false, controller = null, selection = null;
  const turns = [];
  const tabs = [...document.querySelectorAll('[data-page]')];
  function switchPage(page) {
    tabs.forEach((tab) => {
      const active = tab.dataset.page === page;
      tab.setAttribute('aria-selected', String(active)); tab.tabIndex = active ? 0 : -1;
      $(`page-${tab.dataset.page}`).hidden = !active;
    });
    document.querySelector('footer').hidden = page !== 'calculator';
    document.querySelector('.brand-sub').textContent = `/ ${pageTitle(page).toUpperCase()}`;
    history.replaceState(null, '', `#${page === 'draw' ? 'canvas' : page}`);
    document.title = t(`${pageTitle(page)} · Jev`);
  }
  tabs.forEach((tab, index) => {
    tab.addEventListener('click', () => switchPage(tab.dataset.page));
    tab.addEventListener('keydown', (event) => {
      const next = {ArrowRight: (index + 1) % tabs.length, ArrowLeft: (index + tabs.length - 1) % tabs.length, Home: 0, End: tabs.length - 1}[event.key];
      if (next === undefined) return;
      event.preventDefault(); tabs[next].click(); tabs[next].focus();
    });
  });
  function pageFromHash() {
    const page = location.hash === '#canvas' ? 'draw' : location.hash.slice(1);
    switchPage(['calculator', 'chat', 'draw'].includes(page) ? page : 'calculator');
  }
  window.addEventListener('hashchange', pageFromHash);
  pageFromHash();
  const characterLabel = (choice) => choice === 'SPACE' ? t('空格') : choice === 'NEWLINE' ? t('换行') : choice === 'END' ? t('终止符') : choice;
  function selectCharacter(turn, index, focus = false) {
    selection = {turn, index};
    turn.focusIndex = index;
    document.querySelectorAll('.chat-character').forEach((button) => {
      const selected = button === turn.buttons[index];
      button.classList.toggle('selected', selected);
      button.setAttribute('aria-pressed', String(selected));
    });
    turns.forEach((item) => item.buttons.forEach((button, i) => { button.tabIndex = i === (item.focusIndex ?? 0) ? 0 : -1; }));
    if (focus) turn.buttons[index].focus();
    const step = turn.steps[index];
    $('chat-detail-empty').hidden = true; $('chat-detail').hidden = false;
    $('chat-position').textContent = t('第 {n} 次判断', {n: index + 1});
    $('chat-choice').textContent = characterLabel(step.choice);
    $('chat-probability').textContent = percent(step.probabilities[step.choice]);
    $('chat-confidence').textContent = percent(step.confidence);
    const ranked = Object.entries(step.probabilities).sort(([a, pa], [b, pb]) => pb - pa || Number(b === step.choice) - Number(a === step.choice) || a.localeCompare(b));
    $('chat-candidates').replaceChildren(...ranked.map(([option, probability]) => {
      const row = node('div', `candidate${option === step.choice ? ' chosen' : ''}`);
      const bar = node('div', 'bar'), fill = node('div', 'fill');
      fill.style.width = `${probability * 100}%`; bar.append(fill);
      row.append(node('span', '', characterLabel(option)), bar, node('span', 'prob', percent(probability)));
      return row;
    }));
    $('chat-detail-meta').textContent = `${step.model} · ${step.latency_ms} ms · ${step.tokens} tokens`;
    renderRequestInput('chat', step.request);
  }
  function updateControls() {
    document.body.dataset.chatBusy = String(running);
    updateProviderControls();
    $('chat-send').hidden = running;
    $('chat-send').disabled = busy || document.body.dataset.drawBusy === 'true';
    $('chat-stop').hidden = !running; $('chat-stop').disabled = stopping;
    $('chat-clear').disabled = running; $('chat-limit').disabled = running;
    $('chat-input').readOnly = running;
    $('connection').disabled = busy || running || document.body.dataset.drawBusy === 'true';
    $('submit').disabled = busy || running || document.body.dataset.drawBusy === 'true';
    document.dispatchEvent(new Event('jev:chat-busy'));
  }
  document.addEventListener('jev:busy', updateControls);
  function statusText(turn) {
    const status = {generating: '生成中…', complete: '已结束', limit: '已达字符上限 · 未完成', repeated_space: '连续两个空格，已停止 · 未完成', repeated_character: '连续五个相同字符，已停止 · 未完成', stopped: '已停止 · 未完成', error: '请求失败 · 未完成'}[turn.status];
    return `${t(status)} · ${t('{n} 个字符', {n: turn.reply.length})}`;
  }
  function showStatus(turn) { turn.meta.textContent = statusText(turn); }
  function appendCharacter(turn, step) {
    const container = $('chat-messages');
    const atBottom = container.scrollHeight - container.scrollTop - container.clientHeight < 80;
    const index = turn.steps.length;
    const follow = !selection || (selection.turn === turn && selection.index === index - 1);
    turn.steps.push(step);
    const button = node('button', `chat-character${step.choice === 'END' ? ' chat-end' : ''}${step.choice === 'NEWLINE' ? ' chat-newline' : ''}${step.choice === 'SPACE' ? ' chat-space' : ''}`, step.choice === 'END' ? 'END' : step.choice === 'NEWLINE' ? '↵' : step.character);
    button.type = 'button'; button.tabIndex = -1;
    button.setAttribute('aria-label', `${index + 1} · ${characterLabel(step.choice)}`);
    button.setAttribute('aria-pressed', 'false');
    button.addEventListener('click', () => selectCharacter(turn, index));
    button.addEventListener('keydown', (event) => {
      const next = {ArrowLeft: Math.max(0, index - 1), ArrowRight: Math.min(turn.steps.length - 1, index + 1), Home: 0, End: turn.steps.length - 1}[event.key];
      if (next !== undefined) { event.preventDefault(); selectCharacter(turn, next, true); }
    });
    turn.buttons.push(button); turn.output.append(button);
    if (step.choice === 'NEWLINE') turn.output.append(document.createElement('br'));
    if (index === 0) button.tabIndex = 0;
    if (follow) selectCharacter(turn, index);
    if (atBottom) container.scrollTop = container.scrollHeight;
  }
  $('chat-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    if (running || busy || document.body.dataset.drawBusy === 'true') return;
    const prompt = $('chat-input').value.trim();
    if (!prompt) return;
    if (!await configReady) {
      $('chat-error').textContent = t('无法连接计算服务，请刷新页面或稍后重试。'); $('chat-error').hidden = false; return;
    }
    if (running || busy || document.body.dataset.drawBusy === 'true') return;
    if (needsApiKey()) { openKeyDialog(); return; }
    const history = turns.slice(-3).flatMap((turn) => [{role: 'user', content: turn.prompt}, {role: 'assistant', content: turn.reply}]);
    const limit = Number($('chat-limit').value);
    running = true; stopping = false; selection = null; updateControls();
    $('chat-request').open = false;
    $('chat-error').hidden = true; $('chat-empty').hidden = true; $('chat-input').value = '';
    const user = node('div', 'chat-user', prompt), assistant = node('div', 'chat-assistant');
    const output = node('div', 'chat-output'), meta = node('p', 'chat-message-meta');
    meta.setAttribute('role', 'status');
    assistant.append(node('div', 'chat-author', t('JEV')), output, meta);
    const turn = {prompt, reply: '', steps: [], buttons: [], status: 'generating', output, meta};
    turns.push(turn); $('chat-messages').append(user, assistant); showStatus(turn);
    $('chat-messages').scrollTop = $('chat-messages').scrollHeight;
    try {
      while (!stopping) {
        controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 125000);
        let data;
        try {
          const response = await fetch('/api/chat', {method: 'POST', signal: controller.signal,
            headers: inferenceHeaders(),
            body: JSON.stringify({message: prompt, reply: turn.reply, history, max_characters: limit})});
          if (!(response.headers.get('content-type') || '').includes('application/json')) throw new Error(t('服务暂时不可用，请稍后重试。'));
          data = await response.json();
          if (!response.ok) throw new Error(errorText(data.error || '请求失败'));
        } finally { clearTimeout(timeout); }
        if (stopping) break;
        if (!data.step || !data.step.probabilities || typeof data.reply !== 'string' || !['continue', 'complete', 'limit', 'repeated_space', 'repeated_character'].includes(data.status)) throw new Error(t('服务返回了无效结果。'));
        turn.reply = data.reply; appendCharacter(turn, data.step);
        if (data.status === 'continue' && turn.reply.endsWith('  ')) data.status = 'repeated_space';
        if (data.status === 'continue' && turn.reply.length >= 5 && turn.reply.slice(-5) === turn.reply.slice(-1).repeat(5)) data.status = 'repeated_character';
        turn.status = data.status === 'continue' ? 'generating' : data.status; showStatus(turn);
        if (data.status !== 'continue') break;
      }
      if (stopping) turn.status = 'stopped';
    } catch (error) {
      turn.status = stopping ? 'stopped' : 'error';
      if (!stopping) {
        $('chat-error').textContent = error.name === 'AbortError' ? t('本轮请求超时，请稍后重试。') : error instanceof TypeError ? t('网络连接失败，请检查网络后重试。') : error.message;
        $('chat-error').hidden = false;
      }
    } finally {
      running = false; controller = null; showStatus(turn); updateControls();
      if (!$('page-chat').hidden) $('chat-input').focus();
    }
  });
  $('chat-stop').addEventListener('click', () => { stopping = true; controller?.abort(); updateControls(); });
  $('chat-input').addEventListener('keydown', (event) => {
    if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) { event.preventDefault(); $('chat-form').requestSubmit(); }
  });
  $('chat-clear').addEventListener('click', () => {
    if (running) return;
    turns.length = 0; selection = null;
    $('chat-request').open = false;
    $('chat-messages').replaceChildren($('chat-empty')); $('chat-empty').hidden = false;
    $('chat-detail').hidden = true; $('chat-detail-empty').hidden = false; $('chat-error').hidden = true;
    $('chat-input').value = ''; $('chat-input').focus();
  });
  document.addEventListener('jev:language', () => {
    document.querySelectorAll('.chat-author').forEach(author => { author.textContent = t('JEV'); });
    turns.forEach((turn) => { showStatus(turn); turn.buttons.forEach((button, i) => button.setAttribute('aria-label', `${i + 1} · ${characterLabel(turn.steps[i].choice)}`)); });
    if (selection) selectCharacter(selection.turn, selection.index);
    updateControls();
  });
})();
