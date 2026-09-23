const $ = (id) => document.getElementById(id);
const places = ['个位', '十位', '百位', '千位', '万位', '十万位', '百万位', '千万位', '亿位'];
const placeName = (p) => t(places[p]) || t('10^{p} 位', {p});
const percent = (p) => new Intl.NumberFormat(locale, {style: 'percent', minimumFractionDigits: 1, maximumFractionDigits: 1}).format(p);
let strategy = 'random', eventHistory = [], replaying = false;
let mode = 'choice', steps = [], selected = null, runId = null, busy = false, terminal = false;
let apiKey = '', stopRequested = false, environmentKey = false;
// Always start checked, including browsers that restore prior form values.
$('include-context').checked = true;
function updateKeyStatus() {
  $('connection').textContent = environmentKey ? t('使用环境 Key') : apiKey ? t('API Key 已填写') : t('设置 API Key');
  $('connection').classList.toggle('ready', Boolean(environmentKey || apiKey));
}
function normalizeApiKey(value) {
  let key = value.trim();
  for (let i = 0; i < 4; i++) {
    const previous = key;
    if (key.length >= 2 && ['""', "''", '“”', '‘’'].includes(key[0] + key[key.length - 1])) key = key.slice(1, -1).trim();
    key = key.replace(/^(?:export\s+)?TYPESAFE_API_KEY\s*=\s*/, '').trim();
    key = key.replace(/^(?:Authorization:\s*)?Bearer\s+/i, '').trim();
    if (key === previous) break;
  }
  return key;
}
function openKeyDialog() {
  $('key-note').textContent = environmentKey
    ? t('当前优先使用本地环境 Key。移除环境配置并重启服务后，可使用页面填写的 Key。')
    : t('仅当前页面使用，刷新后清除。');
  $('api-key').value = '';
  $('api-key').placeholder = apiKey ? t('已填写，输入新 Key 可替换') : t('粘贴你的 API Key');
  $('key-error').hidden = true;
  $('key-clear').disabled = !apiKey;
  $('key-dialog').showModal();
  $('api-key').focus();
}
$('connection').addEventListener('click', openKeyDialog);
$('key-close').addEventListener('click', () => $('key-dialog').close());
$('key-dialog').addEventListener('close', () => { $('api-key').value = ''; });
$('key-form').addEventListener('submit', (event) => {
  event.preventDefault();
  const value = normalizeApiKey($('api-key').value);
  if (!value && apiKey) { $('key-dialog').close(); return; }
  if (!/^[\x21-\x7e]{1,2048}$/.test(value)) {
    $('key-error').textContent = t('请输入有效的 API Key，不含空格或换行。');
    $('key-error').hidden = false;
    return;
  }
  apiKey = value;
  updateKeyStatus();
  $('key-dialog').close();
});
$('key-clear').addEventListener('click', () => {
  apiKey = ''; updateKeyStatus(); $('key-dialog').close();
});
function node(tag, className, text) {
  const el = document.createElement(tag);
  if (className) el.className = className;
  if (text !== undefined) el.textContent = text;
  return el;
}
function optionLabel(value) { return value === 'negative' ? t('负数') : value === 'positive' ? t('非负数') : t(value); }
function title(step) {
  if (step.event === 'sign') return t('符号判断');
  if (step.event === 'digit') return t('{place}判断', {place: placeName(step.position)});
  if (step.event === 'comparison') return `${step.strategy === 'binary' ? t('二分法') : t('随机数')} ${step.candidate}`;
  return t('候选 {n}', {n: step.candidate});
}
function question(step) {
  if (step.event === 'sign') return t('向零截断后的整数是否为负数？');
  if (step.event === 'digit') return t('绝对值的{place}是哪一位数字，还是已经结束？', {place: placeName(step.position)});
  if (step.event === 'comparison') return t('{n} 是否大于结果的绝对值？', {n: step.candidate});
  return t('{n} 是否等于结果的绝对值？', {n: step.candidate});
}
function setBusy(value) {
  busy = value;
  document.body.classList.toggle('busy', value);
  $('submit').disabled = value;
  $('submit').replaceChildren(document.createTextNode(value ? t('预测中') : t('开始计算')), node('span', '', value ? '…' : '↗'));
  $('stop').hidden = !value; $('stop').disabled = false;
  ['expression', 'include-context', 'mode-choice', 'mode-noul', 'connection', 'strategy-binary', 'strategy-random'].forEach((id) => { $(id).disabled = value; });
  $('upper').disabled = value || mode !== 'noul';
  document.querySelectorAll('[data-example]').forEach((button) => { button.disabled = value; });
}
function updateMode() {
  const isNoul = mode === 'noul';
  ['binary', 'random'].forEach((value) => $(`strategy-${value}`).setAttribute('aria-pressed', String(strategy === value)));
  $('mode-choice').setAttribute('aria-pressed', String(!isNoul));
  $('mode-noul').setAttribute('aria-pressed', String(isNoul));
  $('context-control').hidden = isNoul; $('range-control').hidden = !isNoul;
  $('upper').required = isNoul;
  $('upper').disabled = busy || !isNoul;
  $('digits').hidden = isNoul; $('noul-display').hidden = !isNoul;
  $('mode-tag').textContent = t('{mode} / 整数', {mode: mode.toUpperCase()});
  ['choice', 'random', 'binary'].forEach((value) => {
    $(`description-${value}`).hidden = value !== (isNoul ? strategy : 'choice');
  });
}
// Decorative, one-shot feedback: no input blocking and no persistent particles.
const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
const resultCard = document.querySelector('.comparison');
let resultEffect = null, resultEffectTimer = null;
function clearResultEffect() {
  clearTimeout(resultEffectTimer);
  resultEffectTimer = null;
  resultEffect?.remove();
  resultEffect = null;
  resultCard.classList.remove('result-celebrate', 'result-oops');
}
function playResultEffect(correct) {
  clearResultEffect();
  if (replaying || reducedMotion.matches || document.hidden) return;
  resultCard.classList.add(correct ? 'result-celebrate' : 'result-oops');
  const rect = resultCard.getBoundingClientRect();
  const x = Math.max(30, Math.min(innerWidth - 30, rect.left + rect.width * .65));
  const y = Math.max(90, Math.min(innerHeight - 100, rect.top + 75));
  const layer = node('div', 'result-effect');
  layer.setAttribute('aria-hidden', 'true');
  const colors = ['#df633f', '#e5b83e', '#779d77', '#669bc1', '#ba83ae', '#e4a58b'];
  const count = correct ? (innerWidth < 600 ? 30 : 48) : 3;
  for (let i = 0; i < count; i++) {
    const piece = node('span', correct ? 'confetti-piece' : 'oops-mark', correct ? '' : '?');
    const dx = correct ? (Math.random() - .5) * Math.min(640, innerWidth * .85) : (i - 1) * 36;
    piece.style.left = `${x}px`;
    piece.style.top = `${y}px`;
    piece.style.setProperty('--dx', `${dx}px`);
    piece.style.setProperty('--peak-x', `${dx * .7}px`);
    piece.style.setProperty('--rise', `${-(45 + Math.random() * (correct ? 125 : 25))}px`);
    piece.style.setProperty('--fall', `${correct ? 170 + Math.random() * 160 : -25}px`);
    piece.style.setProperty('--turn', `${correct ? (Math.random() - .5) * 900 : (i - 1) * 18}deg`);
    piece.style.setProperty('--delay', `${i * (correct ? 3 : 80)}ms`);
    if (correct) {
      piece.style.backgroundColor = colors[i % colors.length];
      piece.style.borderRadius = i % 3 === 0 ? '50%' : '1px';
      piece.style.width = `${5 + Math.random() * 4}px`;
      piece.style.height = `${8 + Math.random() * 6}px`;
    }
    layer.append(piece);
  }
  resultEffect = layer;
  document.body.append(layer);
  resultEffectTimer = setTimeout(clearResultEffect, correct ? 2000 : 1050);
}
reducedMotion.addEventListener('change', clearResultEffect);
document.addEventListener('visibilitychange', () => { if (document.hidden) clearResultEffect(); });

