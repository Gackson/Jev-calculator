# jev-olympics

[English](../README.md) · **简体中文** · [繁體中文](README.zh-TW.md) · [日本語](README.ja.md) · [Español](README.es.md) · [한국어](README.ko.md)

Let Jev do math, chat, and draw things—in a probabilistic way.

[进入赛场](https://jev-olympics.vercel.app/)

三个项目，没有奖牌。每次失误都有一份详细的事故报告。

这是一个由 TypeSafe Jev 模型驱动的小游乐场。我们不直接索要完整答案，而是让 Jev 一步一步做选择，拼出计算结果、对话和图画。主要用途是好玩。如果产生了实用价值，那属于意外事故。

## 比赛项目

- **Calculator**：用 Choice 从个位向左选择数字，或用 Noul 判断是否相等、大小关系，搜索整数答案。旁边同时运行真正的计算，让失望也可以量化。
- **Chat**：一个字符或一个单词地拼出英文回答。单词模式包含 249 个常用词、四种标点 `. , ? !`、`NEWLINE` 和 `END`，共 255 项。词间自动添加空格。
- **Canvas**：在 4×4 至 14×14 的黑白点阵上逐格扫描、选择坐标，或移动圆珠笔作画。画出来像不像描述，也是实验的一部分。
- **Notes**：给每次判断添加指令、背景或鼓励。Notes 在可用选项范围内优先于内置任务指令。

## 查看事故现场

点击数字、字符、单词或绘图判断，查看概率、confidence（如有）、模型、耗时和 token 用量。展开默认折叠的 **查看完整输入**，可以看到该轮实际发送的 JSON，不含认证信息。

Jev 怎么选，我们就怎么留。不会看过答案后偷偷改卷。Calculator 标出第一次错误判断，Chat 和 Canvas 保留未完成的现场。

界面与 README 都支持六种语言；切换界面语言不会翻译模型指令或输出。对话、画布和 Notes 只保存在页面内存，刷新后消失。

## 比赛规则

- **Calculator**：支持整数、算术运算符和括号。用精确有理数计算参考答案，比较时向零截断为整数。Choice 最多输出 24 位，再检查一次终止符；Noul 先扩大搜索区间，再随机取数或取中位数。Choice 可选择是否带入之前的预测。
- **Chat**：每步携带当前消息、已生成文本、最多三轮历史和 Notes；单词模式还携带之前的选择。字符模式遇到两个连续空格或五个相同字符停止；单词模式连续五次选择同一项停止。上限为 64 / 128 / 256 个字符，或 32 / 64 / 128 次单词模式判断，标点和控制标记也计入。因重复或上限停止会标记未完成，不伪装成 `END`。
- **Canvas**：枚举法按顺序遍历像素；蒙特卡洛法选择坐标或 `END`；圆珠笔选择起点、方向、抬笔或 `END`。边界、重复检测和步数上限负责让实验有个尽头。
- **Notes**：开始时固定本轮内容，每次判断原样发送，运行中不能修改。Notes 不保证能提高预测效果。

## 本地运行

Python 3.9+；TypeSafe 推理无需额外 Python 依赖。在项目根目录的 `.env` 或环境变量中配置 `TYPESAFE_API_KEY`：

```dotenv
TYPESAFE_API_KEY=your-typesafe-api-key
```

```bash
python3 calculator.py
```

打开 <http://127.0.0.1:8765>。用 `--port 8766` 修改端口，或用 `--model jev-latest` 修改模型；默认模型为 `jev-1.13.0`。服务只监听本机。修改配置后重启，不要将真实凭据提交到 Git。

也支持可选的本地 **Laya** 推理。安装、部署和配置细节见[开发指南（英文）](development.md)。

## 开发

```bash
python3 -m unittest discover -s tests -t . -v
python3 -m unittest tests.test_chat_words -v
node --check calculator_ui/app.js
```

测试使用模拟模型响应，HTTP 集成测试会绑定本机端口。CI 检查 Python 3.9、3.12 和前端 JavaScript 语法。测试保证实验能跑，不保证 Jev 长出了常识。

| 目录 | 内容 |
| --- | --- |
| `calculator_ui/` | 界面和翻译 |
| `api/` | Vercel 函数入口 |
| `tests/` | 单元测试和 HTTP 集成测试 |
| `docs/` | 多语言 README 和开发指南 |

参考：[TypeSafe 快速开始](https://docs.typesafe.ai/introduction/quickstart)、[Choice](https://docs.typesafe.ai/primitives/choice)、[HTTP API](https://docs.typesafe.ai/api)、[confidence](https://docs.typesafe.ai/confidence)。
