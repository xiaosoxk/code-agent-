# -*- coding: utf-8 -*-
"""
flashcards.py — 间隔重复记忆卡(SM-2算法): 考研英语单词/政治/专业课错题
数据: {"cards":[{"id","front","back","tag","ease","interval","due","reps","lapses"}]}
评分: 记忆质量 q∈{0,1,2,3,4,5} (忘了=0/2, 想起来但费力=3, 轻松=5)
用法: add → 每天 review(自动取到期卡) → 输入自评分 → 自动排期
"""
import json, os, datetime
from . import config

FILE = config.CARDS_FILE

def _today(): return datetime.date.today()
def _load():
    if os.path.exists(FILE):
        return json.load(open(FILE, encoding="utf-8"))
    return {"cards": [], "next_id": 1}
def _save(db): json.dump(db, open(FILE, "w", encoding="utf-8"),
                         ensure_ascii=False, indent=1)

def add(front, back, tag="general"):
    db = _load()
    c = {"id": db["next_id"], "front": front, "back": back, "tag": tag,
         "ease": 2.5, "interval": 0, "due": _today().isoformat(),
         "reps": 0, "lapses": 0}
    db["cards"].append(c); db["next_id"] += 1
    _save(db)
    return c

def due_cards(tag=None):
    """今天到期的卡(新卡interval=0也算到期)"""
    db = _load()
    today = _today().isoformat()
    return [c for c in db["cards"]
            if c["due"] <= today and (tag is None or c["tag"] == tag)]

def review(cid, quality):
    """SM-2: q>=3 通过(间隔×ease), q<3 重学(间隔=1)"""
    db = _load()
    for c in db["cards"]:
        if c["id"] == cid:
            q = max(0, min(5, int(quality)))
            if q < 3:
                c["reps"] = 0; c["interval"] = 1
                c["lapses"] = c.get("lapses", 0) + 1
            else:
                if c["reps"] == 0:   c["interval"] = 1
                elif c["reps"] == 1: c["interval"] = 6
                else:                c["interval"] = max(1, int(round(c["interval"] * c["ease"])))
                c["reps"] += 1
                c["ease"] = max(1.3, c["ease"] + 0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
            c["due"] = (_today() + datetime.timedelta(days=c["interval"])).isoformat()
            _save(db)
            return c
    return None

def stats():
    db = _load()
    due = len(due_cards())
    return {"total": len(db["cards"]), "due": due,
            "learned": sum(1 for c in db["cards"] if c["reps"] >= 2)}

def import_lines(tag, text):
    """批量导入: 每行 '正面|背面'"""
    n = 0
    for ln in text.splitlines():
        ln = ln.strip()
        if "|" in ln:
            a, b = ln.split("|", 1)
            add(a.strip(), b.strip(), tag); n += 1
    return n
