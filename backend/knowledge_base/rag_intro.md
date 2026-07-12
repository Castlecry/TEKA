# RAG 技术详解

## 什么是 RAG

检索增强生成（Retrieval-Augmented Generation，RAG）是一种将信息检索与大语言模型相结合的技术范式。它由 Facebook AI Research（FAIR）团队于 2020 年提出，旨在解决大语言模型在知识更新和事实准确性方面的不足。

## RAG 的工作原理

RAG 系统通常包含以下核心组件：

1. **文档解析**：将 PDF、Word、PPT 等格式的文档转换为纯文本或 Markdown
2. **文本切片**：将长文档切分为适当大小的片段（chunk）
3. **向量嵌入**：使用嵌入模型（如 nomic-embed-text）将文本片段转换为高维向量
4. **向量存储**：将向量存入向量数据库（如 OpenSearch、Milvus、Chroma）
5. **语义检索**：根据用户查询的向量，在数据库中检索最相似的文档片段
6. **生成回答**：将检索结果作为上下文，由 LLM（如 qwen3.5）生成最终回答

## RAG 的优势

- **减少幻觉**：基于真实文档回答，降低模型编造信息的风险
- **知识更新**：无需重新训练模型，更新文档库即可获取最新知识
- **可追溯性**：可以追溯回答的信息来源，提高可信度
- **成本控制**：相比微调（Fine-tuning），RAG 的部署和维护成本更低
- **领域适配**：可以快速适配不同领域的知识库

## RAG 的常见架构

### 基础 RAG（Naive RAG）
最简单的 RAG 架构：文档 → 切片 → 嵌入 → 存储 → 检索 → 生成

### 高级 RAG（Advanced RAG）
在基础 RAG 上增加：
- 查询重写（Query Rewriting）
- 重排序（Reranking）
- 混合检索（Hybrid Search：向量 + 关键词）

### 模块化 RAG（Modular RAG）
将 RAG 流程拆分为独立模块，支持灵活组合：
- 路由模块：决定是否需要检索
- 检索模块：从多个数据源检索
- 生成模块：整合信息生成回答

## 常用工具和技术栈

| 组件 | 工具 |
|------|------|
| 文档解析 | MinerU、Unstructured、PyPDF2 |
| 文本切片 | LangChain TextSplitter、自定义切片 |
| 向量嵌入 | nomic-embed-text、text-embedding-ada-002 |
| 向量数据库 | OpenSearch、Milvus、Chroma、Qdrant |
| 大语言模型 | qwen3.5、GPT-4、Llama 3 |
| 联网搜索 | SearXNG、Tavily、DuckDuckGo |
| 应用框架 | LangChain、LlamaIndex、FastAPI |

## RAG 的应用场景

1. **企业知识库问答**：员工通过自然语言查询公司文档
2. **智能客服**：基于产品文档自动回答客户问题
3. **学术研究助手**：检索论文库并生成综述
4. **法律文档分析**：检索相关法条和案例
5. **医疗问答系统**：基于医学文献提供健康建议
