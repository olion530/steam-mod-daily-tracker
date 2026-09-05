# steam-mod-daily-tracker

自动记录“吸锥波波酱”的 7 个《杀戮尖塔 2》Steam 创意工坊 MOD 数据。

每天直接调用 Steam 官方 `GetPublishedFileDetails` 接口，记录：

- 浏览量（views）
- 当前订阅量（subscriptions）
- 当前收藏量（favorited）
- 公开留言数（num_comments_public）

并计算与上一天的绝对增减。

## 跟踪的 7 个 MOD

- `3795933082` — Yoink! — Speed Picks
- `3795496818` — Always Fight Two Bosses at Any Ascension
- `3795496596` — Relic Rewards: Choose One of Three
- `3786269745` — ORBSSSSSSS！！！！
- `3778713629` — Prismatic Gem
- `3772547670` — 德纳修斯大帝 / Sire Denathrius
- `3752747984` — OUCHMOD

## 自动输出

- `data/latest.json`：最新机器可读数据
- `data/latest.md`：最新日报表格
- `data/history/YYYY-MM-DD.json`：每天历史快照

## 定时

GitHub Actions 每天北京时间 20:00 自动查询一次，同时支持手动运行。
