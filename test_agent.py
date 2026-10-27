# -*- coding: utf-8 -*-
"""test_agent.py — Agent 冒烟自检（全离线, 无API依赖）"""
import sys, os, tempfile
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# 隔离测试数据(不污染真实data)
import agent.config as config
_tmp = tempfile.mkdtemp()
config.TASKS_FILE = os.path.join(_tmp, "tasks.json")
config.CARDS_FILE = os.path.join(_tmp, "cards.json")
from agent import tasks, flashcards, weekly, core

# --- 1) 任务 ---
t = tasks.add("完成ADC采样调试", "bishe", "high", "2026-11-05")
assert t["id"] == 1
tasks.add("背单词list1", "kaoyan", "mid")
assert len(tasks.list_tasks()) == 2
tasks.do(1)
done = [t for t in tasks.list_tasks(all_=True) if t["done"]]
assert len(done) == 1 and done[0]["done_date"]
print("tasks OK")

# --- 2) 记忆卡 SM-2 ---
c = flashcards.add("OFDM的CP作用", "对抗多径ISI并简化频域均衡", "kaoyan")
r1 = flashcards.review(c["id"], 5)     # 第一轮: 间隔1天
assert r1["interval"] == 1 and r1["reps"] == 1
r2 = flashcards.review(c["id"], 4)     # 第二轮: 间隔6天
assert r2["interval"] == 6
r3 = flashcards.review(c["id"], 3)     # 第三轮: 间隔6*ease
assert r3["interval"] >= 6
e0 = r3["ease"]
r4 = flashcards.review(c["id"], 1)     # 忘了 → 重学
assert r4["interval"] == 1 and r4["lapses"] == 1
print("flashcards SM-2 OK (ease %.2f, 忘记自动重学)" % e0)

# --- 3) 工具注册表(agent循环用) ---
assert "task_add" in core.TOOL_IMPL and "weekly_report" in core.TOOL_IMPL
r = core.TOOL_IMPL["task_list"]["fn"]()
print("tools OK:", r.splitlines()[0])

# --- 4) 离线模式提示 ---
msg = core.run_agent("测试")
assert msg.startswith("[离线模式]"), "无API时应返回离线提示"
print("offline fallback OK")

# --- 5) 周报 ---
p, md = weekly.generate(7)
assert os.path.exists(p) and "周报" in md
print("weekly OK ->", p)

print("ALL AGENT SMOKE TESTS PASSED")
