# 现成方案调研：考点预测

> 调研日期：2026-10-09
> 问题：有没有现成的"考点预测"算法可以直接用？

## 结论（先说答案）

**没有开箱即用的通用考点预测算法。** 原因不是技术不行，而是**问题定义本身高度依赖具体场景**——不同学校、不同课程、不同老师的出题偏好差异太大，无法训练一个通用模型。

但有**三类可直接复用的资源**，以及**几个思路相近的现成项目**。

## 关键区分：两个容易混淆的问题

| | 知识追踪（Knowledge Tracing） | 考点预测（本项目） |
|---|---|---|
| **输入** | 大量学生的答题记录 | 历年试卷 + 课件 |
| **输出** | 某学生答对下一题的概率 | 今年会考哪些知识点 |
| **数据量** | 需上万条交互记录 | 几份试卷（几十道题） |
| **建模对象** | 学生 | 课程内容 |
| **学术热度** | 极高（IEEE TLT 综述级） | 低（无标准问题定义） |

**知识追踪是当前教育 AI 的主流方向，但它解决的不是我们的问题。** 而且它需要的数据我们完全没有（没有学生的历史答题数据）。

## 现成项目清单

### 1. hanhan761/class-SignalScore — 智能考点预测系统

- **思路**：把考点按「信号强度 × 认知深度」二维打分，分三类输出：
  - 必考高危区（高信号 + 高深度 → 预测大题）
  - 普通掌握区（基础考点 → 预测小题）
  - 已过滤内容（判定"不考"，附理由）
- **技术栈**：Streamlit + DeepSeek API + Instructor（结构化输出）+ Plotly
- **与本项目的关系**：**思路最接近**。核心是 LLM 提取 + 负向过滤（先判断"不考"再判断"考"）
- 参考价值：★★★★★（可直接借鉴评分维度设计）

### 2. namanipie/MarkMint — 考试资料分析平台

- **思路**：摄取历年试卷 → 提取结构化元数据 → "ExamDNA" + "MintAI" 预测重点主题
- **技术栈**：Next.js + FastAPI + PostgreSQL + sentence-transformers + PyMuPDF + easyocr
- **特点**：前后端分离、可本地运行、有完整工程化方案
- 参考价值：★★★☆☆（工程架构可借鉴，但它是 Web 平台，与本项目"不做网站"的定位不同）

### 3. jiangnanboy/knowledge-automatic-tagging — 试题知识点标注

- **思路**：把"给题目打知识点标签"建模为**多标签文本分类**
- **技术栈**：TextCNN / Transformer-Encoder + torchtext + 搜狗预训练词向量
- **数据**：高中 4 科目、29000+ 题目、73 个知识点
- **与本项目的关系**：这是**上游任务**——先把题目映射到知识点，才能统计考点分布
- 参考价值：★★★★☆（如果未来要做"题目 → 知识点"的自动标注，这是现成的实现参考）

### 4. jiangnanboy/education_knowledge_graph_app — 教育知识图谱

- **思路**：用 Neo4j 建"知识点-题目"图谱，支持追踪、查询、推断
- **技术栈**：Django + PyTorch + Neo4j
- 参考价值：★★★☆☆（图谱化适合知识点间有明确层级关系的学科）

## 可复用的算法组件

我们的方案不需要发明算法，只需组合成熟组件：

| 环节 | 推荐组件 | 说明 |
|---|---|---|
| 中文分词 | **jieba** | 事实标准，轻量；加自定义词典可识别专业术语 |
| 关键词提取 | **TF-IDF**（scikit-learn）/ **KeyBERT** / **YAKE** | TF-IDF 最轻；KeyBERT 语义质量更高但需模型 |
| 关联度计算 | **TextRank**（summa / pytextrank） | 共现图 + 迭代权重，无需训练 |
| 语义相似度 | **sentence-transformers**（如 `text2vec-base-chinese`） | 判断两个考点是否同一概念 |
| 主题聚类 | **BERTopic** / **gensim LDA** | 把分散的关键词聚成"考点簇" |
| 出题 + 解释 | 本地 LLM | 我们的差异化在这里：**给 rationale** |

**全部无需训练**，开箱可用。

## 我们的方案定位

```
历年真题 ──┐
          ├─→ [1] 知识点/关键词提取（TF-IDF + jieba）
课件 PPT ──┤   [2] 关联度与共现（TextRank + 共现矩阵）
          │   [3] 时序加权（近 N 年权重更高）
          └─→ [4] 语义聚类（BERTopic，可选）
              [5] LLM 归纳 + 出题 + 解释 rationale
              → 预测试卷
```

**为什么不用知识追踪类模型**：
1. 需要学生答题记录，我们没有
2. 需要上万条样本训练，我们只有几十道题
3. 目标不同：它预测"学生会不会做"，我们预测"老师会考什么"

**为什么这个组合是务实的**：
- 每个组件都成熟、无训练、轻量
- 「频次 + 时序 + 语义」三个维度足以覆盖大多数出题规律
- 差异化的重点放在**可解释性**（rationale），而不是模型复杂度

## 引用

- [Knowledge Tracing 综述（IEEE TLT 2024）](https://dlnext.acm.org/doi/10.1109/tlt.2024.3383325) — 含开源库 EduData / EduKTM
- [class-SignalScore](http://github.com/hanhan761/class-SignalScore) — 考点预测系统（LLM 驱动）
- [knowledge-automatic-tagging](https://github.com/jiangnanboy/knowledge-automatic-tagging) — 试题知识点多标签分类
- [MarkMint](https://kaiyuanbang.cn/zh-cn/repo/namanipie-markmint.html) — 考试资料分析平台
- [education_knowledge_graph_app](https://github.com/jiangnanboy/education_knowledge_graph_app) — 教育知识图谱
