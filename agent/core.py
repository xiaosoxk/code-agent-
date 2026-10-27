# -*- coding: utf-8 -*-
"""
core.py — Agent 核心：OpenAI 兼容工具调用循环（可插 DeepSeek/Ollama/任意兼容端点）
+ 离线降级：无API时所有工具仍可经CLI直接使用

工具以"注册表"模式组织：每个工具 = {name, desc, params(JSON Schema), fn}
fn(**kwargs) -> str (结果文本, 回填给LLM)
新增工具只需写函数+注册, agent循环零改动 —— 答辩讲"可扩展工具生态"
"""
import json, os
from . import config, tasks, flashcards, weekly

# ================= 工具实现(全部离线可用) =================
TOOL_IMPL = {}

def tool(name, desc, params):
    def deco(fn):
        TOOL_IMPL[name] = {"desc": desc, "params": params, "fn": fn}
        return fn
    return deco

@tool("task_add", "添加任务", {
    "type": "object",
    "properties": {
        "title": {"type": "string", "description": "任务内容"},
        "project": {"type": "string", "enum": ["bishe", "kaoyan", "job", "general"]},
        "priority": {"type": "string", "enum": ["high", "mid", "low"]},
        "due": {"type": "string", "description": "截止日期 YYYY-MM-DD, 可省略"}},
    "required": ["title"]})
def t_task_add(title, project="general", priority="mid", due=None):
    t = tasks.add(title, project, priority, due)
    return "已添加任务 #%d: %s [%s/%s]" % (t["id"], t["title"], t["project"], t["priority"])

@tool("task_done", "完成任务", {
    "type": "object", "properties": {"id": {"type": "integer"}}, "required": ["id"]})
def t_task_done(id):
    t = tasks.do(id)
    return ("已完成: %s" % t["title"]) if t else "任务不存在"

@tool("task_list", "列出未完成任务", {"type": "object", "properties": {
    "project": {"type": "string"}}})
def t_task_list(project=None):
    ts = tasks.list_tasks(project)
    if not ts:
        return "没有未完成任务"
    return "\n".join("#%d [%s/%s]%s %s" % (t["id"], t["project"], t["priority"],
                     (" 截止" + t["due"]) if t["due"] else "", t["title"]) for t in ts)

@tool("card_add", "添加记忆卡(格式: 正面|背面)", {
    "type": "object",
    "properties": {"front": {"type": "string"}, "back": {"type": "string"},
                   "tag": {"type": "string"}}, "required": ["front", "back"]})
def t_card_add(front, back, tag="general"):
    c = flashcards.add(front, back, tag)
    return "记忆卡 #%d 已添加" % c["id"]

@tool("card_due", "查看今日到期记忆卡数量", {"type": "object", "properties": {}})
def t_card_due(_=None):
    s = flashcards.stats()
    return "总卡%d张, 今日待复习%d张, 已巩固%d张" % (s["total"], s["due"], s["learned"])

@tool("weekly_report", "生成本周周报(git提交+完成任务)", {
    "type": "object", "properties": {}})
def t_weekly(_=None):
    path, _ = weekly.generate()
    return "周报已生成: " + path

TOOL_IMPL["milestones_bishe"] = {
    "desc": "导入毕设21天里程碑模板", "params": {"type": "object", "properties": {}},
    "fn": lambda: "已导入 %d 条毕设里程碑" % tasks.milestones_bishe()}
TOOL_IMPL["card_stats"] = TOOL_IMPL["card_due"]

# ================= LLM 工具调用循环 =================
SYSTEM_PROMPT = (
    "你是电子信息工程专业学生的个人助理Agent。管理毕设(bishe)/考研(kaoyan)/求职(job)任务、"
    "间隔重复记忆卡、周报生成。用户消息可能是自然语言, 你应调用合适工具完成操作, "
    "然后简洁回复结果。涉及学习建议时给出具体可执行的安排。")

def _http_post(url, payload, api_key):
    """urllib实现(零额外依赖)"""
    import urllib.request
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json",
                 "Authorization": "Bearer " + api_key})
    return json.loads(urllib.request.urlopen(req, timeout=120).read().decode())

def run_agent(user_msg, max_rounds=6, on_event=print):
    """LLM工具调用循环。返回最终回复。无API配置时返回离线提示。"""
    cfg = config.llm_config()
    if not cfg["api_key"]:
        return ("[离线模式] 未配置LLM。所有工具仍可用CLI方式:\n"
                "  python main.py task add \"...\"\n"
                "  python main.py task list / done <id>\n"
                "  python main.py card add \"正面|背面\" / review / stats\n"
                "  python main.py weekly\n"
                "配置LLM: data/llm.json 填入 {\"api_key\":\"sk-...\"} (推荐DeepSeek, 国内直连)")

    tools = [{"type": "function", "function":
              {"name": n, "description": v["desc"], "parameters": v["params"]}}
             for n, v in TOOL_IMPL.items()]
    messages = [{"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_msg}]
    url = cfg["api_base"].rstrip("/") + "/chat/completions"

    for _ in range(max_rounds):
        resp = _http_post(url, {
            "model": cfg["model"], "messages": messages, "tools": tools}, cfg["api_key"])
        msg = resp["choices"][0]["message"]
        calls = msg.get("tool_calls")
        if not calls:
            return msg.get("content", "(无回复)")
        messages.append(msg)
        for call in calls:
            name = call["function"]["name"]
            try:
                args = json.loads(call["function"]["arguments"] or "{}")
            except json.JSONDecodeError:
                args = {}
            impl = TOOL_IMPL.get(name)
            result = str(impl["fn"](**args)) if impl else "未知工具: " + name
            on_event("[工具] %s(%s) -> %s" % (name, args, result[:80]))
            messages.append({"role": "tool", "tool_call_id": call["id"],
                             "content": result})
    return "达到最大轮数"
