# Price Monitor Plugin

监控淘宝、京东、拼多多商品价格，通过 OpenClaw/Hermes 每日推送通知。

适用于 OpenClaw/Hermes 机器人框架。

## 安装

复制到 Claude Code plugins 目录：

```bash
# 克隆仓库
git clone <repo-url> price-monitor

# 移动到 plugins 目录
mv price-monitor ~/.claude/plugins/price-monitor
```

## 配置

1. 安装依赖：
```bash
pip install requests beautifulsoup4
```

2. 配置 OpenClaw/Hermes 推送（可选）：
```
/hermes set daily-price-notification true
```

## 使用方法

### 添加商品监控
```
监控这个商品 https://item.taobao.com/item.htm?id=xxx
帮我监控京东的这个商品 https://item.jd.com/xxx.html
添加拼多多商品 https://mobile.yangkeduo.com/goods.html?goods_id=xxx
```

### 查询价格
```
查一下这个商品的价格
现在监控的商品多少钱？
```

### 管理商品
```
列出我监控的商品
删除 xxx 商品的监控
```

### 定时推送
设置每日推送：
```
/schedule daily 9:00 price-monitor/daily-report
/schedule daily 9:00 price-monitor/daily-report --chat <target>
```

## 定时任务

手动配置 cron：
```bash
0 9 * * * python3 /path/to/plugins/price-monitor/scripts/daily_report.py >> /tmp/price_report.log
```

## 项目结构

```
price-monitor/
├── .claude-plugin/
│   └── plugin.json
├── skills/
│   └── price-monitor/
│       └── SKILL.md
├── scripts/
│   ├── scrape_price.py    # 价格爬取
│   └── daily_report.py     # 每日报告
├── references/
│   └── platforms.md       # 平台API文档
└── data/
    └── products.json      # 商品数据
```

## 免责声明

本工具仅供学习研究使用，请勿用于商业爬虫。爬取第三方网站需遵守其 robots.txt 和使用条款。
