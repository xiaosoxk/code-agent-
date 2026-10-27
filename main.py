# -*- coding: utf-8 -*-
"""main.py — Agent 命令行入口
离线用法(不需要任何API):
  python main.py task milestones            导入毕设21天里程碑
  python main.py task add "写开题报告" --project bishe --priority high
  python main.py task list [--project bishe] [--all]
  python main.py task done 3
  python main.py card add "OFDM的CP作用|对抗多径ISI" --tag kaoyan
  python main.py card review                今日复习(逐张打分q0~5)
  python main.py card stats
  python main.py weekly                     生成周报md
在线用法(配置 data/llm.json 后):
  python main.py agent "帮我安排这周毕设计划"
"""
import sys, os, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from agent import tasks, flashcards, weekly, core

def main():
    ap = argparse.ArgumentParser("agent")
    sub = ap.add_subparsers(dest="cmd", required=True)

    t = sub.add_parser("task"); ts = t.add_subparsers(dest="op", required=True)
    ta = ts.add_parser("add"); ta.add_argument("title"); ta.add_argument("--project", default="general")
    ta.add_argument("--priority", default="mid"); ta.add_argument("--due", default=None)
    tl = ts.add_parser("list"); tl.add_argument("--project"); tl.add_argument("--all", action="store_true")
    td = ts.add_parser("done"); td.add_argument("id", type=int)
    ts.add_parser("milestones")

    c = sub.add_parser("card"); cs = c.add_subparsers(dest="op", required=True)
    ca = cs.add_parser("add"); ca.add_argument("frontback"); ca.add_argument("--tag", default="general")
    cs.add_parser("review"); cs.add_parser("stats")

    w = sub.add_parser("weekly"); w.add_argument("--days", type=int, default=7)

    a = sub.add_parser("agent"); a.add_argument("message")

    args = ap.parse_args()
    if args.cmd == "task":
        if args.op == "add":
            t = tasks.add(args.title, args.project, args.priority, args.due)
            print("已添加 #%d: %s" % (t["id"], t["title"]))
        elif args.op == "list":
            for t in tasks.list_tasks(args.project, args.all):
                mark = "x" if t["done"] else " "
                due = (" 截止" + t["due"]) if t["due"] else ""
                print("#%-3d [%s] %s %s%s" % (t["id"], mark, t["project"], t["title"], due))
        elif args.op == "done":
            t = tasks.do(args.id)
            print("已完成:" + (t["title"] if t else "未找到"))
        elif args.op == "milestones":
            print("已导入 %d 条毕设里程碑" % tasks.milestones_bishe())
    elif args.cmd == "card":
        if args.op == "add":
            front, _, back = args.frontback.partition("|")
            c = flashcards.add(front.strip(), back.strip(), args.tag)
            print("记忆卡 #%d: %s" % (c["id"], c["front"]))
        elif args.op == "review":
            due = flashcards.due_cards()
            if not due:
                print("今日无到期卡片"); return
            for c in due:
                input("正面: " + c["front"] + "  (回车看答案)")
                print("背面: " + c["back"])
                q = input("自评分 q0~5 (0=忘了 5=轻松): ")
                r = flashcards.review(c["id"], q)
                print("→ 下次复习: %s (间隔%d天, ease%.2f)\n"
                      % (r["due"], r["interval"], r["ease"]))
            print("本轮复习完成, 剩余到期:", len(flashcards.due_cards()))
        elif args.op == "stats":
            print(flashcards.stats())
    elif args.cmd == "weekly":
        path, md = weekly.generate(days=args.days)
        print(md)
        print("\n周报已保存: " + path)
    elif args.cmd == "agent":
        print(core.run_agent(args.message))

if __name__ == "__main__":
    main()