function resetScreen() {
  clearResultEffect();
  if (!replaying) eventHistory = [];
  steps = []; selected = null; terminal = false;
  $('error').hidden = true; $('first-error').hidden = true;
  $('detail').hidden = true; $('detail-empty').hidden = false;
  $('actual').textContent = '—'; $('verdict').textContent = t('待对比'); $('verdict').className = 'verdict';
  $('comparison-note').textContent = t('整数按向零截断比较');
  $('prediction-note').textContent = '';
  $('run-status').textContent = t('准备好了，慢慢猜。'); $('run-meta').textContent = mode.toUpperCase();
  $('noul-stage').textContent = t('当前候选区间'); $('noul-value').textContent = '—';
  renderSteps();
}
function selectStep(key) {
  selected = key;
  const step = steps.find((s) => s.judgment_index === key);
  if (!step) return;
  const noul = step.type === 'noul';
  $('detail-empty').hidden = true; $('detail').hidden = false;
  $('detail-place').textContent = t('第 {n} 步 · {title}', {n: key, title: title(step)});
  $('detail-choice').textContent = optionLabel(step.choice);
  $('detail-question').textContent = question(step);
  $('confidence-label').textContent = noul ? t('所选判断概率') : t('判断置信度');
  $('confidence').textContent = percent(noul ? step.decision_probability : step.confidence);
  $('probability-label').textContent = noul ? t('NOUL · 是 / 否') : t('概率 · TOP 3');
  const options = noul ? [{ option: '是', probability: step.noul }, { option: '否', probability: 1 - step.noul }] : step.top_three;
  $('candidates').replaceChildren(...options.map(({ option, probability }) => {
    const row = node('div', 'candidate'), bar = node('div', 'bar'), fill = node('div', 'fill');
    fill.style.width = `${probability * 100}%`; bar.append(fill);
    row.append(node('span', '', optionLabel(option)), bar, node('span', 'prob', percent(probability)));
    return row;
  }));
  $('detail-correct').textContent = `${step.first_error ? t('首次错误') + ' · ' : ''}${step.correct ? t('判断正确') : t('判断错误')} · ${t('正确选项：{option}', {option: optionLabel(step.expected)})}`;
  $('detail-correct').className = `detail-correct ${step.correct ? 'good' : 'bad'}`;
  $('detail-footnote').textContent = noul ? t('Noul 无独立置信度；概率 ≥ 50% 判为“是”。') : t('置信度不等于正确率。');
  document.querySelectorAll('[data-step]').forEach((button) => {
    const active = button.dataset.step === String(key);
    button.classList.toggle('selected', active); button.setAttribute('aria-pressed', String(active));
  });
}
function bindStep(button, step) {
  button.type = 'button'; button.dataset.step = step.judgment_index;
  button.setAttribute('aria-label', t('第 {n} 步 {title} {choice}，查看详情', {n: step.judgment_index, title: title(step), choice: optionLabel(step.choice)}));
  button.setAttribute('aria-pressed', String(selected === step.judgment_index));
  if (selected === step.judgment_index) button.classList.add('selected');
  if (step.first_error) button.classList.add('first-wrong');
  button.addEventListener('click', () => selectStep(step.judgment_index));
  return button;
}
function digitButton(step) {
  const sign = step.event === 'sign';
  const value = sign ? '−' : step.choice;
  const button = node('button', `digit${step.choice === 'END' ? ' end' : ''}${sign ? ' sign' : ''}`);
  button.append(node('span', 'number', value), node('small', '', sign ? t('符号') : step.choice === 'END' ? t('终止') : placeName(step.position)));
  return bindStep(button, step);
}
function renderSteps() {
  const digitSteps = steps.filter((s) => s.event === 'digit');
  const cards = [], end = digitSteps.find((s) => s.choice === 'END'), sign = steps.find((s) => s.event === 'sign');
  if (end) cards.push(digitButton(end));
  if (sign?.choice === 'negative') cards.push(digitButton(sign));
  digitSteps.filter((s) => s.choice !== 'END').slice().reverse().forEach((s) => cards.push(digitButton(s)));
  $('digits').replaceChildren(...(cards.length ? cards : [node('span', 'placeholder', '—')]));
  $('trace').replaceChildren(...(steps.length ? steps.map((step) => {
    const row = node('button', 'judgment-row');
    row.append(node('span', 'step-index', String(step.judgment_index).padStart(2, '0')));
    const description = node('span', 'step-description');
    description.append(node('strong', '', title(step)));
    const range = step.after ? `${step.before.join('–')} → ${BigInt(step.after[0]) > BigInt(step.after[1]) ? t('空区间') : step.after.join('–')}` : step.event === 'candidate' ? t('逐项确认最终候选') : step.event === 'sign' ? t('独立判断正负') : t('从右向左 · 第 {n} 位', {n: step.position + 1});
    description.append(node('small', '', range));
    row.append(description, node('span', 'step-answer', optionLabel(step.choice)));
    const p = step.type === 'noul' ? step.decision_probability : step.probabilities[step.choice];
    row.append(node('span', 'step-probability', `P ${percent(p)}`), node('span', `step-verdict ${step.correct ? 'good' : 'bad'}`, step.first_error ? t('首次错误') : step.correct ? t('正确') : t('错误')));
    return bindStep(row, step);
  }) : [node('p', 'trace-empty', t('Jev的每次判断记录在这里'))]));
  $('step-count').textContent = String(steps.length).padStart(2, '0');
}
function showError(message) { $('error').hidden = false; $('error').dataset.message = message; $('error').textContent = errorText(message); }
function handleEvent(event) {
  if (!replaying) eventHistory.push(event);
  if (event.event === 'start') {
    $('actual').textContent = event.actual;
    $('comparison-note').textContent = t('对照整数：{n}', {n: event.integer_target});
    $('run-status').textContent = mode === 'noul' ? t('正在判断候选数与结果符号…') : t('正在判断个位与结果符号…');
    if (mode === 'noul') $('noul-value').textContent = `0–${event.upper}`;
  } else if (['sign', 'digit', 'comparison', 'candidate'].includes(event.event)) {
    steps.push(event); renderSteps();
    selectStep(event.judgment_index);
    if (!replaying) {
      $('trace').scrollTop = $('trace').scrollHeight;
    }
    $('run-meta').textContent = t('{n} 次判断', {n: steps.length});
    if (event.event === 'digit') {
      $('run-status').textContent = event.choice === 'END' ? t('已收到终止符，停止向左预测') : t('已得到{place}，正在判断{next}…', {place: placeName(event.position), next: placeName(event.position + 1)});
    } else if (event.event === 'comparison') {
      const empty = BigInt(event.after[0]) > BigInt(event.after[1]);
      $('noul-value').textContent = empty ? t('空区间') : event.after.join('–');
      $('run-status').textContent = t('{n} → Jev 判断{choice}，{next}…', {n: event.candidate, choice: optionLabel(event.choice), next: empty ? t('无剩余候选') : t('继续缩小范围')});
    } else if (event.event === 'candidate') {
      $('noul-stage').textContent = t('逐项确认候选');
      $('run-status').textContent = t('候选 {n} → {choice}', {n: event.candidate, choice: optionLabel(event.choice)});
    }
    $('prediction-note').textContent = '';
    if (event.first_error) {
      $('first-error').hidden = false;
      $('first-error').textContent = t('首次错误：第 {n} 步 · {title} · 点击查看 →', {n: event.judgment_index, title: title(event)});
      $('first-error').onclick = () => { selectStep(event.judgment_index); $('detail').scrollIntoView({ block: 'nearest', behavior: 'smooth' }); };
    }
  } else if (event.event === 'done') {
    if (terminal) return;
    terminal = true;
    $('run-meta').textContent = `${t('{n} 次判断', {n: event.judgments})} · ${(event.elapsed_ms / 1000).toFixed(2)} s · ${event.tokens} tokens`;
    if (event.status !== 'complete') {
      const message = event.status === 'empty' ? t('Jev 在个位提前终止，未产生整数结果') : event.status === 'ambiguous' ? t('多个候选被判为“是”：{values}', {values: event.accepted.join(', ')}) : t('没有候选被判为“是”，无法确定答案');
      $('run-status').textContent = t('判断结束 · 无唯一有效结果');
      $('verdict').textContent = t('无有效结果'); $('verdict').className = 'verdict bad';
      $('prediction-note').textContent = message;
      if (mode === 'noul') { $('noul-stage').textContent = t('无法确定唯一答案'); $('noul-value').textContent = '—'; }
    } else {
      $('run-status').textContent = mode === 'noul' ? t('判断完成 · 已检查所有最终候选') : t('预测完成 · 已由终止符结束');
      $('verdict').textContent = event.match ? t('整数一致') : t('结果不同');
      $('verdict').className = `verdict ${event.match ? 'good' : 'bad'}`;
      $('prediction-note').textContent = t('Jev 整数结果：{n} · {audit}', {n: event.result, audit: event.first_error_index === null ? t('所有判断均正确') : t('首次错误在第 {n} 步', {n: event.first_error_index})});
      if (mode === 'noul') { $('noul-stage').textContent = t('JEV 最终整数'); $('noul-value').textContent = event.result; }
      playResultEffect(event.match === true);
    }
  } else if (['error', 'limit', 'cancelled'].includes(event.event)) {
    terminal = true;
    $('run-status').textContent = event.event === 'cancelled' ? t('测试已停止') : t('预测未完成');
    $('prediction-note').textContent = t('未完成，已保留现有判断。');
    $('verdict').textContent = t('未完成'); $('verdict').className = 'verdict bad';
    if (event.message) showError(event.message);
  }
}
$('calculator-form').addEventListener('submit', async (e) => {
  e.preventDefault(); if (busy) return;
  const expression = $('expression').value.trim(); if (!expression) return;
  if (!await configReady || busy) return;
  if (!environmentKey && !apiKey) { openKeyDialog(); return; }
  resetScreen(); runId = crypto.randomUUID(); stopRequested = false;
  $('run-status').textContent = t('正在连接 Jev…'); setBusy(true);
  const input = { expression, mode, strategy, include_context: $('include-context').checked, upper: $('upper').value.trim() };
  const started = performance.now();
  try {
    let cursor = null;
    do {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 125000);
      let data;
      try {
        const response = await fetch('/api/step', { method: 'POST', signal: controller.signal,
          headers: { 'Content-Type': 'application/json', ...(!environmentKey && apiKey ? { 'Authorization': `Bearer ${apiKey}` } : {}) },
          body: JSON.stringify({ ...input, cursor }) });
        if (!(response.headers.get('content-type') || '').includes('application/json')) {
          throw new Error('服务暂时不可用，请稍后重试。');
        }
        data = await response.json();
        if (!response.ok) throw new Error(data.error || '请求失败');
      } finally { clearTimeout(timeout); }
      if (stopRequested) { handleEvent({ event: 'cancelled' }); break; }
      if (!Array.isArray(data.events) || !Object.hasOwn(data, 'cursor')) throw new Error('服务返回了无效结果。');
      for (const event of data.events) {
        if (event.event === 'done') event.elapsed_ms = Math.round(performance.now() - started);
        handleEvent(event);
      }
      cursor = data.cursor;
    } while (cursor && !terminal);
    if (!terminal) throw new Error('连接中断，未收到完整结果。');
  } catch (error) {
    handleEvent(stopRequested ? { event: 'cancelled' } : { event: 'error',
      message: error.name === 'AbortError' ? '本轮请求超时，请稍后重试。' : error instanceof TypeError ? '网络连接失败，请检查网络后重试。' : error.message });
  } finally { setBusy(false); runId = null; }
});
$('stop').addEventListener('click', () => {
  if (!runId) return;
  stopRequested = true;
  $('stop').disabled = true;
  $('run-status').textContent = t('正在停止，等待当前请求结束后不再发起下一次判断…');
});
['choice', 'noul'].forEach((value) => $(`mode-${value}`).addEventListener('click', () => {
  if (busy || mode === value) return;
  mode = value; updateMode(); resetScreen();
}));
['binary', 'random'].forEach((value) => $(`strategy-${value}`).addEventListener('click', () => {
  if (busy || strategy === value) return;
  strategy = value; updateMode(); resetScreen();
}));
$('include-context').addEventListener('change', () => { updateMode(); resetScreen(); });
document.querySelectorAll('[data-example]').forEach((button) => button.addEventListener('click', () => {
  $('expression').value = button.dataset.example; $('expression').focus();
}));
const configReady = fetch('/api/config').then((r) => {
  if (!r.ok) throw new Error('服务未连接');
  return r.json();
}).then((config) => {
  environmentKey = config.auth_mode === 'environment';
  updateKeyStatus();
  return true;
}).catch(() => { showError('无法连接计算服务，请刷新页面或稍后重试。'); return false; });
updateKeyStatus();
updateMode();

