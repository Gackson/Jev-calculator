const $ = (id) => document.getElementById(id);
const places = ['个位', '十位', '百位', '千位', '万位', '十万位', '百万位', '千万位', '亿位'];
const placeName = (p) => places[p] || `10^${p} 位`;
const percent = (p) => `${(p * 100).toFixed(1)}%`;
let mode = 'choice', steps = [], selected = null, runId = null, busy = false, terminal = false;
let apiKey = '';
// Always start checked, including browsers that restore prior form values.
$('include-context').checked = true;
function updateKeyStatus() {
  $('connection').textContent = apiKey ? 'API Key 已填写' : '设置 API Key';
  $('connection').classList.toggle('ready', Boolean(apiKey));
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
  $('api-key').value = '';
  $('api-key').placeholder = apiKey ? '已填写，输入新 Key 可替换' : '粘贴你的 API Key';
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
    $('key-error').textContent = '请输入有效的 API Key，不含空格或换行。';
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
function optionLabel(value) { return value === 'negative' ? '负数' : value === 'positive' ? '非负数' : value; }
function title(step) {
  if (step.event === 'sign') return '符号判断';
  if (step.event === 'digit') return `${placeName(step.position)}判断`;
  if (step.event === 'comparison') return `随机数 ${step.candidate}`;
  return `候选 ${step.candidate}`;
}
function question(step) {
  if (step.event === 'sign') return '向零截断后的整数是否为负数？';
  if (step.event === 'digit') return `绝对值的${placeName(step.position)}是哪一位数字，还是已经结束？`;
  if (step.event === 'comparison') return `${step.candidate} 是否大于结果的绝对值？`;
  return `${step.candidate} 是否等于结果的绝对值？`;
}
function setBusy(value) {
  busy = value;
  document.body.classList.toggle('busy', value);
  $('submit').disabled = value;
  $('submit').replaceChildren(document.createTextNode(value ? '预测中' : '开始计算'), node('span', '', value ? '…' : '↗'));
  $('stop').hidden = !value; $('stop').disabled = false;
  ['expression', 'include-context', 'mode-choice', 'mode-noul', 'connection'].forEach((id) => { $(id).disabled = value; });
  $('upper').disabled = value || mode !== 'noul';
  document.querySelectorAll('[data-example]').forEach((button) => { button.disabled = value; });
}
function updateMode() {
  const isNoul = mode === 'noul';
  $('mode-choice').setAttribute('aria-pressed', String(!isNoul));
  $('mode-noul').setAttribute('aria-pressed', String(isNoul));
  $('context-control').hidden = isNoul; $('range-control').hidden = !isNoul;
  $('upper').required = isNoul;
  $('upper').disabled = busy || !isNoul;
  $('digits').hidden = isNoul; $('noul-display').hidden = !isNoul;
  $('mode-tag').textContent = `${mode.toUpperCase()} / 整数`;
  $('mode-description').textContent = isNoul
    ? '随机取非答案数字猜大小，逐步缩小区间；剩余不足 5 项时逐项确认。'
    : '从个位向左逐位选择 0–9，遇到终止符即停止。';
}
function resetScreen() {
  steps = []; selected = null; terminal = false;
  $('error').hidden = true; $('first-error').hidden = true;
  $('detail').hidden = true; $('detail-empty').hidden = false;
  $('actual').textContent = '—'; $('verdict').textContent = '待对比'; $('verdict').className = 'verdict';
  $('comparison-note').textContent = '整数按向零截断比较';
  $('prediction-note').textContent = '';
  $('run-status').textContent = '准备好了，慢慢猜。'; $('run-meta').textContent = mode.toUpperCase();
  $('noul-stage').textContent = '当前候选区间'; $('noul-value').textContent = '—';
  renderSteps();
}
function selectStep(key) {
  selected = key;
  const step = steps.find((s) => s.judgment_index === key);
  if (!step) return;
  const noul = step.type === 'noul';
  $('detail-empty').hidden = true; $('detail').hidden = false;
  $('detail-place').textContent = `第 ${key} 步 · ${title(step)}`;
  $('detail-choice').textContent = optionLabel(step.choice);
  $('detail-question').textContent = question(step);
  $('confidence-label').textContent = noul ? '所选判断概率' : '判断置信度';
  $('confidence').textContent = percent(noul ? step.decision_probability : step.confidence);
  $('probability-label').textContent = noul ? 'NOUL · 是 / 否' : '概率 · TOP 3';
  const options = noul ? [{ option: '是', probability: step.noul }, { option: '否', probability: 1 - step.noul }] : step.top_three;
  $('candidates').replaceChildren(...options.map(({ option, probability }) => {
    const row = node('div', 'candidate'), bar = node('div', 'bar'), fill = node('div', 'fill');
    fill.style.width = `${probability * 100}%`; bar.append(fill);
    row.append(node('span', '', optionLabel(option)), bar, node('span', 'prob', percent(probability)));
    return row;
  }));
  $('detail-correct').textContent = `${step.first_error ? '首次错误 · ' : ''}${step.correct ? '判断正确' : '判断错误'} · 正确选项：${optionLabel(step.expected)}`;
  $('detail-correct').className = `detail-correct ${step.correct ? 'good' : 'bad'}`;
  $('detail-footnote').textContent = noul ? `Noul 无独立置信度；概率 ≥ 50% 判为“是”。` : '置信度不等于正确率。';
  document.querySelectorAll('[data-step]').forEach((button) => {
    const active = button.dataset.step === String(key);
    button.classList.toggle('selected', active); button.setAttribute('aria-pressed', String(active));
  });
}
function bindStep(button, step) {
  button.type = 'button'; button.dataset.step = step.judgment_index;
  button.setAttribute('aria-label', `第 ${step.judgment_index} 步 ${title(step)} ${optionLabel(step.choice)}，查看详情`);
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
  button.append(node('span', 'number', value), node('small', '', sign ? '符号' : step.choice === 'END' ? '终止' : placeName(step.position)));
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
    const range = step.after ? `${step.before.join('–')} → ${BigInt(step.after[0]) > BigInt(step.after[1]) ? '空区间' : step.after.join('–')}` : step.event === 'candidate' ? '逐项确认最终候选' : step.event === 'sign' ? '独立判断正负' : `从右向左 · 第 ${step.position + 1} 位`;
    description.append(node('small', '', range));
    row.append(description, node('span', 'step-answer', optionLabel(step.choice)));
    const p = step.type === 'noul' ? step.decision_probability : step.probabilities[step.choice];
    row.append(node('span', 'step-probability', `P ${percent(p)}`), node('span', `step-verdict ${step.correct ? 'good' : 'bad'}`, step.first_error ? '首次错误' : step.correct ? '正确' : '错误'));
    return bindStep(row, step);
  }) : [node('p', 'trace-empty', 'Jev的每次判断记录在这里')]));
  $('step-count').textContent = String(steps.length).padStart(2, '0');
}
function showError(message) { $('error').hidden = false; $('error').textContent = message; }
function handleEvent(event) {
  if (event.event === 'start') {
    $('actual').textContent = event.actual;
    $('comparison-note').textContent = `对照整数：${event.integer_target}`;
    $('run-status').textContent = mode === 'noul' ? '正在判断随机数与结果符号…' : '正在判断个位与结果符号…';
    if (mode === 'noul') $('noul-value').textContent = `0–${event.upper}`;
  } else if (['sign', 'digit', 'comparison', 'candidate'].includes(event.event)) {
    steps.push(event); renderSteps();
    if (selected === null || (event.event === 'digit' && steps.length === 2)) selectStep(event.judgment_index);
    $('run-meta').textContent = `${steps.length} 次判断`;
    if (event.event === 'digit') {
      $('run-status').textContent = event.choice === 'END' ? '已收到终止符，停止向左预测' : `已得到${placeName(event.position)}，正在判断${placeName(event.position + 1)}…`;
    } else if (event.event === 'comparison') {
      const empty = BigInt(event.after[0]) > BigInt(event.after[1]);
      $('noul-value').textContent = empty ? '空区间' : event.after.join('–');
      $('run-status').textContent = `${event.candidate} → Jev 判断${event.choice}，${empty ? '无剩余候选' : '继续缩小范围'}…`;
    } else if (event.event === 'candidate') {
      $('noul-stage').textContent = '逐项确认候选';
      $('run-status').textContent = `候选 ${event.candidate} → ${event.choice}`;
    }
    $('prediction-note').textContent = '';
    if (event.first_error) {
      $('first-error').hidden = false;
      $('first-error').textContent = `首次错误：第 ${event.judgment_index} 步 · ${title(event)} · 点击查看 →`;
      $('first-error').onclick = () => { selectStep(event.judgment_index); $('detail').scrollIntoView({ block: 'nearest', behavior: 'smooth' }); };
    }
  } else if (event.event === 'done') {
    terminal = true;
    $('run-meta').textContent = `${event.judgments} 次判断 · ${(event.elapsed_ms / 1000).toFixed(2)} s · ${event.tokens} tokens`;
    if (event.status !== 'complete') {
      const message = event.status === 'empty' ? 'Jev 在个位提前终止，未产生整数结果' : event.status === 'ambiguous' ? `多个候选被判为“是”：${event.accepted.join('、')}` : '没有候选被判为“是”，无法确定答案';
      $('run-status').textContent = '判断结束 · 无唯一有效结果';
      $('verdict').textContent = '无有效结果'; $('verdict').className = 'verdict bad';
      $('prediction-note').textContent = message;
      if (mode === 'noul') { $('noul-stage').textContent = '无法确定唯一答案'; $('noul-value').textContent = '—'; }
    } else {
      $('run-status').textContent = mode === 'noul' ? '判断完成 · 已检查所有最终候选' : '预测完成 · 已由终止符结束';
      $('verdict').textContent = event.match ? '整数一致' : '结果不同';
      $('verdict').className = `verdict ${event.match ? 'good' : 'bad'}`;
      $('prediction-note').textContent = `Jev 整数结果：${event.result} · ${event.first_error_index === null ? '所有判断均正确' : `首次错误在第 ${event.first_error_index} 步`}`;
      if (mode === 'noul') { $('noul-stage').textContent = 'JEV 最终整数'; $('noul-value').textContent = event.result; }
    }
  } else if (['error', 'limit', 'cancelled'].includes(event.event)) {
    terminal = true;
    $('run-status').textContent = event.event === 'cancelled' ? '测试已停止' : '预测未完成';
    $('prediction-note').textContent = '未完成，已保留现有判断。';
    $('verdict').textContent = '未完成'; $('verdict').className = 'verdict bad';
    if (event.message) showError(event.message);
  }
}
$('calculator-form').addEventListener('submit', async (e) => {
  e.preventDefault(); if (busy) return;
  const expression = $('expression').value.trim(); if (!expression) return;
  if (!apiKey) { openKeyDialog(); return; }
  resetScreen(); runId = crypto.randomUUID();
  $('run-status').textContent = '正在连接 Jev…'; setBusy(true);
  try {
    const response = await fetch('/api/calculate', { method: 'POST', headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${apiKey}` }, body: JSON.stringify({ expression, run_id: runId, mode, include_context: $('include-context').checked, upper: $('upper').value.trim() }) });
    if (!response.ok) throw new Error((await response.json()).error || '请求失败');
    const reader = response.body.getReader(), decoder = new TextDecoder();
    let buffer = '';
    for (;;) {
      const { value, done } = await reader.read();
      buffer += decoder.decode(value, { stream: !done });
      const lines = buffer.split('\n'); buffer = lines.pop();
      for (const line of lines) if (line.trim()) handleEvent(JSON.parse(line));
      if (done) break;
    }
    if (buffer.trim()) handleEvent(JSON.parse(buffer));
    if (!terminal) throw new Error('连接中断，未收到完整结果。');
  } catch (error) { handleEvent({ event: 'error', message: error.message }); }
  finally { setBusy(false); runId = null; }
});
$('stop').addEventListener('click', async () => {
  if (!runId) return;
  $('stop').disabled = true;
  $('run-status').textContent = '正在停止，等待当前请求结束后不再发起下一次判断…';
  try {
    const response = await fetch('/api/cancel', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ run_id: runId }) });
    if (!response.ok) throw new Error('停止请求失败，请稍后重试。');
  } catch (error) { showError(error.message); $('stop').disabled = false; }
});
['choice', 'noul'].forEach((value) => $(`mode-${value}`).addEventListener('click', () => {
  if (busy || mode === value) return;
  mode = value; updateMode(); resetScreen();
}));
$('include-context').addEventListener('change', () => { updateMode(); resetScreen(); });
document.querySelectorAll('[data-example]').forEach((button) => button.addEventListener('click', () => {
  $('expression').value = button.dataset.example; $('expression').focus();
}));
fetch('/api/config').then((r) => {
  if (!r.ok) throw new Error('服务未连接');
}).catch(() => { showError('无法连接本地服务，请重新启动 calculator.py。'); });
updateKeyStatus();
updateMode();
