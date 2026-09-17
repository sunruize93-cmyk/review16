# Review16

**一篇论文，16 种有关联的审稿视角。每处分歧，都能回到证据。**

[English](README.md) · [真实论文实测](examples/real-paper/README.md) · [详细用法](docs/guide.md) · [MIT 开源协议](LICENSE)

Review16 是面向 **AI/ML 论文投稿前自查**的 skill。它让你的 AI 启动 16 个独立 reviewer，做一轮交叉质询，再生成包含每位 reviewer 分数、证据和修改建议的可视化报告。

![四个维度组合出的16种审稿类型](skills/review16/assets/reviewer-atlas.png)

## 三步上手

**1. 安装到 Codex**（需要 Python 3.9+）：

```bash
git clone https://github.com/sunruize93-cmyk/review16.git
cd review16
python3 install.py
```

安装器不会覆盖已有版本。安装后新开一个 Codex 会话；宿主需支持 subagent，可以每批运行 3 位 reviewer。

**2. 附上论文，复制这句话：**

> 用 $review16 审这篇论文，目标是【会议、年份、track】。运行全部 16 位 reviewer 和一轮交叉质询，展示各自评分、分歧与最值得做的三项修改。有可靠的公开历史数据时，再加入论文匿名混排定位。

**3. 打开生成的 HTML 报告。** 点击人像就能查看该类型的分数、证据和相邻类型。你不需要手动开 16 个 agent。

## 审完能得到什么

- **16 份独立初审：** 每人的初评分、质询后分数、证据与置信度。
- **分歧解释：** 哪些是误读，哪些是适用范围不同，哪些是研究偏好不同。
- **三项优先修改：** 根据证据作出判断，不机械平均 16 个分数。
- **可选历史定位：** 数据足够且版本可核验时，展示在历史参照集中的位置区间。

## 16 个类型有什么关联

四组偏好组合成 **2 × 2 × 2 × 2 = 16** 个类型：

| 维度 | 两端偏好 |
|---|---|
| 证据 | **D 演绎** ↔ **E 实证** |
| 贡献 | **I 解释** ↔ **U 效用** |
| 范围 | **G 通用** ↔ **C 情境** |
| 研究风险 | **N 探索** ↔ **R 稳健** |

每个类型有 **4 个只差一轴的邻居**和 **1 个四轴相反的对照类型**。例如 DIGN 与 DIGR 只在探索/稳健上不同，DIGN 与 EUCR 则互相质询。所有类型使用相同的论文领域和正确性底线。[查看完整关系 →](skills/review16/references/types.md)

## 先看看效果

[真实论文实测与全部分数](examples/real-paper/README.md) · [界面演示（合成数据，下载后打开）](examples/report.html)

这是实验性的作者辅助工具。16 种角色不等于 16 位独立人类专家，分数更分散也不等于更准确。它**不预测中稿率**；历史版本或评分不可靠时会明确说明，不能伪造校准结果。[已做的验证](docs/validation.md) · [后续评测计划](docs/benchmark-plan.md)

[详细用法与 CLI](docs/guide.md) · [历史数据要求](skills/review16/references/anchors.md) · [参与贡献](CONTRIBUTING.md) · [相关项目](docs/landscape.zh-CN.md)

本项目与 MBTI、16Personalities 无隶属关系。[人像与来源](assets/illustration-provenance.md)。项目代码及自有材料采用 MIT；引用的第三方论文与审稿记录保留原有权利。
