# jev-olympics

[English](../README.md) · [简体中文](README.zh-CN.md) · **繁體中文** · [日本語](README.ja.md) · [Español](README.es.md) · [한국어](README.ko.md)

Let Jev do math, chat, and draw things—in a probabilistic way.

[進入賽場](https://jev-olympics.vercel.app/)

三個項目，沒有獎牌。每次失誤都有一份詳細的事故報告。

這是一個由 TypeSafe Jev 模型驅動的小遊樂場。我們不直接索取完整答案，而是讓 Jev 一步一步做選擇，拼出計算結果、對話和圖畫。主要用途是好玩。如果產生了實用價值，那屬於意外事故。

## 比賽項目

- **Calculator**：用 Choice 從個位往左選擇數字，或用 Noul 判斷是否相等、大小關係，搜尋整數答案。旁邊同時執行真正的計算，讓失望也能量化。
- **Chat**：一個字元或一個單詞地拼出英文回答。單詞模式包含 249 個常用詞、四種標點 `. , ? !`、`NEWLINE` 和 `END`，共 255 項。詞間自動添加空格。
- **Canvas**：在 4×4 至 14×14 的黑白點陣上逐格掃描、選擇座標，或移動原子筆作畫。畫出來像不像描述，也是實驗的一部分。
- **Notes**：給每次判斷添加指令、背景或鼓勵。Notes 在可用選項範圍內優先於內建任務指令。

## 查看事故現場

點擊數字、字元、單詞或繪圖判斷，查看機率、confidence（如有）、模型、耗時和 token 用量。展開預設摺疊的 **查看完整輸入**，可以看到該輪實際送出的 JSON，不含認證資訊。

Jev 怎麼選，我們就怎麼留。不會看過答案後偷偷改考卷。Calculator 標出第一次錯誤判斷，Chat 和 Canvas 保留未完成的現場。

介面與 README 都支援六種語言；切換介面語言不會翻譯模型指令或輸出。對話、畫布和 Notes 只保存在頁面記憶體，重新整理後消失。

## 比賽規則

- **Calculator**：支援整數、算術運算子和括號。用精確有理數計算參考答案，比較時向零截斷為整數。Choice 最多輸出 24 位，再檢查一次終止符；Noul 先擴大搜尋區間，再隨機取數或取中位數。Choice 可選擇是否帶入之前的預測。
- **Chat**：每步帶上目前訊息、已產生文字、最多三輪歷史和 Notes；單詞模式還帶上之前的選擇。字元模式遇到兩個連續空格或五個相同字元停止；單詞模式連續五次選擇同一項停止。上限為 64 / 128 / 256 個字元，或 32 / 64 / 128 次單詞模式判斷，標點和控制標記也計入。因重複或上限停止會標示未完成，不偽裝成 `END`。
- **Canvas**：枚舉法依序走訪像素；蒙地卡羅法選擇座標或 `END`；原子筆選擇起點、方向、抬筆或 `END`。邊界、重複偵測和步數上限負責讓實驗有個盡頭。
- **Notes**：開始時固定本輪內容，每次判斷原樣送出，執行中不能修改。Notes 不保證能提高預測效果。

## 本地執行

Python 3.9+；TypeSafe 推理不需額外 Python 依賴。在專案根目錄的 `.env` 或環境變數中設定 `TYPESAFE_API_KEY`：

```dotenv
TYPESAFE_API_KEY=your-typesafe-api-key
```

```bash
python3 calculator.py
```

開啟 <http://127.0.0.1:8765>。用 `--port 8766` 修改連接埠，或用 `--model jev-latest` 修改模型；預設模型為 `jev-1.13.0`。服務只監聽本機。修改設定後重新啟動，不要將真實憑據提交到 Git。

也支援可選的本地 **Laya** 推理。安裝、部署和設定細節見[開發指南（英文）](development.md)。

## 開發

```bash
python3 -m unittest discover -s tests -t . -v
python3 -m unittest tests.test_chat_words -v
node --check calculator_ui/app.js
```

測試使用模擬模型回應，HTTP 整合測試會綁定本機連接埠。CI 檢查 Python 3.9、3.12 和前端 JavaScript 語法。測試保證實驗能跑，不保證 Jev 長出了常識。

| 目錄 | 內容 |
| --- | --- |
| `calculator_ui/` | 介面和翻譯 |
| `api/` | Vercel 函數入口 |
| `tests/` | 單元測試和 HTTP 整合測試 |
| `docs/` | 多語言 README 和開發指南 |

參考：[TypeSafe 快速開始](https://docs.typesafe.ai/introduction/quickstart)、[Choice](https://docs.typesafe.ai/primitives/choice)、[HTTP API](https://docs.typesafe.ai/api)、[confidence](https://docs.typesafe.ai/confidence)。
