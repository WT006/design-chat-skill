# Talk to Plan

**English** | [中文](README.zh-CN.md)

An AI skill for human-led design discussions. Explore ideas together and turn approved decisions into clear design docs.

## Why Talk to Plan?

- **Tired of endless follow-up questions?** You want to explore an idea, but the conversation turns into a questionnaire about every detail.
- **Still explaining, but AI has already decided?** A tentative thought becomes a requirement before you've agreed to it.
- **Had a useful discussion, then had to piece it all together?** Your decisions are scattered across messages, with no clear design doc to continue from.

Talk to Plan gives you a shared starting point, room to think out loud, and a document that grows as you make decisions.

## How it works

1. **See the big picture.** AI sketches the architecture and suggests discussion topics.
2. **Talk at your own pace.** You choose the topics; AI explains, investigates, and advises.
3. **Decide, then document.** AI records decisions only after you explicitly approve them.

Skip topics, revisit ideas, or leave details for later. “That makes sense” is not treated as approval.

## Install

Requires Node.js and npm. Choose your agent when prompted:

```bash
npx skills add WT006/talk-to-plan-skill --skill talk-to-plan
```

## Use

In Codex:

```text
$talk-to-plan Sketch the overall architecture and suggest a few topics.
Let's discuss them together and document decisions once I approve them.
```

Continue naturally—no need to repeat the skill name. Developed in Codex; the skill instructions are in Chinese, and you can request another conversation language.

## Example conversation

> **You:** $talk-to-plan I want to build a bookmarking tool. Give me the big picture first.
>
> **AI:** We can discuss saving content, organizing and finding it, and syncing across devices. Here's how those parts connect…
>
> **You:** Let's talk about sync. Do we need it in the first version? I'd like to keep things simple.
>
> **AI:** I'd start with local storage if you're using one device. It keeps the first version smaller, but bookmarks won't be available on your other devices.
>
> **You:** Let's go with local storage first. We'll design sync later. Record that.
>
> **AI:** Recorded the decision, its trade-off, and the deferred sync topic in the design doc. Next, we could discuss saving content or organizing it.

## License

[MIT](LICENSE)
