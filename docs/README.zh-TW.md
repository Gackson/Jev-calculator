# jev-olympics

[English](../README.md) · [简体中文](README.zh-CN.md) · **繁體中文** · [日本語](README.ja.md) · [Español](README.es.md) · [한국어](README.ko.md)

Let Jev do math, chat, and draw things—in a probabilistic way.

讓 Jev 以機率的方式算數、聊天和畫畫。[線上體驗](https://jev-olympics.vercel.app/)

## 可以做什麼

- **Calculator**：用 Choice 從個位往左選數字，或用 Noul 反覆判斷「相等／較大／較小」，尋找整數答案，並與精確計算結果對照。
- **Chat**：逐字元或逐詞產生英文回答。單詞模式有 249 個常用英文詞、`. , ? !`、換行和結束，共 255 個選項；詞間自動加空格。
- **Canvas**：在 4×4 至 14×14 黑白點陣上，使用逐格掃描、座標選擇或圓珠筆模式畫圖。
- **Notes**：為每次判斷加入共用指令或鼓勵。Notes 優先於內建指令，但輸出仍限於當次判斷提供的選項。

點擊數字、字元、單詞或繪圖判斷，可查看機率、confidence（如有）、模型、耗時和 token 用量。「查看完整輸入」預設折疊，展開顯示該輪 JSON，不含密鑰。模型預測不會被修正。介面支援六種語言；切換語言不會翻譯模型指令或輸出。重新整理會清除對話、畫布、Notes 和個人 Key。

## 共享 Key 與 BYOK

正式站點預設使用服務端共享 Key，不必填 Key 即可試用。右上角可輸入自己的 TypeSafe Key，優先使用個人額度；清除後恢復共享 Key。個人 Key 無效時不會偷偷改用站點額度。

個人 Key 可在 [TypeSafe 控制台](https://console.typesafe.ai/keys) 取得。瀏覽器僅於目前頁面記憶體保存個人 Key，透過 HTTPS 傳給後端，再呼叫固定的 TypeSafe 端點。共享 Key 不會傳給瀏覽器。

## 本地執行

Python 3.9+，TypeSafe 模式不需額外依賴。在專案根目錄執行：

```bash
python3 calculator.py
```

開啟 <http://127.0.0.1:8765>。可用 `--port 8766` 更換埠號。預設模型為 `jev-1.13.0`。

可在根目錄的 `.env` 設定 `TYPESAFE_API_KEY`。本地優先序為：程序環境變數 → `.env` → 網頁 BYOK；修改環境 Key 後需重新啟動。本地環境 Key 優先於網頁 Key，與正式站點的個人 Key 優先規則不同。不要提交真實密鑰。

## Vercel 部署

將 `TYPESAFE_API_KEY` 以 **Secret** 類型加入 **Production**，再部署：

```bash
vercel env add TYPESAFE_API_KEY production --sensitive
vercel deploy --prod
```

透過提示輸入密鑰，不要把值放進命令參數或原始碼。只有 `VERCEL_ENV=production` 才啟用共享 Key；預覽環境仍使用 BYOK。雲端不讀 `.env` 或本地 Laya 權重。移除變數並重新部署即可關閉共享存取。

公開試用會消耗站點所有者的 TypeSafe 額度，由所有者在控制台管理。應用沒有跨執行個體的全域額度或速率限制；同源檢查無法阻擋腳本直接呼叫。

## 停止規則與開發

Chat 字元模式遇到兩個連續空格或五個相同字元即停止；單詞模式連續五次選到同一詞或標記也停止。字元上限為 64 / 128 / 256，單詞模式步數上限為 32 / 64 / 128。達到上限或重複停止會標示未完成，不偽造 `END`。繪圖也有邊界、重複與步數限制，停止時保留部分結果。

測試集中於 `tests/`，不呼叫付費模型 API：

```bash
python3 -m unittest discover -s tests -t . -v
python3 -m unittest tests.test_chat_words -v
```

前端位於 `calculator_ui/`，雲端入口位於 `api/`，翻譯位於 `docs/`。可選的本地 Laya 不需要 API Key，也不會在失敗時退回雲端。完整演算法、Laya 安裝和專案結構請參閱 [英文文件](../README.md)。
