# jev-olympics

[English](../README.md) · [简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md) · **日本語** · [Español](README.es.md) · [한국어](README.ko.md)

Let Jev do math, chat, and draw things—in a probabilistic way.

[競技場へ](https://jev-olympics.vercel.app/)

競技は三つ。メダルはなし。失敗には一件ずつ詳しい事故報告書が付きます。

TypeSafe の Jev モデルで遊ぶ、小さな実験場です。完成した答えを求める代わりに、計算、会話、お絵描きを一つずつの選択で進めてもらいます。目的は遊ぶこと。実用性が生まれたら、それは想定外の副作用です。

## 競技種目

- **Calculator**：Choice で一の位から数字を選ぶか、Noul で等しいか、大小関係はどうかを判定して整数を探します。隣では正確な計算も行うので、がっかりした量も測れます。
- **Chat**：英語の回答を一文字ずつ、または一単語ずつ作ります。単語モードは日常的な英単語 249 個、`. , ? !`、`NEWLINE`、`END` の計 255 選択肢。単語間の空白は自動挿入されます。
- **Canvas**：4×4〜14×14 の白黒グリッドで、画素の順次走査、座標選択、ボールペンの移動によって描画します。指示したものに見えるかどうかも実験のうちです。
- **Notes**：各判定に指示、背景情報、励ましを追加します。利用可能な選択肢の範囲で、組み込み指示より優先されます。

## 事故現場を調べる

数字、文字、単語、描画の判定をクリックすると、確率、confidence（ある場合）、モデル、処理時間、トークン使用量が見られます。既定で折りたたまれた **入力全体を表示** を開くと、認証情報を除いた実際の JSON を確認できます。

Jev の選択はそのまま残します。模範解答を見てからこっそり答案を直すことはありません。Calculator は最初の誤判定を示し、Chat と Canvas は未完成の現場を保存します。

UI と README は同じ 6 言語に対応しています。言語を切り替えてもモデルの指示や出力は翻訳しません。会話、描画、Notes はページのメモリだけに保存され、再読み込みで消えます。

## 競技規則

- **Calculator**：整数、算術演算子、括弧に対応。正確な有理数計算で参照値を求め、比較時にはゼロ方向に切り捨てた整数を使います。Choice は最大 24 桁と最後の終了確認、Noul は範囲を広げた後に乱数または中央値で探索します。Choice の文脈に過去の予測を含めるか選べます。
- **Chat**：各ステップにメッセージ、回答の途中経過、最大 3 往復の履歴、Notes を渡します。単語モードでは過去の選択も渡します。文字モードは空白が 2 回連続、または同じ文字が 5 回連続すると停止。単語モードは同じ選択が 5 回連続すると停止します。上限は 64 / 128 / 256 文字、または句読点や制御記号を含む 32 / 64 / 128 回の単語モード判定です。反復や上限による停止は未完了と表示し、`END` に見せかけません。
- **Canvas**：列挙モードは画素を順番に走査し、モンテカルロは座標か `END` を選びます。ボールペンは開始点、方向、ペン上げ、`END` を選びます。境界、反復検査、ステップ上限で実験を有限に保ちます。
- **Notes**：実行開始時に固定し、各判定にそのまま送ります。途中では編集できません。Notes による予測の改善は保証されません。

## ローカル実行

Python 3.9 以上。TypeSafe 推論に追加の Python 依存関係はありません。プロジェクトのルートにある `.env` または環境変数で `TYPESAFE_API_KEY` を設定します。

```dotenv
TYPESAFE_API_KEY=your-typesafe-api-key
```

```bash
python3 calculator.py
```

<http://127.0.0.1:8765> を開きます。`--port 8766` でポート、`--model jev-latest` でモデルを変更できます。既定モデルは `jev-1.13.0`。サーバーは localhost だけで待ち受けます。設定変更後は再起動し、実際の認証情報を Git に入れないでください。

任意でローカル **Laya** 推論も利用できます。インストール、デプロイ、設定の詳細は [開発ガイド（英語）](development.md) を参照してください。

## 開発

```bash
python3 -m unittest discover -s tests -t . -v
python3 -m unittest tests.test_chat_words -v
node --check calculator_ui/app.js
```

テストはモデルの応答を模擬し、HTTP 統合テストはループバックポートを使います。CI は Python 3.9、3.12 とフロントエンドの JavaScript 構文を検証します。実験が動くかはテストしますが、Jev に常識が芽生えたかは対象外です。

| ディレクトリ | 内容 |
| --- | --- |
| `calculator_ui/` | UI と翻訳 |
| `api/` | Vercel 関数の入口 |
| `tests/` | 単体テストと HTTP 統合テスト |
| `docs/` | 翻訳された README と開発ガイド |

参考：[TypeSafe クイックスタート](https://docs.typesafe.ai/introduction/quickstart)、[Choice](https://docs.typesafe.ai/primitives/choice)、[HTTP API](https://docs.typesafe.ai/api)、[confidence](https://docs.typesafe.ai/confidence)。
