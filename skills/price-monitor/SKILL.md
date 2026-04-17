---
name: price-monitor
description: This skill should be used when the user wants to "监控商品价格", "查询价格", "添加商品", "价格推送", "每日价格提醒", or mentions price monitoring for Taobao/JD.com/Pinduoduo products. Monitors product prices and sends daily notifications via Hermes.
version: 1.0.0
---

# Price Monitor Skill

实时监控淘宝、京东、拼多多商品价格，每日推送价格变动通知。

## 功能概述

- **添加监控商品**: 支持淘宝/京东/拼多多商品链接或关键词搜索
- **价格查询**: 实时爬取各平台商品价格
- **每日推送**: 通过 Hermes 每日定时推送价格报告
- **价格预警**: 当价格低于设定阈值时主动提醒

## 快速使用

### 添加商品监控

用户可以随时通过对话添加商品：

```
监控这个商品 https://item.taobao.com/item.htm?id=xxx
帮我监控京东的这个商品 https://item.jd.com/xxx.html
添加拼多多商品 https://mobile.yangkeduo.com/goods.html?goods_id=xxx
```

### 查询当前价格

```
查一下这个商品的价格
这些监控的商品现在多少钱？
```

### 管理监控列表

```
列出我监控的商品
删除 xxx 商品的监控
清除所有监控
```

## 工作流程

### 1. 解析商品信息

收到商品链接后，调用 `scripts/parse_product.py` 解析平台和商品 ID：

```bash
python scripts/parse_product.py <url>
```

### 2. 爬取价格

调用 `scripts/scrape_price.py` 获取价格：

```bash
python scripts/scrape_price.py <platform> <product_id>
```

平台参数: `taobao`, `jd`, `pinduoduo`

### 3. 存储数据

价格数据存储在 `~/.claude/plugins/price-monitor/data/products.json`

### 4. 发送推送

通过 Hermes 发送每日价格报告：

```
/hermes send <target> <message>
```

## 定时任务配置

设置每日推送（建议早上 9 点）：

```
/schedule daily 9:00 price-monitor/daily-report
```

或使用 cron:

```
0 9 * * * <path-to-scripts>/daily_report.sh
```

## 参考资料

- **`references/platforms.md`** - 各平台反爬机制和应对策略
- **`scripts/scrape_price.py`** - 价格爬取核心脚本
- **`scripts/daily_report.py`** - 每日报告生成脚本

## 平台支持

| 平台 | 状态 | 备注 |
|------|------|------|
| 淘宝 | ✅ | 需要 cookie 或使用接口 |
| 京东 | ✅ | 部分页面需要登录 |
| 拼多多 | ✅ | 建议使用 m.shuffleuid.com 镜像 |
