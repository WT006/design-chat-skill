# Design Chat

An AI skill for human-led design discussions. Explore the big picture, discuss topics at your own pace, and turn approved decisions into clear, evolving design docs.

由人主导的设计共创 skill：先看全局，按自己的节奏逐块探讨，明确拍板后再把共识沉淀为文档。

## Why Design Chat?

Sometimes you want to think with AI, ask questions, and refine an idea as you go. Design Chat gives the conversation a lightweight structure without turning it into an endless interview.

- **See the big picture.** Start with an understandable architecture and a few suggested discussion topics.
- **Lead the conversation.** Choose, add, revisit, or skip topics. Ask questions and express requirements in your own words.
- **Get useful advice.** The assistant explains trade-offs, investigates relevant facts, and challenges inconsistent assumptions when needed.
- **Decide when to settle.** Approve a direction without having to resolve every implementation detail.
- **Keep a coherent design doc.** Once you explicitly approve a decision, the assistant synthesizes the relevant discussion and updates the document.

This is an instruction-based skill, with no bundled executable scripts or required external integrations. It was developed and structurally validated in Codex. Behavior in other skill-compatible agents may vary. The instructions are written in Chinese; you can request discussion in your preferred language.

## Install

### With the Skills CLI

Requires Node.js and npm. Run this command and select your agent and installation scope:

```bash
npx skills add WT006/design-chat-skill --skill design-chat
```

To install for Codex across your projects:

```bash
npx skills add WT006/design-chat-skill --skill design-chat -a codex -g
```

See the [Skills CLI documentation](https://github.com/vercel-labs/skills/blob/main/docs/commands.md) for other agents and installation options.

### Download manually

Use **Code → Download ZIP** on GitHub, unzip the repository, and place its contents in a folder named `design-chat` inside your agent's supported skills directory. Keep `SKILL.md`, `references/`, and `agents/` together. Do not install only the `SKILL.md` file: it references the document guide.

## Use

In Codex, invoke the skill explicitly:

```text
$design-chat Review the project context, sketch the overall architecture,
and suggest a few topics for us to discuss. I'll choose where to start.
```

中文开场示例：

```text
$design-chat 结合项目资料，先给我一版整体框架和几个值得讨论的模块。
我们逐块探讨，我明确拍板后再把结论整理到设计文档中。
```

Then talk naturally. You do not need to repeat the skill name in every message.

| What you say / 你可以这样说 | What happens / 如何处理 |
| --- | --- |
| “Let's discuss the test environment first.” / “先聊测试环境。” | Follows the topic you choose / 跟随你选择的话题 |
| “Why this approach?” / “你为什么建议这样设计？” | Explains reasoning and trade-offs / 解释原理、理由与取舍 |
| “That makes sense.” / “明白了，有道理。” | Continues the discussion; not automatic approval / 不自动当作定案 |
| “Let's go with this; decide storage later.” / “方向定了，存哪里以后再说。” | Records the approved direction and deferred boundary / 记录已定方向，保留明确暂缓的部分 |
| “I haven't decided yet.” / “还没定，先别写。” | Keeps the proposal in the conversation / 未确认方案留在对话中 |

Explicit approval such as “Let's go with this” can trigger a document update; a separate “save this” command is not required. Approval applies only to the decision being discussed, not to every earlier suggestion. If its scope is unclear, the assistant asks a short clarification.

The assistant uses an existing design document when appropriate, or creates one at a sensible location. Tell it your preferred file if you have one. Approved changes update the relevant text and diagrams; unapproved proposals are not inserted as “pending proposals.” The skill does not automatically start implementation after discussion.

## 中文说明

这个 skill 适合项目架构、复杂功能和方案取舍的讨论。AI 先提供整体视野和议题，你主导表达与提问；AI 负责解答、调查、建议和整理，不要求每轮都追问。

讨论可以跨模块、回退或暂缓细节。你明确认可后，AI 回看相关交流，把零散共识整理为完整设计说明，并同步维护受影响的正文和图表。记录完成后，它会提示剩余议题，方便继续讨论。

它不追求问尽所有分支，也不把“听懂了”当成“同意了”。普通问答、单次文案整理或直接实施任务无需进入这套流程。

## Files

```text
SKILL.md                       Core workflow instructions
agents/openai.yaml             Codex display metadata
references/design-document.md  Guidance for synthesizing approved decisions
LICENSE                        MIT license
```

## Feedback

Issues and pull requests are welcome. When reporting an interaction problem, include a short, sanitized example of what you asked, what the assistant did, and what you expected. Do not include private project information or credentials.

## License

[MIT](LICENSE) © 2026 WT006.
