## 理解代码

```shell
1. 审 analyses 而非 articles
   - workflow 顺序：Collector → Analyzer → analyses → Organizer → articles
   - 若审 articles，质量问题在 organize 之后才暴露，要打回就得重做 organize
   - 审 analyses 可以在 organize 前拦截，节省无用功
2. 权重写代码里不写 prompt
   - prompt 里已有文字说明（"25%"），LLM 能理解权重含义
   - 权重 dict 是给 _compute_weighted_score() 用的，代码逻辑需要精确数值
   - 分离"规则描述"（prompt）和"规则执行"（代码），避免 LLM 读错数字
3. 代码重算而非信任 LLM 算术
   - LLMs 不擅长精确算术是已知问题
   - 接收 LLM 的维度评分（判断任务），但自己算加权和（计算任务）
   - "Trust but verify"：对 LLM 擅长的部分放手，对它弱的环节自己来
4. temperature=0.1
   - 评分需要确定性，同一批条目多次调用应得到相近分数
   - 高 temperature 会让同一输入每次评分波动大，失去审核意义
5. LLM 失败自动通过
   - Review 是质量关卡，不是阻断节点
   - 失败时阻塞流程等于把"网络抖动"变成"系统停机"
   - analyses 已经是 LLM 输出，审核失败不改变已有结果的质量
   - 自动通过让 pipeline 保持韧性，不因单次 API 异常而挂起
```

## 运行验证