function changeLanguage(value) {
  locale = value;
  try { localStorage.setItem('jev-language', locale); } catch (_) { /* Storage may be disabled. */ }
  const previousSelection = selected;
  const hadError = !$('error').hidden, errorMessage = $('error').dataset.message;
  const history = eventHistory.slice();
  replaying = true;
  try {
    translatePage(); updateKeyStatus(); updateMode(); resetScreen();
    history.forEach(handleEvent);
    if (previousSelection !== null) selectStep(previousSelection);
    if (hadError) showError(errorMessage);
    setBusy(busy);
    if (stopRequested && busy) { $('stop').disabled = true; $('run-status').textContent = t('正在停止，等待当前请求结束后不再发起下一次判断…'); }
    else if (busy && !history.length) $('run-status').textContent = t('正在连接 Jev…');
  } finally { replaying = false; }
}

const languageItems = [...document.querySelectorAll('[data-language]')];
function updateLanguageMenu() {
  languageItems.forEach((item) => item.setAttribute('aria-checked', String(item.dataset.language === locale)));
}
function closeLanguageMenu(restoreFocus = false) {
  $('language-menu').hidden = true;
  $('language').setAttribute('aria-expanded', 'false');
  if (restoreFocus) $('language').focus();
}
function openLanguageMenu(index = languageItems.findIndex((item) => item.dataset.language === locale)) {
  updateLanguageMenu();
  $('language-menu').hidden = false;
  $('language').setAttribute('aria-expanded', 'true');
  languageItems[Math.max(0, index)].focus();
}
$('language').addEventListener('click', () => {
  if ($('language-menu').hidden) openLanguageMenu();
  else closeLanguageMenu(true);
});
$('language').addEventListener('keydown', (event) => {
  if (!['ArrowDown', 'ArrowUp'].includes(event.key)) return;
  event.preventDefault();
  openLanguageMenu(event.key === 'ArrowDown' ? 0 : languageItems.length - 1);
});
languageItems.forEach((item) => item.addEventListener('click', () => {
  if (locale !== item.dataset.language) changeLanguage(item.dataset.language);
  updateLanguageMenu();
  closeLanguageMenu(true);
}));
$('language-menu').addEventListener('keydown', (event) => {
  const index = languageItems.indexOf(document.activeElement);
  const next = {ArrowDown: (index + 1) % languageItems.length, ArrowUp: (index - 1 + languageItems.length) % languageItems.length, Home: 0, End: languageItems.length - 1}[event.key];
  if (next !== undefined) { event.preventDefault(); languageItems[next].focus(); }
  if (event.key === 'Escape') { event.preventDefault(); closeLanguageMenu(true); }
});
// Closing on focus departure preserves normal Tab navigation to the API button.
$('language-picker').addEventListener('focusout', (event) => {
  if (!$('language-picker').contains(event.relatedTarget)) closeLanguageMenu();
});
document.addEventListener('click', (event) => {
  if (!$('language-picker').contains(event.target)) closeLanguageMenu();
});
updateLanguageMenu();
translatePage();
resetScreen();
