# Design Chat

**English** | [中文](README.zh-CN.md)

An AI skill for human-led design discussions. Explore ideas together and turn approved decisions into clear design docs.

## How it works

1. **See the big picture.** AI sketches the architecture and suggests discussion topics.
2. **Talk at your own pace.** You choose the topics; AI explains, investigates, and advises.
3. **Decide, then document.** AI records decisions only after you explicitly approve them.

Skip topics, revisit ideas, or leave details for later. “That makes sense” is not treated as approval.

## Install

Requires Node.js and npm. Choose your agent when prompted:

```bash
npx skills add WT006/design-chat-skill --skill design-chat
```

## Use

In Codex:

```text
$design-chat Sketch the overall architecture and suggest a few topics.
Let's discuss them together and document decisions once I approve them.
```

Continue naturally—no need to repeat the skill name. Developed in Codex; the skill instructions are in Chinese, and you can request another conversation language.

## License

[MIT](LICENSE)
