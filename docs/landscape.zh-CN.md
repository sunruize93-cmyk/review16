# Review16：项目调研与可验证的差异化

调研日期：**2026-09-17**。GitHub stars 通过各仓库官方 API 的
`stargazers_count` 字段读取，快照时间 **04:05 UTC**。Stars 只是一时的关注度快照，
不代表审稿准确性、实际用户数或工程质量；下面不是完整排行榜。

首版范围是 **AI/ML 顶会论文的作者投稿前审查**。数据链路优先做 ICLR / OpenReview；
ICML、NeurIPS 或其他 venue 必须分别核验年份、rubric、公开数据覆盖和评分阶段，
不能沿用一套假定通用的 1–10 分制。

## 相关项目

| 官方项目 | Stars 快照 | 已有能力与可借鉴之处 |
|---|---:|---|
| [Scientific Agent Skills](https://github.com/K-Dense-AI/scientific-agent-skills) | 45,263 | 一条安装命令、多宿主支持、分类目录、视频教程、脚本测试和 CI；已有 peer-review skill。 |
| [AI Research Skills](https://github.com/Orchestra-Research/AI-Research-SKILLs) | 12,753 | README 首屏动图、安装器、真实 demo 仓库、按需 references；已有研究严谨性 reviewer。 |
| [Research Paper Writing Skills](https://github.com/Master-cai/Research-Paper-Writing-Skills) | 6,881 | 聚焦 ML/CV/NLP，中英 README，方法论来源说明，简洁入口与章节参考资料。 |
| [PaperJury](https://github.com/Spark-To-Paper-Skills/paperjury) | 1,189 | 直接竞品：领域 reviewer、独立审阅、证据定位、争议裁定、修订复查、确定性状态管理。 |
| [AgentReview](https://github.com/Ahren09/AgentReview) | 412 | EMNLP 2024 官方实现，配置 reviewer 特征，模拟 reviewer / author / AC 讨论，提供数据、Notebook 和在线 demo。 |
| [Agent Reviewers](https://github.com/AReviewers/AgentReviewers) | 5 | ICML 2025 官方仓库，介绍领域背景、多模态 reviewer 和历史记忆；当日 README 仍称代码即将公开，不等于已有可运行实现。 |
| [Review Feedback Agent](https://github.com/zou-group/review_feedback_agent) | 35 | 对审稿意见的具体性、可行动性提供反馈，并附可靠性检查。可借鉴为审稿质量复查层。 |
| [The AI Scientist](https://github.com/SakanaAI/AI-Scientist) | 14,562 | 可独立调用 reviewer，支持 ensemble / reflection，提供 ICLR 批量评测入口及运行材料。 |

每个表格链接都是项目原始仓库。可在 GitHub 官方 REST endpoint
`https://api.github.com/repos/<owner>/<repo>` 更新 stars；更新时应保留日期，
不要把上述数字写成长期固定的宣传事实。能力描述来自项目文档，未据此认定其效果已被独立验证。

## 多角色和对抗审查已有先例

不能声称 Review16 是首个人格审稿、多 agent 审稿或对抗式审稿工具。
PaperJury 已把领域 reviewer、引文证据、阅读覆盖、争议裁定与修订状态结合在一起，
并提供完整运行展示。[项目 README](https://github.com/Spark-To-Paper-Skills/paperjury)

其 [reviewer personas 文档](https://github.com/Spark-To-Paper-Skills/paperjury/blob/main/references/reviewer-personas.md)
规定默认三位领域专家，按论文子领域分配，独立通读全文；人格由通用要求、领域 overlay 和 venue profile 组成。
它明确区分实际论文缺陷与 AI 误读，并审计审稿意见是否有原文依据。
这是可以借鉴的工程实践，不是“更多角色一定没有帮助”的实验定论。

[AgentReview](https://github.com/Ahren09/AgentReview) 已研究可配置 reviewer 特征和多阶段讨论；
[Agent Reviewers](https://github.com/AReviewers/AgentReviewers) 已提出领域背景与共享记忆。
因而，16 张角色卡是识别度设计，真正需要验证的是这些角色是否带来互补、正确且有用的判断。

## 建议的项目定位

> A calibrated review panel that shows where your paper stands—and why different research communities disagree.

这里的 calibrated 是待验证的设计目标。未完成公开评测时，README 必须写明实验性状态，
不能用“最强”“准确预测录用”或“消灭 6 分问题”代替证据。

Review16 可以集中在三个可核验的能力上：

1. **有来源的参考集相对位置。** 依据同 venue、年份、子领域和评审阶段建立参考集；
   隐藏历史评分与结果，让目标稿和参考稿共同参与顺序随机化的成对判断。
   参考集内百分位不能直接叫总体排名或录用概率。
2. **16 种关联视角的分歧地图。** 用四个二元轴的笛卡尔积定义 16 类型：
   D/E（演绎 / 实证）、I/U（解释 / 效用）、G/C（通用 / 情境）、N/R（探索 / 稳健）。
   每个类型都能沿一个轴找到相邻类型，也能找到四轴全反的对照类型；
   用 Hamming 邻居和对照分配交审，使“为什么两位 reviewer 分歧”有具体解释。
   每个角色公布关切、证据门槛、适用范围和盲点；
   分别报告评价、置信信息与弃权，不把领域外 reviewer 的弱判断当成同等质量的投票。
   喜好差异是诊断信号，不是经过验证的投稿推荐。
   AI/ML 领域专长独立作为多对多映射，不能把一个类型固定等同理论、视觉或 NLP。
   四轴是设计词汇，不宣称它们具有经过验证的心理学意义或统计独立性。
3. **证据约束的争议裁定。** 优点与缺点均绑定 claim、位置和证据；
   将事实矛盾、适用条件不同、价值偏好不同分别处理，保留合理分歧，不强制各方平均为 6 分。

原创建模的人像可以成为 README 的传播入口。视觉应有一致但独立的设计，
不要复制现成 MBTI 商业角色画面，也不要把这套研究视角宣传成心理测量工具。

## 公开 benchmark 发展策略

### 第一阶段：先让失败可复现

- 冻结 venue / year / phase 与参考集 manifest；人工核验 submission-time PDF、评分来源和缺失情况。
- 划分开发集与不参与 prompt 调整的留出集；避免同一论文的修订版本跨集合泄漏。
- 记录模型版本、prompt 版本、随机顺序、token、耗时与费用。
- 先发布小而完整的评测，展示失败案例；预埋缺陷稿只能测特定诊断能力，不能证明自然论文录用预测能力。

### 第二阶段：验证 16 个角色的增量

相同论文集合和预先声明的预算规则下，对比：

| 对照 | 主要回答的问题 |
|---|---|
| 单个通用 reviewer | 基础能力如何？ |
| 同一通用 reviewer 的重复采样 | 改善是否只是更多计算？ |
| 16 个独立角色，无讨论 | 角色是否带来有效互补？ |
| 独立角色加参考集成对比较 | 相对判断是否改善排序？ |
| 加入证据复核与有限讨论 | 是否减少误读？是否损失合理分歧？ |

至少包含：人工核验的错误批评率、关键问题召回、建议可行动性、成对排序与历史结果的一致度、
交换呈现顺序后的稳定性、重复运行稳定性、成本。置信区间按独立论文/参考样本重采样，
不要把同模型 16 个角色当作 16 个独立人类样本。

历史评分和最终录用仅是噪声标签，不能自动等同论文质量真值。
模型可能认识公开论文，匿名化不能保证去除训练记忆；应披露重识别与版本污染检查。
先报告相对排序及其不确定性。只有在额外独立留出数据上验证映射、覆盖与稳定性后，
再讨论与具体 venue / year 绑定的录用概率估计。

### 第三阶段：用可检查报告传播

README 首屏采用 16 人原创角色总览和一张真实报告截图。
紧接着给三步使用方法、完整示例、评测表和局限。
示例应展示至少一条被证据驳回的 AI 批评及一处无法裁定的争议。
高星库值得借鉴的是清晰入口、可运行示例、版本与安装维护；不能推断这些元素一定带来 stars。

## OpenReview 最小可执行入口

首版提供只读取一个公开 forum 的标准库脚本：

```bash
python skills/review16/scripts/fetch_openreview.py \
  --forum AC5n7xHuR1 --out /tmp/review16-openreview-example
```

该 ID 对应公开的 [AgentHarm forum](https://openreview.net/forum?id=AC5n7xHuR1)。
脚本仅请求 API2 的当前 submission、论坛 notes 和 submission edits，不下载 PDF；
不读取密钥、不需要账号、无自动重试。每个集合至多 3 页、每页 100 条，每次响应至多 8 MiB。
输出目录必须是新目录，以保护已有快照。

`metadata.json` 保留原评分字段、原值、venue 字段、时间戳及 PDF 候选来源。
字段名匹配只是候选识别，不推断评分制或初审/终审阶段。
`submission_version_verified` 始终为 `false`，必须另行审计版本证据；
submission edits 可能是局部修改，脚本也没有抓取 reviewer note 的完整改分历史。
原始快照含身份、历史分数和决策信息，必须留在校准管理员一侧，不能交给盲审角色。

API 不可访问时，脚本写出真实错误与 `status: unavailable`，以非零码退出，
不能把空数据伪装成成功。公开 API smoke 测试和单测通过是两类不同证据。

**本次 smoke 记录（2026-09-17）：** 对上述真实 forum 的匿名 API 请求返回 HTTP 403，
脚本以退出码 2 保存失败快照；网页入口也出现浏览器验证页。
因此本次只验证了离线解析、分页边界和真实联网失败降级，尚未验证成功获取在线 forum 的完整链路。
测试产物保存在 `/tmp`，没有向仓库提交第三方全文或真实审稿文本。

实现依据是 OpenReview 官方 [API2 endpoint 文档](https://docs.openreview.net/reference/api-v2/openapi-definition)、
[按 forum 获取 notes 的指南](https://docs.openreview.net/how-to-guides/data-retrieval-and-modification/how-to-get-all-notes-for-submissions-reviews-rebuttals-etc)
和 [Edits 说明](https://docs.openreview.net/getting-started/objects-in-openreview/introduction-to-edits)，
均于 2026-09-17 核验。公开可访问不自动授予再分发全文的权利；仓库只提交工具与合成测试样本。


**真实论文备用渠道实测：** 同日通过 AllenAI PeerRead 的固定 Git 提交成功下载 ICLR 2017 论文与原始推荐分，并在 OpenReview 官方历史脚本中核对评分量表。该档案缺少足以核验论文修订版与评分阶段一致性的版本记录，因此只用于真实稿件审稿与来源审计，没有冒充已校准的历史锚点。见[公开实测记录](../examples/real-paper/README.md)。
