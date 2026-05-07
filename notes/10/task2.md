## 理解代码

```shell
1. add_conditional_edges(source, router, mapping)
   - source: 触发条件判断的节点（"review"）
   - router: 函数，接收 state，返回字符串（"save" 或 "organize"）
   - mapping: 字典，{router返回值: 目标节点}，决定下一步去哪
2. router 返回值和 mapping 的关系
   - router 返回的字符串必须是 mapping 的 key
   - 返回 "save" → mapping"save" = "save" → 跳到 save 节点
   - 返回 "organize" → mapping"organize" = "organize" → 跳到 organize 节点
3. organize 怎么知道要修正
   - state["iteration"] > 0 且 state["review_feedback"] 有内容时
   - organize_node 内部会调用 _apply_feedback_correction(articles, feedback)
   - feedback 是 review_node 输出的，organize 直接从 state 读取
4. 循环结束条件
   - iteration >= 2 时 review_node 强制返回 review_passed=True，必走 save → END
   - 或者 review_passed=True（LLM 评分通过）也直接 save → END
```

## 运行测试

```shell
/Users/millerlin/Codes/local/opencode-workspace/action-camp/ai-knowledge-base/v3/.venv/lib/python3.14/site-packages/langgraph/cache/base/__init__.py:8: LangChainPendingDeprecationWarning: The default value of `allowed_objects` will change in a future version. Pass an explicit value (e.g., allowed_objects='messages' or allowed_objects='core') to suppress this warning.
  from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
2026-05-07 22:41:37,658 INFO 工作流图构建完成，开始执行...
2026-05-07 22:41:37,663 INFO [Collector] 开始采集 GitHub Trending 仓库...
2026-05-07 22:41:40,383 INFO [Collector] 采集完成，共 14 条符合条件的仓库
2026-05-07 22:41:40,385 INFO [Event] Node: collect, node_state type: dict, value: {'sources': [{'url': 'https://github.com/EbookFoundation/free-programming-books', 'title': 'EbookFoundation/free-programming-books', 'description': ':books: Freely available programming books', 'stars': 387870, 'language': 'Python'}, {'url': 'https://github.com/tensorflow/tensorflow', 'title': 'tensorflow/tensorflow', 'description': 'An Open Source Machine Learning Framework for Everyone', 'stars': 195028, 'language': 'C++'}, {'url': 'https://github.com/affaan-m/everything-claude-code', 'title': 'affaan-m/everything-claude-code', 'description': 'The agent harness performance optimization system. Skills, instincts, memory, security, and research-first development for Claude Code, Codex, Opencode, Cursor and beyond.', 'stars': 175162, 'language': 'JavaScript'}, {'url': 'https://github.com/huggingface/transformers', 'title': 'huggingface/transformers', 'description': '🤗 Transformers: the model-definition framework for state-of-the-art machine learning models in text, vision, audio, and multimodal models, for both inference and training. ', 'stars': 160354, 'language': 'Python'}, {'url': 'https://github.com/airbnb/javascript', 'title': 'airbnb/javascript', 'description': 'JavaScript Style Guide', 'stars': 148113, 'language': 'JavaScript'}, {'url': 'https://github.com/NousResearch/hermes-agent', 'title': 'NousResearch/hermes-agent', 'description': 'The agent that grows with you', 'stars': 137073, 'language': 'Python'}, {'url': 'https://github.com/kubernetes/kubernetes', 'title': 'kubernetes/kubernetes', 'description': 'Production-Grade Container Scheduling and Management', 'stars': 122105, 'language': 'Go'}, {'url': 'https://github.com/microsoft/generative-ai-for-beginners', 'title': 'microsoft/generative-ai-for-beginners', 'description': '21 Lessons, Get Started Building with Generative AI ', 'stars': 110310, 'language': 'Jupyter Notebook'}, {'url': 'https://github.com/deepseek-ai/DeepSeek-V3', 'title': 'deepseek-ai/DeepSeek-V3', 'description': '', 'stars': 103422, 'language': 'Python'}, {'url': 'https://github.com/pytorch/pytorch', 'title': 'pytorch/pytorch', 'description': 'Tensors and Dynamic neural networks in Python with strong GPU acceleration', 'stars': 99725, 'language': 'Python'}, {'url': 'https://github.com/msitarzewski/agency-agents', 'title': 'msitarzewski/agency-agents', 'description': 'A complete AI agency at your fingertips - From frontend wizards to Reddit community ninjas, from whimsy injectors to reality checkers. Each agent is a specialized expert with personality, processes, and proven deliverables.', 'stars': 94649, 'language': 'Shell'}, {'url': 'https://github.com/rasbt/LLMs-from-scratch', 'title': 'rasbt/LLMs-from-scratch', 'description': 'Implement a ChatGPT-like LLM in PyTorch from scratch, step by step', 'stars': 92092, 'language': 'Jupyter Notebook'}, {'url': 'https://github.com/deepseek-ai/DeepSeek-R1', 'title': 'deepseek-ai/DeepSeek-R1', 'description': '', 'stars': 92021, 'language': None}, {'url': 'https://github.com/mermaid-js/mermaid', 'title': 'mermaid-js/mermaid', 'description': 'Generation of diagrams like flowcharts or sequence diagrams from text in a similar manner as markdown', 'stars': 87862, 'language': 'TypeScript'}], 'cost_tracker': {'prompt_tokens': 0, 'completion_tokens': 0, 'total_cost_yuan': 0.0}}
2026-05-07 22:41:40,386 INFO   → 采集到 14 条仓库
2026-05-07 22:41:40,386 INFO [Analyzer] 开始分析 14 条数据（iteration=0）...
2026-05-07 22:41:54,835 INFO HTTP Request: POST https://api.minimax.chat/v1/chat/completions "HTTP/1.1 200 OK"
2026-05-07 22:41:54,840 INFO [Analyzer] 完成 1/14 条
2026-05-07 22:42:05,407 INFO HTTP Request: POST https://api.minimax.chat/v1/chat/completions "HTTP/1.1 200 OK"
2026-05-07 22:42:05,459 INFO [Analyzer] 完成 2/14 条
2026-05-07 22:42:27,608 INFO HTTP Request: POST https://api.minimax.chat/v1/chat/completions "HTTP/1.1 200 OK"
2026-05-07 22:42:27,611 INFO [Analyzer] 完成 3/14 条
2026-05-07 22:42:47,542 INFO HTTP Request: POST https://api.minimax.chat/v1/chat/completions "HTTP/1.1 200 OK"
2026-05-07 22:42:47,593 INFO [Analyzer] 完成 4/14 条
2026-05-07 22:43:04,900 INFO HTTP Request: POST https://api.minimax.chat/v1/chat/completions "HTTP/1.1 200 OK"
2026-05-07 22:43:04,903 INFO [Analyzer] 完成 5/14 条
2026-05-07 22:43:18,674 INFO HTTP Request: POST https://api.minimax.chat/v1/chat/completions "HTTP/1.1 200 OK"
2026-05-07 22:43:18,721 INFO [Analyzer] 完成 6/14 条
2026-05-07 22:43:32,330 INFO HTTP Request: POST https://api.minimax.chat/v1/chat/completions "HTTP/1.1 200 OK"
2026-05-07 22:43:32,335 INFO [Analyzer] 完成 7/14 条
2026-05-07 22:43:56,940 INFO HTTP Request: POST https://api.minimax.chat/v1/chat/completions "HTTP/1.1 200 OK"
2026-05-07 22:43:56,988 INFO [Analyzer] 完成 8/14 条
2026-05-07 22:44:10,643 INFO HTTP Request: POST https://api.minimax.chat/v1/chat/completions "HTTP/1.1 200 OK"
2026-05-07 22:44:10,656 INFO [Analyzer] 完成 9/14 条
2026-05-07 22:44:24,037 INFO HTTP Request: POST https://api.minimax.chat/v1/chat/completions "HTTP/1.1 200 OK"
2026-05-07 22:44:24,039 INFO [Analyzer] 完成 10/14 条
2026-05-07 22:44:40,703 INFO HTTP Request: POST https://api.minimax.chat/v1/chat/completions "HTTP/1.1 200 OK"
2026-05-07 22:44:40,755 INFO [Analyzer] 完成 11/14 条
2026-05-07 22:44:57,282 INFO HTTP Request: POST https://api.minimax.chat/v1/chat/completions "HTTP/1.1 200 OK"
2026-05-07 22:44:57,285 INFO [Analyzer] 完成 12/14 条
2026-05-07 22:45:10,640 INFO HTTP Request: POST https://api.minimax.chat/v1/chat/completions "HTTP/1.1 200 OK"
2026-05-07 22:45:10,693 INFO [Analyzer] 完成 13/14 条
2026-05-07 22:45:27,824 INFO HTTP Request: POST https://api.minimax.chat/v1/chat/completions "HTTP/1.1 200 OK"
2026-05-07 22:45:27,834 INFO [Analyzer] 完成 14/14 条
2026-05-07 22:45:27,834 INFO [Analyzer] 分析完成，共 14 条，cost=¥0.0162
2026-05-07 22:45:27,850 INFO [Event] Node: analyze, node_state type: dict, value: {'analyses': [{'summary': '免费编程书籍聚合仓库，收录了涵盖多语言、多领域的数千本免费技术书籍和教程资源', 'tech_stack': ['多语言支持', 'Markdown文档', 'GitHub协作'], 'tags': ['免费资源', '编程学习', '技术文档', '开源社区', '电子书汇总'], 'problem_solved': '解决程序员学习编程时寻找优质免费学习资源困难的问题，提供了一个集中、分类清晰的免费技术书籍索引平台', 'why_valuable': '拥有超过38万stars的极高人气，是全球最大的免费编程学习资源库之一，持续由社区维护更新，覆盖从入门到高级的各层次技术内容，极大降低了编程学习的经济门槛', 'category': 'tool', 'relevance_score': 0.55}, {'summary': 'TensorFlow是Google开源的端到端机器学习框架，提供从数据处理、模型构建、训练到部署的全流程工具支持。', 'tech_stack': ['Python', 'C++', 'CUDA', 'Bazel', 'NumPy', 'Keras'], 'tags': ['深度学习', '机器学习', '神经网络', 'TensorFlow', 'Google开源', '端到端平台'], 'problem_solved': '降低机器学习开发门槛，提供统一的API接口解决从实验到生产的全链路问题，支持大规模分布式训练和跨平台部署。', 'why_valuable': '作为全球最流行的ML框架之一，拥有19.5万stars的庞大社区、丰富的预训练模型生态和企业级生产支持，是AI技术普及和工业落地的核心基础设施。', 'category': 'framework', 'relevance_score': 0.95}, {'summary': '一个AI代码助手代理框架的性能优化系统，支持Claude Code、Codex、Cursor等多平台，专注于技能管理、记忆机制、安全性和研究驱动的开发模式。', 'tech_stack': ['Agent Framework', 'Python', 'Performance Optimization', 'AI Code Assistant', 'Memory Management', 'Security Layer'], 'tags': ['AI代理优化', '代码助手框架', '性能工程', '多模型支持', '安全开发', '研究驱动开发', '记忆系统'], 'problem_solved': '解决AI代码助手代理的性能瓶颈、记忆管理效率低下、安全风险以及技能调用混乱等问题，提供统一的优化框架和开发规范。', 'why_valuable': '拥有超过17.5万星标的高人气项目，兼容主流AI编程工具生态，通过系统化的方法论提升代理运行效率，降低开发者在AI辅助编程中的使用门槛和出错率。', 'category': 'agent', 'relevance_score': 0.92}, {'summary': 'Hugging Face Transformers是全球最流行的开源机器学习模型框架，提供预训练的NLP、CV、音频和多模态SOTA模型，支持PyTorch、TensorFlow等多框架统一API调用。', 'tech_stack': ['Python', 'PyTorch', 'TensorFlow', 'JAX', 'Transformers架构', 'Tokenizer', 'Datasets库', '深度学习框架'], 'tags': ['预训练模型', '自然语言处理', '计算机视觉', '音频处理', '多模态AI', '模型框架', '迁移学习', '开源ML库'], 'problem_solved': '解决AI模型使用门槛高的问题，提供预训练模型库和统一API，让开发者无需从头训练即可快速使用和微调SOTA模型，降低研究和生产部署成本。', 'why_valuable': '拥有16万+ stars的顶级开源生态，是AI领域事实标准框架，生态覆盖模型 Hub、数据集、Tokenizers等完整工具链，极大加速AI应用开发进程。', 'category': 'framework', 'relevance_score': 0.98}, {'summary': 'Airbnb 维护的 JavaScript 编码风格规范指南，是业界最受欢迎的 JavaScript 最佳实践参考', 'tech_stack': ['JavaScript', 'ESLint', 'Node.js', '前端开发', '后端开发'], 'tags': ['代码规范', '风格指南', '编码最佳实践', 'JavaScript', '代码质量', 'ESLint配置', '可维护性'], 'problem_solved': '解决团队协作中代码风格不一致的问题，提供统一的编码规范，帮助开发者编写一致、可读、可维护的 JavaScript 代码', 'why_valuable': '拥有超过 14.8 万颗星标，是 JavaScript 领域最流行的风格指南，被众多企业和开源项目采用，显著提升代码质量和团队协作效率', 'category': 'tool', 'relevance_score': 0.7}, {'summary': 'NousResearch 开源的模块化 AI Agent 框架，具备工具调用、任务规划和持续学习能力的高性能自主智能体。', 'tech_stack': ['Python', 'LLM', 'Tool Calling', 'ReAct 范式', 'LangChain 生态'], 'tags': ['AI Agent', '自主智能体', '工具调用', '任务规划', '大语言模型', '开源 AI'], 'problem_solved': '为开发者提供开箱即用的 Agent 开发框架，解决构建 AI Agent 时的复杂工程问题，包括工具调用、记忆管理、多步骤推理等核心能力。', 'why_valuable': 'Stars 数超过 137k 说明其极高的社区认可度，提供了成熟稳定的 Agent 开发范式，降低了 AI Agent 的开发门槛，且支持灵活扩展和定制，是当前最流行的开源 Agent 框架之一。', 'category': 'agent', 'relevance_score': 0.92}, {'summary': 'Kubernetes是Google开源的生产级容器编排平台，用于自动化容器化应用的部署、扩展、负载均衡和运维管理', 'tech_stack': ['Go语言', 'Docker/容器技术', 'etcd分布式存储', 'RESTful API', 'YAML/JSON配置', 'cgroups命名空间隔离', '云原生生态'], 'tags': ['容器编排', '云原生', '微服务', 'DevOps', '自动化运维', '服务发现', '负载均衡', '弹性伸缩'], 'problem_solved': '解决大规模容器集群的手动管理难题，提供自动化部署、扩缩容、自愈、负载均衡和服务发现等能力', 'why_valuable': '作为云原生时代的标准基础设施，大幅降低微服务运维复杂度，是现代AI/ML应用部署的核心平台，具有高可用、自动恢复和可扩展特性', 'category': 'framework', 'relevance_score': 0.35}, {'summary': '微软官方发布的生成式AI入门教程，通过21节系统性课程帮助初学者掌握生成式AI开发技能', 'tech_stack': ['Generative AI', 'Large Language Models', 'Prompt Engineering', 'Azure OpenAI', 'Python', 'ChatGPT'], 'tags': ['生成式AI', '入门教程', '微软官方', '教育', 'LLM', 'Prompt工程', '开源课程'], 'problem_solved': '降低生成式AI学习门槛，为开发者提供系统化、结构化的入门路径，避免初学者在浩繁资料中迷失方向', 'why_valuable': '微软官方背书确保内容权威性，11万+星标验证了极高的社区认可度，21节课程循序渐进配含实战代码，是目前最受欢迎的生成式AI入门资源之一', 'category': 'tool', 'relevance_score': 0.85}, {'summary': 'DeepSeek-V3是由DeepSeek AI开源的大规模语言模型，采用MoE架构，拥有超过6000亿参数，在多项评测中达到国际领先水平。', 'tech_stack': ['Transformer', 'MoE (Mixture of Experts)', 'PyTorch', 'Deep Learning', 'LLM', '预训练/微调'], 'tags': ['开源大语言模型', 'MoE架构', 'DeepSeek', 'AI模型', 'NLP', '生成式AI'], 'problem_solved': '为研究者和开发者提供高性能开源LLM，降低AI应用开发门槛，减少对闭源模型的依赖。', 'why_valuable': '开源且性能接近GPT-4等顶级闭源模型，星标超10万证明其技术领先性和社区广泛认可，对AI民主化有重要意义。', 'category': 'llm', 'relevance_score': 0.95}, {'summary': 'PyTorch 是 Facebook/Meta 维护的主流深度学习框架，以 Python 实现张量计算和动态神经网络，提供强大的 GPU 加速能力。', 'tech_stack': ['Python', 'CUDA/GPU加速', '张量计算 (Tensor)', '动态计算图', '自动微分 (Autograd)', '神经网络模块 (nn.Module)', '优化器 (optim)', '分布式训练', 'TorchScript'], 'tags': ['深度学习框架', '张量计算', 'GPU加速', '神经网络', '自动微分', '开源框架', 'Python生态'], 'problem_solved': '解决深度学习模型开发中面临的张量运算效率、GPU资源利用、模型快速迭代和自动梯度计算等问题，降低深度学习研究和应用的门槛。', 'why_valuable': 'PyTorch 是全球最流行的深度学习框架之一，拥有庞大的社区生态和丰富的预训练模型库。其动态图特性使调试直观方便，灵活的架构设计支持从研究原型到生产部署的完整流程，是现代 AI 开发的核心基础设施。', 'category': 'framework', 'relevance_score': 0.98}, {'summary': '一个多专业AI代理平台，提供前端开发、社交媒体运营、内容创作等领域的专项代理服务，各代理具有独特个性和工作流程。', 'tech_stack': ['Python', 'AI Agent', 'Multi-Agent System', 'LLM Integration', 'Task Automation'], 'tags': ['AI代理', '多代理系统', '自动化', '专业代理', '人工智能团队', '工作流自动化'], 'problem_solved': '提供即用型AI代理团队，涵盖前端开发、社交媒体运营、内容创作等场景，避免从零构建多个专业AI助手的重复工作。', 'why_valuable': '拥有近10万stars的高人气项目，封装了多个经过验证的专业AI代理，支持快速集成到各类应用场景，大幅提升开发和运营效率。', 'category': 'agent', 'relevance_score': 0.92}, {'summary': '用PyTorch从零实现类ChatGPT大语言模型的详细教程项目，通过逐步步骤帮助理解LLM内部原理', 'tech_stack': ['Python', 'PyTorch', '深度学习', 'Transformer', '神经网络', '自注意力机制'], 'tags': ['大模型从零实现', 'PyTorch', 'Transformer架构', '深度学习', 'LLM教程', 'NLP'], 'problem_solved': '帮助开发者从底层理解大型语言模型的工作原理，不依赖任何第三方LLM库，从零构建完整的LLM', 'why_valuable': '通过92K+ stars证明了极高的受欢迎程度，提供了极其清晰的逐步教程，系统讲解LLM核心技术（嵌入、注意力、位置编码、训练等），是理解现代LLM架构的最佳实践资源', 'category': 'framework', 'relevance_score': 0.95}, {'summary': 'DeepSeek-R1是中国深度求索公司开源的推理大语言模型，专注于复杂推理能力提升，对标OpenAI o1，拥有超过92k星标。', 'tech_stack': ['深度学习', 'Transformer架构', '大语言模型(LLM)', '推理强化学习', 'Python', 'PyTorch'], 'tags': ['开源大模型', '推理模型', 'DeepSeek', 'AI推理', '深度学习', '自然语言处理'], 'problem_solved': '解决复杂推理任务，包括数学问题求解、代码生成、逻辑推理等，提供开源免费的强推理能力模型。', 'why_valuable': 'DeepSeek-R1是目前最强大的开源推理模型之一，性能对标OpenAI o1但完全开源免费，极大降低了强推理AI的获取门槛，推动了开源AI社区的发展和推理能力研究的进步。', 'category': 'llm', 'relevance_score': 0.95}, {'summary': '一个通过类Markdown文本语法生成流程图、时序图、甘特图等多种图表的开源图表绘制库', 'tech_stack': ['JavaScript', 'TypeScript', 'D3.js', 'SVG'], 'tags': ['图表生成', '流程图', '时序图', '文本转图表', '文档工具', '可视化'], 'problem_solved': '解决了使用复杂图形工具创建图表的问题，允许开发者通过简单的文本描述快速生成专业的图表，并方便集成到文档、网页和README中', 'why_valuable': '通过文本方式创建图表降低了技术门槛，支持版本控制，便于团队协作，在GitHub上拥有超过87K星的高人气，广泛应用于技术文档编写和API文档中', 'category': 'tool', 'relevance_score': 0.35}], 'cost_tracker': {'prompt_tokens': 2553, 'completion_tokens': 6828, 'total_cost_yuan': 0.016209}}
2026-05-07 22:45:27,852 INFO   → 分析完成 14 条，cost=¥0.0162
2026-05-07 22:45:27,852 INFO [Organizer] 开始组织 14 条数据（iteration=0）...
2026-05-07 22:45:27,852 INFO [Organizer] 过滤后（score>=0.6）：11 条
2026-05-07 22:45:27,852 INFO [Organizer] 去重后：1 条（移除 10 条重复）
2026-05-07 22:45:27,853 INFO [Organizer] 组织完成，共 1 条待审文章
2026-05-07 22:45:27,853 INFO [Event] Node: organize, node_state type: dict, value: {'articles': [{'summary': 'Hugging Face Transformers是全球最流行的开源机器学习模型框架，提供预训练的NLP、CV、音频和多模态SOTA模型，支持PyTorch、TensorFlow等多框架统一API调用。', 'tech_stack': ['Python', 'PyTorch', 'TensorFlow', 'JAX', 'Transformers架构', 'Tokenizer', 'Datasets库', '深度学习框架'], 'tags': ['预训练模型', '自然语言处理', '计算机视觉', '音频处理', '多模态AI', '模型框架', '迁移学习', '开源ML库'], 'problem_solved': '解决AI模型使用门槛高的问题，提供预训练模型库和统一API，让开发者无需从头训练即可快速使用和微调SOTA模型，降低研究和生产部署成本。', 'why_valuable': '拥有16万+ stars的顶级开源生态，是AI领域事实标准框架，生态覆盖模型 Hub、数据集、Tokenizers等完整工具链，极大加速AI应用开发进程。', 'category': 'framework', 'relevance_score': 0.98, 'id': '2026-05-07-000'}]}
2026-05-07 22:45:27,853 INFO   → 整理完成 1 条待审
2026-05-07 22:45:27,854 INFO [Reviewer] 开始审核 1 条数据（iteration=0）...
2026-05-07 22:45:43,198 INFO HTTP Request: POST https://api.minimax.chat/v1/chat/completions "HTTP/1.1 200 OK"
2026-05-07 22:45:43,243 INFO [Reviewer] 审核完成：passed=True, overall_score=0.82
2026-05-07 22:45:43,243 INFO [Reviewer] 各维度得分: summary=0.80 tags=0.75 category=0.95 consistency=0.80
2026-05-07 22:45:43,244 INFO [Router] review_passed=True, iteration=1
2026-05-07 22:45:43,244 INFO [Event] Node: review, node_state type: dict, value: {'review_passed': True, 'review_feedback': '该条目整体质量较好，但存在以下可优化点：\n1. 摘要可补充生态完整性（如Hub、Tokenizers、Datasets等组件）；\n2. 标签缺少核心的"Transformers架构"标签，建议添加；\n3. tech_stack中的JAX未在摘要中体现，可保持一致或在摘要中补充；\n4. "音频处理"标签建议更精确为"语音处理"或"音频/语音"以符合业界惯例。', 'iteration': 1, 'cost_tracker': {'prompt_tokens': 3015, 'completion_tokens': 7499, 'total_cost_yuan': 0.018013}}
2026-05-07 22:45:43,245 INFO   → 审核结果: passed=True, iteration=1, feedback=该条目整体质量较好，但存在以下可优化点：
1. 摘要可补充生态完整性（如Hub、Tokenizers
2026-05-07 22:45:43,245 INFO [Saver] 开始保存 1 条文章...
2026-05-07 22:45:43,247 INFO [Saver] 已保存: 2026-05-07-000
2026-05-07 22:45:43,248 INFO [Saver] 保存完成，共 1 条，已更新索引
2026-05-07 22:45:43,249 INFO [Event] Node: save, node_state type: NoneType, value: None
2026-05-07 22:45:43,249 INFO 工作流执行完毕
```