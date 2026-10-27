# -*- coding: utf-8 -*-
"""
config.py — 配置与JSON存储
数据存放在 agent/data/ 下(建议加入.gitignore, 隐私数据)
LLM配置优先级: 环境变量 > llm.json
"""
import os, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
os.makedirs(DATA, exist_ok=True)

TASKS_FILE  = os.path.join(DATA, "tasks.json")
CARDS_FILE  = os.path.join(DATA, "cards.json")

def llm_config():
    """LLM配置: 环境变量优先, 其次 data/llm.json
    国内推荐 DeepSeek(直连便宜); 本地推荐 Ollama(qwen2.5:7b)
    """
    cfg = {"api_base": "https://api.deepseek.com",
           "api_key": "", "model": "deepseek-chat"}
    p = os.path.join(DATA, "llm.json")
    if os.path.exists(p):
        try:
            cfg.update(json.load(open(p, encoding="utf-8")))
        except Exception:
            pass
    cfg["api_base"] = os.environ.get("AGENT_API_BASE", cfg["api_base"])
    cfg["api_key"]  = os.environ.get("AGENT_API_KEY",  cfg["api_key"])
    cfg["model"]    = os.environ.get("AGENT_MODEL",    cfg["model"])
    return cfg
