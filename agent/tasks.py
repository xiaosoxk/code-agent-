# -*- coding: utf-8 -*-
"""
tasks.py — 任务/里程碑管理(JSON持久化, 离线可用)
数据结构: {"tasks":[{"id","title","project","priority","due","done","created"}]}
项目分类: bishe(毕设) kaoyan(考研) job(求职) general
"""
import json, os, datetime
from . import config

FILE = config.TASKS_FILE

def _load():
    if os.path.exists(FILE):
        return json.load(open(FILE, encoding="utf-8"))
    return {"tasks": [], "next_id": 1}

def _save(db):
    json.dump(db, open(FILE, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

def add(title, project="general", priority="mid", due=None):
    db = _load()
    t = {"id": db["next_id"], "title": title, "project": project,
         "priority": priority, "due": due, "done": False,
         "created": datetime.date.today().isoformat()}
    db["tasks"].append(t); db["next_id"] += 1
    _save(db)
    return t

def do(tid):
    db = _load()
    for t in db["tasks"]:
        if t["id"] == tid:
            t["done"] = True
            t["done_date"] = datetime.date.today().isoformat()
            _save(db)
            return t
    return None

def undone(tid):
    db = _load()
    for t in db["tasks"]:
        if t["id"] == tid:
            t["done"] = False
            _save(db)
            return t
    return None

def list_tasks(project=None, all_=False):
    db = _load()
    out = []
    today = datetime.date.today().isoformat()
    for t in db["tasks"]:
        if project and t["project"] != project:
            continue
        if not all_ and t["done"]:
            continue
        out.append(t)
    # 排序: 未完成优先, priority 高在前, due 早在前
    pri = {"high": 0, "mid": 1, "low": 2}
    out.sort(key=lambda t: (t["done"], pri.get(t["priority"], 1), t["due"] or "9999"))
    return out

def milestones_bishe():
    """毕设21天里程碑模板(对应保姆级实施手册) — 一键导入"""
    ms = [
        ("bishe", "零硬件全链路: smoke_test全绿+上位机接仿真器", "high"),
        ("bishe", "核心板串口通: HELLO帧可见", "high"),
        ("bishe", "ADC+DMA采样: 信号源正弦上位机可见", "high"),
        ("bishe", "FFT开环: 叠加3次谐波THD=18.03%", "high"),
        ("bishe", "锁相闭环: 50.3Hz漂移锁定+THD恢复", "high"),
        ("bishe", "前端电路: 偏置1.65V实测+fc=3.39kHz", "mid"),
        ("bishe", "协议联调: 拔线三次自动重连+丢帧统计", "mid"),
        ("bishe", "标定+测试矩阵回填论文【实测】", "high"),
    ]
    for _, title, pri in ms:
        add(title, "bishe", pri)
    return len(ms)
