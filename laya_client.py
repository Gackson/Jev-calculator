"""Optional, offline Laya backend. Heavy dependencies load only on first use."""
import importlib.util
import json
import os
from pathlib import Path
import threading

from typesafe_client import ApiFailure


class LocalModelFailure(ApiFailure):
    pass


class LayaClient:
    model = "laya-local"

    def __init__(self, path=None, device="auto"):
        self.path = Path(path).expanduser().resolve() if path else None
        self.device = None if device == "auto" else device
        self.agent = None
        self.lock = threading.Lock()

    def _checkpoint(self):
        if self.path is not None:
            return self.path
        root = Path(__file__).resolve().parent
        for directory in (root, root.parent):
            manifest = directory / ".cache-laya/checkpoint.json"
            if manifest.is_file():
                try:
                    config = json.loads(manifest.read_text())
                    return Path(config["snapshot_path"]) / config.get("subfolder", "")
                except (ValueError, KeyError, TypeError):
                    break
        raise LocalModelFailure("未找到本地 Laya 模型，请用 --laya-path 指定已下载的模型目录。")

    def available(self):
        """Check offline files and the current runtime without loading the model."""
        if importlib.util.find_spec("laya") is None:
            return False
        try:
            self._validated_checkpoint()
        except (LocalModelFailure, OSError):
            return False
        return True

    def _validated_checkpoint(self):
        path = self._checkpoint()
        if not all((path / name).exists() for name in
                   ("rl_agent_config.json", "model.safetensors", "tokenizer", "encoder")):
            raise LocalModelFailure("本地 Laya 模型文件不完整，请检查 --laya-path 指向的模型目录。")
        return path

    def _load(self):
        path = self._validated_checkpoint()
        # No implicit downloads, API calls or hosted fallback, even with an HF token set.
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["TRANSFORMERS_OFFLINE"] = "1"
        os.environ.setdefault("USE_TF", "0")
        os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
        try:
            import laya
        except ImportError:
            raise LocalModelFailure("当前 Python 未安装 Laya，请使用 .venv-laya/bin/python 或安装 requirements-laya.txt 后重启。") from None
        try:
            self.agent = laya.load(str(path), device=self.device)
        except Exception:
            raise LocalModelFailure("无法加载本地 Laya 模型，请检查模型文件、依赖和可用内存。") from None

    def _budget(self, state, questions):
        """Preserve the entire SDK input, including all 197 options at 14×14."""
        from laya.common import render_options, serialize_state
        agent = self.agent
        tok = agent.tok
        def count(text):
            return len(tok(text.replace(tok.mask_token, " "), add_special_tokens=False)["input_ids"])
        head = 0
        for definition in questions.values():
            question = agent._to_internal(definition)
            options = [count(" " + option) for option in render_options(question)]
            if any(length > 48 for length in options):
                raise LocalModelFailure("选项超出本地 Laya 的长度限制，请缩短输入。")
            instructions = count("%s question: %s" % (question["t"], question["ins"]))
            head = max(head, max(16, instructions) + sum(length + 1 for length in options))
        total = head + count(serialize_state(state)) + 4
        capacity = min(8192, agent.model.encoder.config.max_position_embeddings)
        if total > capacity:
            raise LocalModelFailure("输入超出本地 Laya 的上下文容量，请缩短消息或新建对话。")
        agent.cfg["head_max_len"] = head
        agent.cfg["max_len"] = total

    def __call__(self, payload):
        # The agent and its token budgets are shared across request threads.
        with self.lock:
            if self.agent is None:
                self._load()
            try:
                self._budget(payload["state"], payload["questions"])
                response = self.agent.predict(payload["state"], payload["questions"])
            except LocalModelFailure:
                raise
            except Exception:
                raise LocalModelFailure("本地 Laya 推理失败，请检查可用内存，或用 --laya-device cpu 重启。") from None
            return {**response, "model": self.model}