```shell
millerlin@millerdeMacBook-Pro v3 % uv run python3 -m workflows.graph
/Users/millerlin/Codes/local/opencode-workspace/action-camp/ai-knowledge-base/v3/.venv/lib/python3.14/site-packages/langgraph/cache/base/__init__.py:8: LangChainPendingDeprecationWarning: The default value of `allowed_objects` will change in a future version. Pass an explicit value (e.g., allowed_objects='messages' or allowed_objects='core') to suppress this warning.
  from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
2026-05-09 06:37:19,544 INFO 工作流图构建完成，开始执行...
2026-05-09 06:37:19,546 INFO [Collector] 开始采集 GitHub Trending 仓库...
2026-05-09 06:37:21,764 INFO [Collector] 采集完成，共 14 条符合条件的仓库
2026-05-09 06:37:21,776 INFO [Event] Node: collect
2026-05-09 06:37:21,776 INFO   → 采集到 14 条仓库
2026-05-09 06:37:21,776 INFO [Analyzer] 开始分析 14 条数据（iteration=0）...
2026-05-09 06:37:31,746 INFO HTTP Request: POST https://api.minimax.chat/v1/chat/completions "HTTP/1.1 200 OK"
2026-05-09 06:37:31,797 INFO [Analyzer] 完成 1/14 条
2026-05-09 06:37:39,766 INFO HTTP Request: POST https://api.minimax.chat/v1/chat/completions "HTTP/1.1 200 OK"
2026-05-09 06:37:39,769 INFO [Analyzer] 完成 2/14 条
2026-05-09 06:37:52,124 INFO HTTP Request: POST https://api.minimax.chat/v1/chat/completions "HTTP/1.1 200 OK"
2026-05-09 06:37:52,128 INFO [Analyzer] 完成 3/14 条
2026-05-09 06:38:03,437 INFO HTTP Request: POST https://api.minimax.chat/v1/chat/completions "HTTP/1.1 200 OK"
2026-05-09 06:38:03,491 INFO [Analyzer] 完成 4/14 条
2026-05-09 06:38:10,562 INFO HTTP Request: POST https://api.minimax.chat/v1/chat/completions "HTTP/1.1 200 OK"
2026-05-09 06:38:10,566 INFO [Analyzer] 完成 5/14 条
2026-05-09 06:38:20,763 INFO HTTP Request: POST https://api.minimax.chat/v1/chat/completions "HTTP/1.1 200 OK"
2026-05-09 06:38:20,815 INFO [Analyzer] 完成 6/14 条
2026-05-09 06:38:28,167 INFO HTTP Request: POST https://api.minimax.chat/v1/chat/completions "HTTP/1.1 200 OK"
2026-05-09 06:38:28,169 INFO [Analyzer] 完成 7/14 条
2026-05-09 06:38:38,790 INFO HTTP Request: POST https://api.minimax.chat/v1/chat/completions "HTTP/1.1 200 OK"
2026-05-09 06:38:38,840 INFO [Analyzer] 完成 8/14 条
2026-05-09 06:38:47,068 INFO HTTP Request: POST https://api.minimax.chat/v1/chat/completions "HTTP/1.1 200 OK"
2026-05-09 06:38:47,115 INFO [Analyzer] 完成 9/14 条
2026-05-09 06:38:56,980 INFO HTTP Request: POST https://api.minimax.chat/v1/chat/completions "HTTP/1.1 200 OK"
2026-05-09 06:38:56,984 INFO [Analyzer] 完成 10/14 条
2026-05-09 06:39:09,316 INFO HTTP Request: POST https://api.minimax.chat/v1/chat/completions "HTTP/1.1 200 OK"
2026-05-09 06:39:09,364 INFO [Analyzer] 完成 11/14 条
2026-05-09 06:39:16,072 INFO HTTP Request: POST https://api.minimax.chat/v1/chat/completions "HTTP/1.1 200 OK"
2026-05-09 06:39:16,077 INFO [Analyzer] 完成 12/14 条
2026-05-09 06:39:25,468 INFO HTTP Request: POST https://api.minimax.chat/v1/chat/completions "HTTP/1.1 200 OK"
2026-05-09 06:39:25,472 INFO [Analyzer] 完成 13/14 条
2026-05-09 06:39:34,722 INFO HTTP Request: POST https://api.minimax.chat/v1/chat/completions "HTTP/1.1 200 OK"
2026-05-09 06:39:34,724 INFO [Analyzer] 完成 14/14 条
2026-05-09 06:39:34,724 INFO [Analyzer] 分析完成，共 14 条，cost=¥0.0163
2026-05-09 06:39:34,727 INFO [Event] Node: analyze
2026-05-09 06:39:34,727 INFO   → 分析完成 14 条，cost=¥0.0163
2026-05-09 06:39:34,728 INFO [Reviewer] 开始审核 14 条 analyses（iteration=0）...
2026-05-09 06:39:34,728 INFO [Reviewer] 限制审核前 5 条（控 token 消耗）
2026-05-09 06:39:59,711 INFO HTTP Request: POST https://api.minimax.chat/v1/chat/completions "HTTP/1.1 200 OK"
2026-05-09 06:39:59,756 INFO [Reviewer] 收到 5 条审核结果的数组，计算平均分
2026-05-09 06:39:59,756 INFO [Reviewer] 加权总分=6.48（阈值=7.0），passed=False
2026-05-09 06:39:59,756 INFO [Reviewer] 各维度得分: summary=6.6 technical=5.2 relevance=7.0 originality=5.4 formatting=8.8
2026-05-09 06:39:59,758 INFO [Router] review_passed=False, iteration=0
2026-05-09 06:39:59,760 INFO [Event] Node: review
2026-05-09 06:39:59,760 INFO   → 审核结果: passed=False, iteration=0, feedback=条目1: 该条目与AI/LLM/Agent领域几乎无直接关联。摘要描述的是通用编程电子书资源项目，缺
2026-05-09 06:39:59,760 INFO [Organizer] 开始组织 14 条数据（iteration=0）...
2026-05-09 06:39:59,760 INFO [Organizer] 过滤后（score>=0.6）：12 条
2026-05-09 06:39:59,760 INFO [Organizer] 去重后：1 条（移除 11 条重复）
2026-05-09 06:39:59,760 INFO [Organizer] 组织完成，共 1 条待审文章
2026-05-09 06:39:59,760 INFO [Event] Node: organize
2026-05-09 06:39:59,760 INFO   → 整理完成 1 条待审
2026-05-09 06:39:59,760 INFO [Reviewer] 开始审核 14 条 analyses（iteration=0）...
2026-05-09 06:39:59,760 INFO [Reviewer] 限制审核前 5 条（控 token 消耗）
2026-05-09 06:40:23,210 INFO HTTP Request: POST https://api.minimax.chat/v1/chat/completions "HTTP/1.1 200 OK"
2026-05-09 06:40:23,255 INFO [Reviewer] 收到 5 条审核结果的数组，计算平均分
2026-05-09 06:40:23,256 INFO [Reviewer] 加权总分=6.79（阈值=7.0），passed=False
2026-05-09 06:40:23,256 INFO [Reviewer] 各维度得分: summary=7.0 technical=6.6 relevance=6.6 originality=5.6 formatting=8.2
2026-05-09 06:40:23,257 INFO [Router] review_passed=False, iteration=0
2026-05-09 06:40:23,259 INFO [Event] Node: review
2026-05-09 06:40:23,259 INFO   → 审核结果: passed=False, iteration=0, feedback=条目1: 该条目与AI/LLM/Agent领域相关性极低。免费编程书籍项目虽对编程学习有帮助，但不属
2026-05-09 06:40:23,259 INFO [Organizer] 开始组织 14 条数据（iteration=0）...
2026-05-09 06:40:23,259 INFO [Organizer] 过滤后（score>=0.6）：12 条
2026-05-09 06:40:23,259 INFO [Organizer] 去重后：1 条（移除 11 条重复）
2026-05-09 06:40:23,259 INFO [Organizer] 组织完成，共 1 条待审文章
2026-05-09 06:40:23,259 INFO [Event] Node: organize
2026-05-09 06:40:23,259 INFO   → 整理完成 1 条待审
2026-05-09 06:40:23,259 INFO [Reviewer] 开始审核 14 条 analyses（iteration=0）...
2026-05-09 06:40:23,259 INFO [Reviewer] 限制审核前 5 条（控 token 消耗）
2026-05-09 06:40:48,950 INFO HTTP Request: POST https://api.minimax.chat/v1/chat/completions "HTTP/1.1 200 OK"
2026-05-09 06:40:49,007 INFO [Reviewer] 收到 5 条审核结果的数组，计算平均分
2026-05-09 06:40:49,007 INFO [Reviewer] 加权总分=6.46（阈值=7.0），passed=False
2026-05-09 06:40:49,007 INFO [Reviewer] 各维度得分: summary=6.4 technical=5.2 relevance=7.2 originality=6.1 formatting=8.0
2026-05-09 06:40:49,008 INFO [Router] review_passed=False, iteration=0
2026-05-09 06:40:49,010 INFO [Event] Node: review
2026-05-09 06:40:49,010 INFO   → 审核结果: passed=False, iteration=0, feedback=条目1: 该条目与AI/LLM/Agent领域相关性较低。summary_quality方面，摘要过
2026-05-09 06:40:49,010 INFO [Organizer] 开始组织 14 条数据（iteration=0）...
2026-05-09 06:40:49,010 INFO [Organizer] 过滤后（score>=0.6）：12 条
2026-05-09 06:40:49,010 INFO [Organizer] 去重后：1 条（移除 11 条重复）
2026-05-09 06:40:49,010 INFO [Organizer] 组织完成，共 1 条待审文章
2026-05-09 06:40:49,011 INFO [Event] Node: organize
2026-05-09 06:40:49,011 INFO   → 整理完成 1 条待审
2026-05-09 06:40:49,011 INFO [Reviewer] 开始审核 14 条 analyses（iteration=0）...
2026-05-09 06:40:49,011 INFO [Reviewer] 限制审核前 5 条（控 token 消耗）
2026-05-09 06:41:08,994 INFO HTTP Request: POST https://api.minimax.chat/v1/chat/completions "HTTP/1.1 200 OK"
2026-05-09 06:41:09,048 INFO [Reviewer] 收到 5 条审核结果的数组，计算平均分
2026-05-09 06:41:09,048 INFO [Reviewer] 加权总分=6.56（阈值=7.0），passed=False
2026-05-09 06:41:09,048 INFO [Reviewer] 各维度得分: summary=7.6 technical=5.0 relevance=6.8 originality=4.7 formatting=9.0
2026-05-09 06:41:09,051 INFO [Router] review_passed=False, iteration=0
2026-05-09 06:41:09,053 INFO [Event] Node: review
2026-05-09 06:41:09,053 INFO   → 审核结果: passed=False, iteration=0, feedback=条目1: 该条目与AI/LLM/Agent领域几乎无直接关联。摘要和内容描述的是一个编程书籍资源导航
2026-05-09 06:41:09,053 INFO [Organizer] 开始组织 14 条数据（iteration=0）...
2026-05-09 06:41:09,053 INFO [Organizer] 过滤后（score>=0.6）：12 条
2026-05-09 06:41:09,053 INFO [Organizer] 去重后：1 条（移除 11 条重复）
2026-05-09 06:41:09,053 INFO [Organizer] 组织完成，共 1 条待审文章
2026-05-09 06:41:09,053 INFO [Event] Node: organize
2026-05-09 06:41:09,053 INFO   → 整理完成 1 条待审
2026-05-09 06:41:09,053 INFO [Reviewer] 开始审核 14 条 analyses（iteration=0）...
2026-05-09 06:41:09,053 INFO [Reviewer] 限制审核前 5 条（控 token 消耗）
2026-05-09 06:41:30,289 INFO HTTP Request: POST https://api.minimax.chat/v1/chat/completions "HTTP/1.1 200 OK"
2026-05-09 06:41:30,330 INFO [Reviewer] 收到 5 条审核结果的数组，计算平均分
2026-05-09 06:41:30,331 INFO [Reviewer] 加权总分=7.11（阈值=7.0），passed=True
2026-05-09 06:41:30,331 INFO [Reviewer] 各维度得分: summary=7.8 technical=6.2 relevance=6.8 originality=6.2 formatting=8.8
2026-05-09 06:41:30,336 INFO [Router] review_passed=True, iteration=0
2026-05-09 06:41:30,337 INFO [Event] Node: review
2026-05-09 06:41:30,337 INFO   → 审核结果: passed=True, iteration=0, feedback=条目1: 该条目与AI/LLM/Agent领域相关度较低。主要是一个编程资源集合网站，技术栈简单（M
2026-05-09 06:41:30,338 INFO [Saver] 开始保存 1 条文章...
2026-05-09 06:41:30,341 INFO [Saver] 已保存: 2026-05-08-000
2026-05-09 06:41:30,342 INFO [Saver] 保存完成，共 1 条，已更新索引
2026-05-09 06:41:30,342 INFO [Event] Node: save
2026-05-09 06:41:30,342 INFO   → 节点返回空状态，跳过
2026-05-09 06:41:30,343 INFO 工作流执行完毕
```