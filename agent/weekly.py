# -*- coding: utf-8 -*-
"""
weekly.py — 周报生成器：git提交记录 + 本周完成任务 → Markdown周报
用途: 毕设周报/导师汇报, 一条命令生成, 省去回忆一周干了什么
"""
import os, subprocess, datetime
from . import config, tasks

def git_log_since(days=7, repo=None):
    """读git提交记录(需已装git, 目录含.git); 失败返回空"""
    repo = repo or os.path.join(config.ROOT, "..")
    try:
        out = subprocess.run(
            ["git", "-C", repo, "log", "--since=%d.days" % days,
             "--pretty=format:%ad %s", "--date=short"],
            capture_output=True, text=True, timeout=15,
            encoding="utf-8", errors="replace")
        return [l for l in out.stdout.splitlines() if l.strip()]
    except Exception:
        return []

def generate(days=7, repo=None, out_path=None):
    today = datetime.date.today()
    start = today - datetime.timedelta(days=days)
    commits = git_log_since(days, repo)
    # 本周完成任务(按done_date)
    db = tasks._load()
    done = [t for t in db["tasks"]
            if t.get("done") and t.get("done_date", "9999") >= start.isoformat()]
    md = ["# 周报 (%s ~ %s)" % (start.isoformat(), today.isoformat()), ""]
    md.append("## 本周完成任务 (%d)" % len(done))
    for t in done:
        md.append("- [%s] %s" % (t["project"], t["title"]))
    if not done:
        md.append("- (本周无任务记录 — 用 `task add/done` 记录)")
    md.append("")
    md.append("## Git 提交记录 (%d)" % len(commits))
    for c in commits:
        md.append("- " + c)
    if not commits:
        md.append("- (无提交记录)")
    md.append("")
    md.append("## 下周计划")
    for t in tasks.list_tasks(all_=False)[:8]:
        md.append("- [%s][%s] %s" % (t["project"], t["priority"], t["title"]))
    md_text = "\n".join(md)
    out_path = out_path or os.path.join(config.DATA, "weekly_%s.md" % today.isoformat())
    open(out_path, "w", encoding="utf-8").write(md_text)
    return out_path, md_text
