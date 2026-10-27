# 个人 Agent 管家（毕设/考研/求职 三合一）

实际天天可用的个人 Agent：任务管理、间隔重复记忆卡（SM-2 考研背诵）、周报自动生成，核心功能**全离线可用**；接入 LLM（DeepSeek 国内直连 / Ollama 本地）后支持自然语言对话 + 工具调用。

## 快速开始
```
cd code/agent
pip install -r requirements.txt

python main.py task milestones                  # 导入毕设21天里程碑
python main.py task add "完成开题报告" --project bishe --priority high
python main.py task list
python main.py task done 3

python main.py card add "OFDM的CP作用|对抗多径ISI" --tag kaoyan
python main.py card review                      # 今日复习(SM-2自动排期)
python main.py card stats

python main.py weekly                           # 生成Markdown周报(git提交+完成任务)
```

## 接入 LLM（可选，两分钟）
创建 `data/llm.json`（或设环境变量）：
```json
{"api_base": "https://api.deepseek.com", "api_key": "sk-你的key", "model": "deepseek-chat"}
```
然后自然语言驱动：
```
python main.py agent "帮我安排这周毕设计划，周五前要完成ADC调试"
```
Agent 会自动调用工具（task_add 等）落地执行。Ollama 本地：api_base 改 `http://localhost:11434/v1`，model 填 `qwen2.5:7b`，key 随便填。

## 架构
```
main.py      CLI入口(argparse子命令)
agent/core.py      LLM工具调用循环(OpenAI兼容, 可插DeepSeek/Ollama) + 离线降级
agent/tasks.py     任务/里程碑(JSON持久化)
agent/flashcards.py  SM-2间隔重复(考研背诵)
agent/weekly.py    周报生成(git log + 任务完成)
tools注册表模式: 新增工具=写函数+@tool装饰器, agent循环零改动
```

## 验证
```
python test_agent.py   # 全离线自检: 任务/SM-2/工具注册/离线降级/周报
```
已验证输出：SM-2 间隔序列 1→6→interval×ease 正确，遗忘自动重学，ease 调整符合算法。
