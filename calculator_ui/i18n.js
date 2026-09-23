// UI messages only. Language choice never changes model questions or API credentials.
const messages = {
  "设置 API Key": {
    "zh-TW": "設定 API Key",
    "en": "Set API Key",
    "ja": "API Key を設定",
    "es": "Configurar API Key",
    "ko": "API Key 설정"
  },
  "使用环境 Key": {
    "zh-TW": "使用環境 Key",
    "en": "Using environment key",
    "ja": "環境の Key を使用中",
    "es": "Key del entorno en uso",
    "ko": "환경 Key 사용 중"
  },
  "API Key 已填写": {
    "zh-TW": "API Key 已填寫",
    "en": "API Key ready",
    "ja": "API Key 設定済み",
    "es": "API Key configurada",
    "ko": "API Key 설정됨"
  },
  "使用自己的 API Key": {
    "zh-TW": "使用自己的 API Key",
    "en": "Use your own API Key",
    "ja": "自分の API Key を使用",
    "es": "Usa tu propia API Key",
    "ko": "내 API Key 사용"
  },
  "关闭 API 设置": {
    "zh-TW": "關閉 API 設定",
    "en": "Close API settings",
    "ja": "API 設定を閉じる",
    "es": "Cerrar ajustes de API",
    "ko": "API 설정 닫기"
  },
  "粘贴你的 API Key": {
    "zh-TW": "貼上你的 API Key",
    "en": "Paste your API Key",
    "ja": "API Key を貼り付け",
    "es": "Pega tu API Key",
    "ko": "API Key 붙여넣기"
  },
  "仅当前页面使用，刷新后清除。": {
    "zh-TW": "僅目前頁面使用，重新整理後清除。",
    "en": "Used only on this page; cleared on reload.",
    "ja": "このページのみで使用し、再読み込みで消去します。",
    "es": "Solo se usa en esta página; se borra al recargar.",
    "ko": "이 페이지에서만 사용하며 새로고침하면 지워집니다."
  },
  "清除": {
    "zh-TW": "清除",
    "en": "Clear",
    "ja": "消去",
    "es": "Borrar",
    "ko": "지우기"
  },
  "使用此 Key": {
    "zh-TW": "使用此 Key",
    "en": "Use this Key",
    "ja": "この Key を使用",
    "es": "Usar esta Key",
    "ko": "이 Key 사용"
  },
  "当前优先使用本地环境 Key。移除环境配置并重启服务后，可使用页面填写的 Key。": {
    "zh-TW": "目前優先使用本機環境 Key。移除環境設定並重啟服務後，可使用頁面填寫的 Key。",
    "en": "The local environment key takes priority. Remove it and restart the service to use a key entered here.",
    "ja": "ローカル環境の Key が優先されます。環境設定から削除してサービスを再起動すると、ここに入力した Key を使えます。",
    "es": "La key del entorno local tiene prioridad. Elimínala y reinicia el servicio para usar una key introducida aquí.",
    "ko": "로컬 환경 Key가 우선됩니다. 환경 설정에서 제거하고 서비스를 재시작하면 여기에 입력한 Key를 사용할 수 있습니다."
  },
  "已填写，输入新 Key 可替换": {
    "zh-TW": "已填寫，輸入新 Key 可替換",
    "en": "Enter a new Key to replace the current one",
    "ja": "新しい Key を入力すると置き換わります",
    "es": "Introduce otra Key para sustituir la actual",
    "ko": "새 Key를 입력하면 교체됩니다"
  },
  "请输入有效的 API Key，不含空格或换行。": {
    "zh-TW": "請輸入有效的 API Key，不含空格或換行。",
    "en": "Enter a valid API Key without spaces or line breaks.",
    "ja": "空白や改行を含まない有効な API Key を入力してください。",
    "es": "Introduce una API Key válida, sin espacios ni saltos de línea.",
    "ko": "공백이나 줄바꿈 없이 유효한 API Key를 입력하세요."
  },
  "Dumb Calculator 首页": {
    "zh-TW": "Dumb Calculator 首頁",
    "en": "Dumb Calculator home",
    "ja": "Dumb Calculator ホーム",
    "es": "Inicio de Dumb Calculator",
    "ko": "Dumb Calculator 홈"
  },
  "看看 Jev 能否用滑稽的方式预测出算式答案": {
    "zh-TW": "看看 Jev 能否用滑稽的方式預測出算式答案",
    "en": "Can Jev guess the answer in a wonderfully silly way?",
    "ja": "Jev はこんな愉快な方法で答えを当てられる？",
    "es": "¿Podrá Jev adivinar la respuesta de una forma absurdamente divertida?",
    "ko": "Jev가 우스꽝스러운 방법으로 정답을 맞힐 수 있을까요?"
  },
  "输入算式": {
    "zh-TW": "輸入算式",
    "en": "Expression input",
    "ja": "式の入力",
    "es": "Entrada de la operación",
    "ko": "수식 입력"
  },
  "计算模式": {
    "zh-TW": "計算模式",
    "en": "Calculation mode",
    "ja": "計算モード",
    "es": "Modo de cálculo",
    "ko": "계산 모드"
  },
  "Choice · 按位计算": {
    "zh-TW": "Choice · 逐位計算",
    "en": "Choice · Digit by digit",
    "ja": "Choice · 一桁ずつ",
    "es": "Choice · Dígito a dígito",
    "ko": "Choice · 자릿수별 계산"
  },
  "Noul · 猜大小": {
    "zh-TW": "Noul · 猜大小",
    "en": "Noul · Higher or lower",
    "ja": "Noul · 大きい？小さい？",
    "es": "Noul · Mayor o menor",
    "ko": "Noul · 클까 작을까"
  },
  "从个位向左逐位选择 0–9，遇到终止符即停止。": {
    "zh-TW": "從個位向左逐位選擇 0–9，遇到終止符即停止。",
    "en": "Pick digits 0–9 from right to left; stop at END.",
    "ja": "一の位から左へ 0–9 を選び、END で終了します。",
    "es": "Elige dígitos del 0 al 9 de derecha a izquierda; termina con END.",
    "ko": "일의 자리부터 왼쪽으로 0–9를 고르고 END에서 멈춥니다."
  },
  "随机取非答案数字猜大小，逐步缩小区间；剩余不足 5 项时逐项确认。": {
    "zh-TW": "隨機取非答案數字猜大小，逐步縮小區間；剩餘不足 5 項時逐項確認。",
    "en": "Compare a random non-answer to narrow the range. With fewer than 5 candidates, check each one.",
    "ja": "正解以外の乱数と比較して範囲を絞り、候補が 5 個未満になったら一つずつ確認します。",
    "es": "Compara un número aleatorio distinto de la respuesta para acotar el rango. Con menos de 5 candidatos, comprueba cada uno.",
    "ko": "정답이 아닌 난수와 비교해 범위를 좁힙니다. 후보가 5개 미만이면 하나씩 확인합니다."
  },
  "取区间中点猜大小；中点为答案时改取相邻数，剩余不足 5 项时逐项确认。": {
    "zh-TW": "取區間中點猜大小；中點為答案時改取相鄰數，剩餘不足 5 項時逐項確認。",
    "en": "Compare the midpoint (a neighbor if it is the answer). With fewer than 5 candidates, check each one.",
    "ja": "範囲の中点と比較します。中点が正解なら隣の数を使い、候補が 5 個未満で個別に確認します。",
    "es": "Compara el punto medio (un vecino si es la respuesta). Con menos de 5 candidatos, comprueba cada uno.",
    "ko": "범위의 중간값과 비교합니다. 정답이면 이웃한 수를 쓰고, 후보가 5개 미만이면 하나씩 확인합니다."
  },
  "输入整数算式": {
    "zh-TW": "輸入整數算式",
    "en": "Enter an integer expression",
    "ja": "整数の式を入力",
    "es": "Introduce una operación con enteros",
    "ko": "정수 수식 입력"
  },
  "例如 (128 + 357) × 6": {
    "zh-TW": "例如 (128 + 357) × 6",
    "en": "e.g. (128 + 357) × 6",
    "ja": "例：(128 + 357) × 6",
    "es": "Ej.: (128 + 357) × 6",
    "ko": "예: (128 + 357) × 6"
  },
  "开始计算": {
    "zh-TW": "開始計算",
    "en": "Calculate",
    "ja": "計算する",
    "es": "Calcular",
    "ko": "계산 시작"
  },
  "停止": {
    "zh-TW": "停止",
    "en": "Stop",
    "ja": "停止",
    "es": "Detener",
    "ko": "중지"
  },
  "在每次预测时，带入之前位次的预测结果": {
    "zh-TW": "每次預測時，帶入先前位數的預測結果",
    "en": "Include previously predicted digits in each prediction",
    "ja": "予測するたびに、それまでの桁の予測結果を含める",
    "es": "Incluir los dígitos ya predichos en cada predicción",
    "ko": "매 예측에 이전 자릿수의 예측 결과 포함"
  },
  "绝对值范围：0 至": {
    "zh-TW": "絕對值範圍：0 至",
    "en": "Magnitude range: 0 to",
    "ja": "絶対値の範囲：0 ～",
    "es": "Rango absoluto: de 0 a",
    "ko": "절댓값 범위: 0부터"
  },
  "上限须大于结果绝对值": {
    "zh-TW": "上限須大於結果絕對值",
    "en": "Limit must exceed the absolute result",
    "ja": "上限は結果の絶対値より大きくしてください",
    "es": "El límite debe superar el valor absoluto del resultado",
    "ko": "상한은 결과의 절댓값보다 커야 합니다"
  },
  "取数方式": {
    "zh-TW": "取數方式",
    "en": "Number selection",
    "ja": "数の選び方",
    "es": "Selección del número",
    "ko": "숫자 선택 방식"
  },
  "二分法": {
    "zh-TW": "二分法",
    "en": "Binary search",
    "ja": "二分探索",
    "es": "Bisección",
    "ko": "이진 탐색"
  },
  "随机数": {
    "zh-TW": "隨機數",
    "en": "Random",
    "ja": "乱数",
    "es": "Aleatorio",
    "ko": "난수"
  },
  "加法": {
    "zh-TW": "加法",
    "en": "Addition",
    "ja": "足し算",
    "es": "Suma",
    "ko": "덧셈"
  },
  "混合运算": {
    "zh-TW": "混合運算",
    "en": "Mixed",
    "ja": "混合計算",
    "es": "Mixta",
    "ko": "혼합 연산"
  },
  "除法": {
    "zh-TW": "除法",
    "en": "Division",
    "ja": "割り算",
    "es": "División",
    "ko": "나눗셈"
  },
  "负数": {
    "zh-TW": "負數",
    "en": "Negative",
    "ja": "負数",
    "es": "Negativo",
    "ko": "음수"
  },
  "非负数": {
    "zh-TW": "非負數",
    "en": "Non-negative",
    "ja": "非負数",
    "es": "No negativo",
    "ko": "0 이상"
  },
  "准备好了，慢慢猜。": {
    "zh-TW": "準備好了，慢慢猜。",
    "en": "Ready. One guess at a time.",
    "ja": "準備完了。ゆっくり当てていこう。",
    "es": "Listo. Una suposición cada vez.",
    "ko": "준비 완료. 천천히 맞혀 봐요."
  },
  "右 → 左": {
    "zh-TW": "右 → 左",
    "en": "Right → left",
    "ja": "右 → 左",
    "es": "Derecha → izquierda",
    "ko": "오른쪽 → 왼쪽"
  },
  "结果对比": {
    "zh-TW": "結果對比",
    "en": "Result comparison",
    "ja": "結果の比較",
    "es": "Comparación de resultados",
    "ko": "결과 비교"
  },
  "JEV 预测": {
    "zh-TW": "JEV 預測",
    "en": "JEV PREDICTION",
    "ja": "JEV の予測",
    "es": "PREDICCIÓN DE JEV",
    "ko": "JEV 예측"
  },
  "CHOICE / 整数": {
    "zh-TW": "CHOICE / 整數",
    "en": "CHOICE / INTEGER",
    "ja": "CHOICE / 整数",
    "es": "CHOICE / ENTERO",
    "ko": "CHOICE / 정수"
  },
  "{mode} / 整数": {
    "zh-TW": "{mode} / 整數",
    "en": "{mode} / INTEGER",
    "ja": "{mode} / 整数",
    "es": "{mode} / ENTERO",
    "ko": "{mode} / 정수"
  },
  "当前候选区间": {
    "zh-TW": "目前候選區間",
    "en": "Current candidate range",
    "ja": "現在の候補範囲",
    "es": "Rango de candidatos actual",
    "ko": "현재 후보 범위"
  },
  "真实结果": {
    "zh-TW": "真實結果",
    "en": "Actual result",
    "ja": "実際の答え",
    "es": "Resultado real",
    "ko": "실제 결과"
  },
  "整数按向零截断比较": {
    "zh-TW": "整數以朝零截斷方式比較",
    "en": "Integers compared by truncating toward zero",
    "ja": "小数部をゼロ方向に切り捨てて整数を比較",
    "es": "Compara enteros truncados hacia cero",
    "ko": "소수부를 0 방향으로 버린 정수로 비교"
  },
  "待对比": {
    "zh-TW": "待比較",
    "en": "Awaiting result",
    "ja": "結果待ち",
    "es": "Pendiente",
    "ko": "비교 대기"
  },
  "判断详情": {
    "zh-TW": "判斷詳情",
    "en": "Judgment details",
    "ja": "判断の詳細",
    "es": "Detalles del juicio",
    "ko": "판단 상세"
  },
  "判断显微镜": {
    "zh-TW": "判斷顯微鏡",
    "en": "Judgment microscope",
    "ja": "判断の顕微鏡",
    "es": "Microscopio de juicios",
    "ko": "판단 현미경"
  },
  "点击数字或判断查看详情": {
    "zh-TW": "點擊數字或判斷查看詳情",
    "en": "Click a digit or judgment for details",
    "ja": "数字や判断をクリックして詳細を表示",
    "es": "Haz clic en un dígito o juicio para ver los detalles",
    "ko": "숫자나 판단을 누르면 상세 정보가 표시됩니다"
  },
  "判断置信度": {
    "zh-TW": "判斷信心度",
    "en": "Judgment confidence",
    "ja": "判断の確信度",
    "es": "Confianza del juicio",
    "ko": "판단 확신도"
  },
  "所选判断概率": {
    "zh-TW": "所選判斷機率",
    "en": "Chosen judgment probability",
    "ja": "選んだ判断の確率",
    "es": "Probabilidad del juicio elegido",
    "ko": "선택한 판단의 확률"
  },
  "候选选项": {
    "zh-TW": "候選選項",
    "en": "Candidate options",
    "ja": "選択肢",
    "es": "Opciones candidatas",
    "ko": "후보 선택지"
  },
  "概率 · TOP 3": {
    "zh-TW": "機率 · TOP 3",
    "en": "Probability · TOP 3",
    "ja": "確率 · TOP 3",
    "es": "Probabilidad · TOP 3",
    "ko": "확률 · TOP 3"
  },
  "NOUL · 是 / 否": {
    "zh-TW": "NOUL · 是 / 否",
    "en": "NOUL · YES / NO",
    "ja": "NOUL · はい / いいえ",
    "es": "NOUL · SÍ / NO",
    "ko": "NOUL · 예 / 아니요"
  },
  "判断列表": {
    "zh-TW": "判斷列表",
    "en": "Judgment log",
    "ja": "判断の記録",
    "es": "Registro de juicios",
    "ko": "판단 기록"
  },
  "Jev的每次判断记录在这里": {
    "zh-TW": "Jev 的每次判斷記錄在這裡",
    "en": "Every Jev judgment is recorded here",
    "ja": "Jev の判断を一つずつここに記録します",
    "es": "Aquí se registra cada juicio de Jev",
    "ko": "Jev의 모든 판단이 여기에 기록됩니다"
  },
  "访问 Dullblade 的 GitHub 主页": {
    "zh-TW": "造訪 Dullblade 的 GitHub 首頁",
    "en": "Visit Dullblade on GitHub",
    "ja": "Dullblade の GitHub を開く",
    "es": "Visita el GitHub de Dullblade",
    "ko": "Dullblade의 GitHub 방문"
  },
  "个位": {
    "zh-TW": "個位",
    "en": "ones",
    "ja": "一の位",
    "es": "unidades",
    "ko": "일의 자리"
  },
  "十位": {
    "zh-TW": "十位",
    "en": "tens",
    "ja": "十の位",
    "es": "decenas",
    "ko": "십의 자리"
  },
  "百位": {
    "zh-TW": "百位",
    "en": "hundreds",
    "ja": "百の位",
    "es": "centenas",
    "ko": "백의 자리"
  },
  "千位": {
    "zh-TW": "千位",
    "en": "thousands",
    "ja": "千の位",
    "es": "millares",
    "ko": "천의 자리"
  },
  "万位": {
    "zh-TW": "萬位",
    "en": "ten-thousands",
    "ja": "万の位",
    "es": "decenas de millar",
    "ko": "만의 자리"
  },
  "十万位": {
    "zh-TW": "十萬位",
    "en": "hundred-thousands",
    "ja": "十万の位",
    "es": "centenas de millar",
    "ko": "십만의 자리"
  },
  "百万位": {
    "zh-TW": "百萬位",
    "en": "millions",
    "ja": "百万の位",
    "es": "millones",
    "ko": "백만의 자리"
  },
  "千万位": {
    "zh-TW": "千萬位",
    "en": "ten-millions",
    "ja": "千万の位",
    "es": "decenas de millón",
    "ko": "천만의 자리"
  },
  "亿位": {
    "zh-TW": "億位",
    "en": "hundred-millions",
    "ja": "億の位",
    "es": "centenas de millón",
    "ko": "억의 자리"
  },
  "10^{p} 位": {
    "zh-TW": "10^{p} 位",
    "en": "10^{p} place",
    "ja": "10^{p} の位",
    "es": "posición 10^{p}",
    "ko": "10^{p} 자리"
  },
  "符号判断": {
    "zh-TW": "符號判斷",
    "en": "Sign judgment",
    "ja": "符号の判断",
    "es": "Juicio del signo",
    "ko": "부호 판단"
  },
  "{place}判断": {
    "zh-TW": "{place}判斷",
    "en": "Digit: {place}",
    "ja": "{place}の判断",
    "es": "Dígito: {place}",
    "ko": "{place} 판단"
  },
  "候选 {n}": {
    "zh-TW": "候選 {n}",
    "en": "Candidate {n}",
    "ja": "候補 {n}",
    "es": "Candidato {n}",
    "ko": "후보 {n}"
  },
  "向零截断后的整数是否为负数？": {
    "zh-TW": "朝零截斷後的整數是否為負數？",
    "en": "Is the integer negative after truncation toward zero?",
    "ja": "ゼロ方向に切り捨てた整数は負数ですか？",
    "es": "¿Es negativo el entero truncado hacia cero?",
    "ko": "0 방향으로 버림한 정수가 음수인가요?"
  },
  "绝对值的{place}是哪一位数字，还是已经结束？": {
    "zh-TW": "絕對值的{place}是哪一位數字，還是已經結束？",
    "en": "Which digit is in the {place} place of the absolute value, or has it ended?",
    "ja": "絶対値の{place}の数字は何ですか？それとも、もう桁がありませんか？",
    "es": "¿Qué dígito ocupa la posición de {place} del valor absoluto, o ya terminó?",
    "ko": "절댓값의 {place} 숫자는 무엇인가요? 아니면 더 이상 자릿수가 없나요?"
  },
  "{n} 是否大于结果的绝对值？": {
    "zh-TW": "{n} 是否大於結果的絕對值？",
    "en": "Is {n} greater than the absolute result?",
    "ja": "{n} は結果の絶対値より大きいですか？",
    "es": "¿Es {n} mayor que el valor absoluto del resultado?",
    "ko": "{n}은 결과의 절댓값보다 큰가요?"
  },
  "{n} 是否等于结果的绝对值？": {
    "zh-TW": "{n} 是否等於結果的絕對值？",
    "en": "Is {n} equal to the absolute result?",
    "ja": "{n} は結果の絶対値と等しいですか？",
    "es": "¿Es {n} igual al valor absoluto del resultado?",
    "ko": "{n}은 결과의 절댓값과 같은가요?"
  },
  "预测中": {
    "zh-TW": "預測中",
    "en": "Predicting",
    "ja": "予測中",
    "es": "Prediciendo",
    "ko": "예측 중"
  },
  "第 {n} 步 · {title}": {
    "zh-TW": "第 {n} 步 · {title}",
    "en": "Step {n} · {title}",
    "ja": "ステップ {n} · {title}",
    "es": "Paso {n} · {title}",
    "ko": "{n}단계 · {title}"
  },
  "是": {
    "zh-TW": "是",
    "en": "Yes",
    "ja": "はい",
    "es": "Sí",
    "ko": "예"
  },
  "否": {
    "zh-TW": "否",
    "en": "No",
    "ja": "いいえ",
    "es": "No",
    "ko": "아니요"
  },
  "大了": {
    "zh-TW": "太大",
    "en": "Too high",
    "ja": "大きい",
    "es": "Mayor",
    "ko": "큼"
  },
  "小了": {
    "zh-TW": "太小",
    "en": "Too low",
    "ja": "小さい",
    "es": "Menor",
    "ko": "작음"
  },
  "首次错误": {
    "zh-TW": "首次錯誤",
    "en": "First error",
    "ja": "最初の誤り",
    "es": "Primer error",
    "ko": "첫 오류"
  },
  "判断正确": {
    "zh-TW": "判斷正確",
    "en": "Correct judgment",
    "ja": "正しい判断",
    "es": "Juicio correcto",
    "ko": "올바른 판단"
  },
  "判断错误": {
    "zh-TW": "判斷錯誤",
    "en": "Incorrect judgment",
    "ja": "誤った判断",
    "es": "Juicio incorrecto",
    "ko": "잘못된 판단"
  },
  "正确选项：{option}": {
    "zh-TW": "正確選項：{option}",
    "en": "Correct option: {option}",
    "ja": "正しい選択肢：{option}",
    "es": "Opción correcta: {option}",
    "ko": "올바른 선택지: {option}"
  },
  "Noul 无独立置信度；概率 ≥ 50% 判为“是”。": {
    "zh-TW": "Noul 無獨立信心度；機率 ≥ 50% 判為「是」。",
    "en": "Noul has no separate confidence score; probability ≥ 50% means “Yes”.",
    "ja": "Noul に独立した確信度はありません。確率 50% 以上を「はい」とします。",
    "es": "Noul no tiene una confianza independiente; una probabilidad ≥ 50 % se interpreta como «Sí».",
    "ko": "Noul에는 별도 확신도가 없습니다. 확률이 50% 이상이면 ‘예’로 판단합니다."
  },
  "置信度不等于正确率。": {
    "zh-TW": "信心度不等於正確率。",
    "en": "Confidence is not accuracy.",
    "ja": "確信度は正答率ではありません。",
    "es": "La confianza no equivale a la precisión.",
    "ko": "확신도가 정답률을 의미하지는 않습니다."
  },
  "第 {n} 步 {title} {choice}，查看详情": {
    "zh-TW": "第 {n} 步 {title} {choice}，查看詳情",
    "en": "Step {n}, {title}, {choice}. View details",
    "ja": "ステップ {n}、{title}、{choice}。詳細を表示",
    "es": "Paso {n}, {title}, {choice}. Ver detalles",
    "ko": "{n}단계, {title}, {choice}. 상세 보기"
  },
  "符号": {
    "zh-TW": "符號",
    "en": "Sign",
    "ja": "符号",
    "es": "Signo",
    "ko": "부호"
  },
  "终止": {
    "zh-TW": "終止",
    "en": "End",
    "ja": "終了",
    "es": "Fin",
    "ko": "종료"
  },
  "空区间": {
    "zh-TW": "空區間",
    "en": "Empty range",
    "ja": "空の範囲",
    "es": "Rango vacío",
    "ko": "빈 범위"
  },
  "逐项确认最终候选": {
    "zh-TW": "逐項確認最終候選",
    "en": "Check each final candidate",
    "ja": "最終候補を一つずつ確認",
    "es": "Comprobar cada candidato final",
    "ko": "최종 후보 개별 확인"
  },
  "独立判断正负": {
    "zh-TW": "獨立判斷正負",
    "en": "Determine the sign separately",
    "ja": "符号は個別に判断",
    "es": "Determinar el signo por separado",
    "ko": "부호를 별도로 판단"
  },
  "从右向左 · 第 {n} 位": {
    "zh-TW": "從右向左 · 第 {n} 位",
    "en": "Right to left · Digit {n}",
    "ja": "右から左 · {n} 桁目",
    "es": "De derecha a izquierda · Dígito {n}",
    "ko": "오른쪽에서 왼쪽 · {n}번째 자리"
  },
  "正确": {
    "zh-TW": "正確",
    "en": "Correct",
    "ja": "正解",
    "es": "Correcto",
    "ko": "정답"
  },
  "错误": {
    "zh-TW": "錯誤",
    "en": "Wrong",
    "ja": "不正解",
    "es": "Incorrecto",
    "ko": "오답"
  },
  "对照整数：{n}": {
    "zh-TW": "對照整數：{n}",
    "en": "Reference integer: {n}",
    "ja": "比較対象の整数：{n}",
    "es": "Entero de referencia: {n}",
    "ko": "비교할 정수: {n}"
  },
  "正在判断候选数与结果符号…": {
    "zh-TW": "正在判斷候選數與結果符號…",
    "en": "Judging the candidate and result sign…",
    "ja": "候補の数と結果の符号を判断中…",
    "es": "Evaluando el candidato y el signo del resultado…",
    "ko": "후보 숫자와 결과 부호 판단 중…"
  },
  "正在判断个位与结果符号…": {
    "zh-TW": "正在判斷個位與結果符號…",
    "en": "Predicting the ones digit and result sign…",
    "ja": "一の位と結果の符号を予測中…",
    "es": "Prediciendo las unidades y el signo del resultado…",
    "ko": "일의 자리와 결과 부호 예측 중…"
  },
  "{n} 次判断": {
    "zh-TW": "{n} 次判斷",
    "en": "{n} judgments",
    "ja": "{n} 回の判断",
    "es": "{n} juicios",
    "ko": "판단 {n}회"
  },
  "已收到终止符，停止向左预测": {
    "zh-TW": "已收到終止符，停止向左預測",
    "en": "END received; no more digits to predict",
    "ja": "END を受信。左への予測を終了",
    "es": "END recibido; termina la predicción de dígitos",
    "ko": "END 수신, 왼쪽 자릿수 예측 종료"
  },
  "已得到{place}，正在判断{next}…": {
    "zh-TW": "已得到{place}，正在判斷{next}…",
    "en": "Got {place}; predicting {next}…",
    "ja": "{place}を取得。{next}を予測中…",
    "es": "Obtenido: {place}; prediciendo: {next}…",
    "ko": "{place} 예측 완료, {next} 판단 중…"
  },
  "无剩余候选": {
    "zh-TW": "無剩餘候選",
    "en": "no candidates remain",
    "ja": "候補なし",
    "es": "no quedan candidatos",
    "ko": "남은 후보 없음"
  },
  "继续缩小范围": {
    "zh-TW": "繼續縮小範圍",
    "en": "narrowing the range",
    "ja": "範囲を絞り込み中",
    "es": "acotando el rango",
    "ko": "범위를 좁히는 중"
  },
  "{n} → Jev 判断{choice}，{next}…": {
    "zh-TW": "{n} → Jev 判斷{choice}，{next}…",
    "en": "{n} → Jev says {choice}; {next}…",
    "ja": "{n} → Jev の判断：{choice}、{next}…",
    "es": "{n} → Jev dice {choice}; {next}…",
    "ko": "{n} → Jev 판단: {choice}, {next}…"
  },
  "逐项确认候选": {
    "zh-TW": "逐項確認候選",
    "en": "Checking candidates individually",
    "ja": "候補を個別に確認",
    "es": "Comprobando cada candidato",
    "ko": "후보 개별 확인 중"
  },
  "候选 {n} → {choice}": {
    "zh-TW": "候選 {n} → {choice}",
    "en": "Candidate {n} → {choice}",
    "ja": "候補 {n} → {choice}",
    "es": "Candidato {n} → {choice}",
    "ko": "후보 {n} → {choice}"
  },
  "首次错误：第 {n} 步 · {title} · 点击查看 →": {
    "zh-TW": "首次錯誤：第 {n} 步 · {title} · 點擊查看 →",
    "en": "First error: step {n} · {title} · View →",
    "ja": "最初の誤り：ステップ {n} · {title} · 詳細 →",
    "es": "Primer error: paso {n} · {title} · Ver →",
    "ko": "첫 오류: {n}단계 · {title} · 상세 보기 →"
  },
  "Jev 在个位提前终止，未产生整数结果": {
    "zh-TW": "Jev 在個位提前終止，未產生整數結果",
    "en": "Jev stopped at the ones digit without producing an integer",
    "ja": "Jev が一の位で終了し、整数を生成できませんでした",
    "es": "Jev se detuvo en las unidades sin producir un entero",
    "ko": "Jev가 일의 자리에서 종료해 정수 결과가 없습니다"
  },
  "多个候选被判为“是”：{values}": {
    "zh-TW": "多個候選被判為「是」：{values}",
    "en": "Multiple candidates received “Yes”: {values}",
    "ja": "複数の候補が「はい」：{values}",
    "es": "Varios candidatos recibieron «Sí»: {values}",
    "ko": "여러 후보가 ‘예’로 판단됨: {values}"
  },
  "没有候选被判为“是”，无法确定答案": {
    "zh-TW": "沒有候選被判為「是」，無法確定答案",
    "en": "No candidate received “Yes”; no answer found",
    "ja": "「はい」の候補がなく、答えを特定できません",
    "es": "Ningún candidato recibió «Sí»; no se pudo determinar la respuesta",
    "ko": "‘예’로 판단된 후보가 없어 답을 정할 수 없습니다"
  },
  "判断结束 · 无唯一有效结果": {
    "zh-TW": "判斷結束 · 無唯一有效結果",
    "en": "Finished · No unique valid result",
    "ja": "判断終了 · 一意の有効な結果なし",
    "es": "Finalizado · Sin resultado válido único",
    "ko": "판단 종료 · 유일한 유효 결과 없음"
  },
  "无有效结果": {
    "zh-TW": "無有效結果",
    "en": "No valid result",
    "ja": "有効な結果なし",
    "es": "Sin resultado válido",
    "ko": "유효 결과 없음"
  },
  "无法确定唯一答案": {
    "zh-TW": "無法確定唯一答案",
    "en": "No unique answer",
    "ja": "答えを一つに特定できません",
    "es": "Sin respuesta única",
    "ko": "답을 하나로 정할 수 없음"
  },
  "判断完成 · 已检查所有最终候选": {
    "zh-TW": "判斷完成 · 已檢查所有最終候選",
    "en": "Done · All final candidates checked",
    "ja": "完了 · 最終候補をすべて確認済み",
    "es": "Completado · Todos los candidatos finales comprobados",
    "ko": "완료 · 최종 후보 모두 확인됨"
  },
  "预测完成 · 已由终止符结束": {
    "zh-TW": "預測完成 · 已由終止符結束",
    "en": "Prediction complete · END received",
    "ja": "予測完了 · END で終了",
    "es": "Predicción completa · END recibido",
    "ko": "예측 완료 · END로 종료"
  },
  "整数一致": {
    "zh-TW": "整數一致",
    "en": "Integers match",
    "ja": "整数が一致",
    "es": "Enteros iguales",
    "ko": "정수 일치"
  },
  "结果不同": {
    "zh-TW": "結果不同",
    "en": "Results differ",
    "ja": "結果が不一致",
    "es": "Resultados distintos",
    "ko": "결과 불일치"
  },
  "Jev 整数结果：{n} · {audit}": {
    "zh-TW": "Jev 整數結果：{n} · {audit}",
    "en": "Jev integer: {n} · {audit}",
    "ja": "Jev の整数結果：{n} · {audit}",
    "es": "Entero de Jev: {n} · {audit}",
    "ko": "Jev 정수 결과: {n} · {audit}"
  },
  "所有判断均正确": {
    "zh-TW": "所有判斷均正確",
    "en": "All judgments correct",
    "ja": "すべての判断が正解",
    "es": "Todos los juicios correctos",
    "ko": "모든 판단이 올바름"
  },
  "首次错误在第 {n} 步": {
    "zh-TW": "首次錯誤在第 {n} 步",
    "en": "First error at step {n}",
    "ja": "最初の誤りはステップ {n}",
    "es": "Primer error en el paso {n}",
    "ko": "첫 오류: {n}단계"
  },
  "JEV 最终整数": {
    "zh-TW": "JEV 最終整數",
    "en": "JEV FINAL INTEGER",
    "ja": "JEV の最終整数",
    "es": "ENTERO FINAL DE JEV",
    "ko": "JEV 최종 정수"
  },
  "测试已停止": {
    "zh-TW": "測試已停止",
    "en": "Run stopped",
    "ja": "テストを停止しました",
    "es": "Prueba detenida",
    "ko": "테스트 중지됨"
  },
  "预测未完成": {
    "zh-TW": "預測未完成",
    "en": "Prediction incomplete",
    "ja": "予測未完了",
    "es": "Predicción incompleta",
    "ko": "예측 미완료"
  },
  "未完成，已保留现有判断。": {
    "zh-TW": "未完成，已保留現有判斷。",
    "en": "Incomplete; existing judgments have been kept.",
    "ja": "未完了です。これまでの判断は保存されています。",
    "es": "Incompleto; se conservan los juicios existentes.",
    "ko": "미완료. 기존 판단은 유지됩니다."
  },
  "未完成": {
    "zh-TW": "未完成",
    "en": "Incomplete",
    "ja": "未完了",
    "es": "Incompleto",
    "ko": "미완료"
  },
  "正在连接 Jev…": {
    "zh-TW": "正在連線 Jev…",
    "en": "Connecting to Jev…",
    "ja": "Jev に接続中…",
    "es": "Conectando con Jev…",
    "ko": "Jev 연결 중…"
  },
  "服务暂时不可用，请稍后重试。": {
    "zh-TW": "服務暫時無法使用，請稍後重試。",
    "en": "Service unavailable. Please try again later.",
    "ja": "サービスを利用できません。後ほど再試行してください。",
    "es": "Servicio no disponible. Inténtalo más tarde.",
    "ko": "서비스를 사용할 수 없습니다. 나중에 다시 시도하세요."
  },
  "请求失败": {
    "zh-TW": "請求失敗",
    "en": "Request failed",
    "ja": "リクエストに失敗しました",
    "es": "Solicitud fallida",
    "ko": "요청 실패"
  },
  "服务返回了无效结果。": {
    "zh-TW": "服務傳回了無效結果。",
    "en": "The service returned an invalid result.",
    "ja": "サービスから無効な結果が返されました。",
    "es": "El servicio devolvió un resultado inválido.",
    "ko": "서비스가 유효하지 않은 결과를 반환했습니다."
  },
  "连接中断，未收到完整结果。": {
    "zh-TW": "連線中斷，未收到完整結果。",
    "en": "Connection lost before the full result arrived.",
    "ja": "結果の受信が完了する前に接続が切れました。",
    "es": "Se perdió la conexión antes de recibir el resultado completo.",
    "ko": "전체 결과를 받기 전에 연결이 끊어졌습니다."
  },
  "本轮请求超时，请稍后重试。": {
    "zh-TW": "本輪請求逾時，請稍後重試。",
    "en": "This request timed out. Please try again.",
    "ja": "リクエストがタイムアウトしました。再試行してください。",
    "es": "La solicitud agotó el tiempo de espera. Inténtalo de nuevo.",
    "ko": "요청 시간이 초과되었습니다. 다시 시도하세요."
  },
  "正在停止，等待当前请求结束后不再发起下一次判断…": {
    "zh-TW": "正在停止，等待目前請求結束後不再發起下一次判斷…",
    "en": "Stopping after the current request finishes…",
    "ja": "現在のリクエストが完了したら停止します…",
    "es": "Se detendrá al terminar la solicitud actual…",
    "ko": "현재 요청이 끝나면 중지합니다…"
  },
  "服务未连接": {
    "zh-TW": "服務未連線",
    "en": "Service disconnected",
    "ja": "サービス未接続",
    "es": "Servicio desconectado",
    "ko": "서비스 연결 안 됨"
  },
  "无法连接计算服务，请刷新页面或稍后重试。": {
    "zh-TW": "無法連線計算服務，請重新整理頁面或稍後重試。",
    "en": "Cannot connect to the calculator. Reload or try again later.",
    "ja": "計算サービスに接続できません。再読み込みするか、後ほど再試行してください。",
    "es": "No se puede conectar con la calculadora. Recarga o inténtalo más tarde.",
    "ko": "계산 서비스에 연결할 수 없습니다. 새로고침하거나 나중에 다시 시도하세요."
  },
  "请先填写自己的 TypeSafe API Key。": {
    "zh-TW": "請先填寫自己的 TypeSafe API Key。",
    "en": "Enter your TypeSafe API Key first.",
    "ja": "先に TypeSafe API Key を入力してください。",
    "es": "Introduce primero tu API Key de TypeSafe.",
    "ko": "먼저 TypeSafe API Key를 입력하세요."
  },
  "API Key 格式不正确，请检查空格或换行。": {
    "zh-TW": "API Key 格式不正確，請檢查空格或換行。",
    "en": "Invalid API Key format. Check for spaces or line breaks.",
    "ja": "API Key の形式が正しくありません。空白や改行を確認してください。",
    "es": "Formato de API Key inválido. Revisa los espacios o saltos de línea.",
    "ko": "API Key 형식이 올바르지 않습니다. 공백이나 줄바꿈을 확인하세요."
  },
  "TypeSafe 拒绝了本地环境 Key（401）。请检查 TYPESAFE_API_KEY 或 .env，修改后重启本地服务。": {
    "zh-TW": "TypeSafe 拒絕了本機環境 Key（401）。請檢查 TYPESAFE_API_KEY 或 .env，修改後重啟本機服務。",
    "en": "TypeSafe rejected the local key (401). Check TYPESAFE_API_KEY or .env, then restart the service.",
    "ja": "TypeSafe がローカル Key を拒否しました（401）。TYPESAFE_API_KEY または .env を確認し、サービスを再起動してください。",
    "es": "TypeSafe rechazó la key local (401). Revisa TYPESAFE_API_KEY o .env y reinicia el servicio.",
    "ko": "TypeSafe가 로컬 Key를 거부했습니다(401). TYPESAFE_API_KEY 또는 .env를 확인하고 서비스를 재시작하세요."
  },
  "TypeSafe 拒绝了此 API Key（401）。请检查是否复制完整，或重新填写。": {
    "zh-TW": "TypeSafe 拒絕了此 API Key（401）。請檢查是否複製完整，或重新填寫。",
    "en": "TypeSafe rejected this API Key (401). Check that you copied the full key or enter it again.",
    "ja": "TypeSafe が API Key を拒否しました（401）。完全にコピーされているか確認するか、再入力してください。",
    "es": "TypeSafe rechazó esta API Key (401). Comprueba que esté completa o introdúcela de nuevo.",
    "ko": "TypeSafe가 API Key를 거부했습니다(401). 전체를 복사했는지 확인하거나 다시 입력하세요."
  },
  "TypeSafe 拒绝访问（403）。请检查此 Key 的权限或账户状态。": {
    "zh-TW": "TypeSafe 拒絕存取（403）。請檢查此 Key 的權限或帳戶狀態。",
    "en": "TypeSafe denied access (403). Check the key permissions or account status.",
    "ja": "TypeSafe がアクセスを拒否しました（403）。Key の権限やアカウント状態を確認してください。",
    "es": "TypeSafe denegó el acceso (403). Revisa los permisos de la key o el estado de la cuenta.",
    "ko": "TypeSafe가 접근을 거부했습니다(403). Key 권한이나 계정 상태를 확인하세요."
  },
  "无法完成 TypeSafe 请求，请稍后重试。": {
    "zh-TW": "無法完成 TypeSafe 請求，請稍後重試。",
    "en": "Could not complete the TypeSafe request. Try again later.",
    "ja": "TypeSafe のリクエストを完了できませんでした。後ほど再試行してください。",
    "es": "No se pudo completar la solicitud a TypeSafe. Inténtalo más tarde.",
    "ko": "TypeSafe 요청을 완료하지 못했습니다. 나중에 다시 시도하세요."
  },
  "算式、范围或预测进度无效，请检查输入后重新计算。": {
    "zh-TW": "算式、範圍或預測進度無效，請檢查輸入後重新計算。",
    "en": "Invalid expression, range or progress. Check your input and start again.",
    "ja": "式、範囲、または予測の進行状態が無効です。入力を確認してやり直してください。",
    "es": "Operación, rango o progreso inválidos. Revisa los datos y vuelve a calcular.",
    "ko": "수식, 범위 또는 진행 상태가 유효하지 않습니다. 입력을 확인하고 다시 계산하세요."
  },
  "本轮预测未完成，请稍后重试。": {
    "zh-TW": "本輪預測未完成，請稍後重試。",
    "en": "This prediction did not finish. Try again later.",
    "ja": "今回の予測は完了しませんでした。後ほど再試行してください。",
    "es": "Esta predicción no se completó. Inténtalo más tarde.",
    "ko": "예측을 완료하지 못했습니다. 나중에 다시 시도하세요."
  },
  "仅允许当前网站调用。": {
    "zh-TW": "僅允許目前網站呼叫。",
    "en": "Only requests from this site are allowed.",
    "ja": "このサイトからのリクエストのみ許可されています。",
    "es": "Solo se permiten solicitudes desde este sitio.",
    "ko": "현재 사이트의 요청만 허용됩니다."
  },
  "需要 JSON 请求。": {
    "zh-TW": "需要 JSON 請求。",
    "en": "A JSON request is required.",
    "ja": "JSON リクエストが必要です。",
    "es": "Se requiere una solicitud JSON.",
    "ko": "JSON 요청이 필요합니다."
  },
  "已预测 {n} 位，下一位仍未返回终止符。已停止，本次没有完整结果。": {
    "zh-TW": "已預測 {n} 位，下一位仍未傳回終止符。已停止，本次沒有完整結果。",
    "en": "Predicted {n} digits without END on the next digit. Stopped without a complete result.",
    "ja": "{n} 桁を予測しても次の桁で END が返らなかったため、未完了のまま停止しました。",
    "es": "Se predijeron {n} dígitos sin END en el siguiente. Se detuvo sin un resultado completo.",
    "ko": "{n}자리를 예측했지만 다음 자리에도 END가 없어 중지했습니다. 완성된 결과가 없습니다."
  },
  "已达到 {n} 次区间判断上限，停止本次测试。": {
    "zh-TW": "已達到 {n} 次區間判斷上限，停止本次測試。",
    "en": "Reached the limit of {n} range judgments. Run stopped.",
    "ja": "範囲判断の上限 {n} 回に達したため停止しました。",
    "es": "Se alcanzó el límite de {n} juicios de rango. Prueba detenida.",
    "ko": "구간 판단 상한 {n}회에 도달하여 중지했습니다."
  },
  "网络连接失败，请检查网络后重试。": {
    "zh-TW": "網路連線失敗，請檢查網路後重試。",
    "en": "Network connection failed. Check your connection and try again.",
    "ja": "ネットワーク接続に失敗しました。接続を確認して再試行してください。",
    "es": "Falló la conexión de red. Comprueba la conexión e inténtalo de nuevo.",
    "ko": "네트워크 연결에 실패했습니다. 연결을 확인하고 다시 시도하세요."
  },
  "语言 / Language": {
    "zh-TW": "語言 / Language",
    "en": "Language",
    "ja": "言語 / Language",
    "es": "Idioma / Language",
    "ko": "언어 / Language"
  }
};
const supportedLanguages = ['zh-CN', 'zh-TW', 'en', 'ja', 'es', 'ko'];
function initialLanguage() {
  try { const saved = localStorage.getItem('jev-language'); if (supportedLanguages.includes(saved)) return saved; } catch (_) {}
  const language = navigator.language || 'zh-CN';
  if (/^zh/i.test(language)) return /TW|HK|MO|Hant/i.test(language) ? 'zh-TW' : 'zh-CN';
  return supportedLanguages.find((value) => language.startsWith(value)) || 'zh-CN';
}
let locale = initialLanguage();
function t(key, values = {}) {
  if (key === undefined || key === null) return '';
  return (messages[key]?.[locale] || String(key)).replace(/\{(\w+)\}/g, (match, name) => values[name] ?? match);
}
// Capture original static copy once, before the app starts updating live text.
const staticCopy = [];
const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
while (walker.nextNode()) {
  const element = walker.currentNode, source = element.textContent.trim();
  if (messages[source]) staticCopy.push({element, source});
}
const staticAttributes = [];
document.querySelectorAll('[aria-label], [placeholder], meta[name="description"]').forEach((element) => {
  for (const name of ['aria-label', 'placeholder', 'content']) {
    const source = element.getAttribute(name);
    if (messages[source]) staticAttributes.push({element, name, source});
  }
});
function translatePage() {
  document.documentElement.lang = locale;
  staticCopy.forEach(({element, source}) => { if (element.isConnected) element.textContent = t(source); });
  staticAttributes.forEach(({element, name, source}) => element.setAttribute(name, t(source)));
}
function errorText(message) {
  const limits = [
    [/^已预测 (\d+) 位，下一位仍未返回终止符。已停止，本次没有完整结果。$/, '已预测 {n} 位，下一位仍未返回终止符。已停止，本次没有完整结果。'],
    [/^已达到 (\d+) 次区间判断上限，停止本次测试。$/, '已达到 {n} 次区间判断上限，停止本次测试。']
  ];
  for (const [pattern, key] of limits) {
    const match = String(message).match(pattern);
    if (match) return t(key, {n: match[1]});
  }
  return t(message);
}
