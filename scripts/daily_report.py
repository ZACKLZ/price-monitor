#!/usr/bin/env python3
"""
每日价格报告生成脚本
配合 cron 或 scheduler 使用
"""

import json
import os
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
PRODUCTS_FILE = os.path.join(DATA_DIR, 'products.json')


def load_products():
    """加载商品数据"""
    if not os.path.exists(PRODUCTS_FILE):
        return []

    with open(PRODUCTS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def generate_report():
    """生成每日价格报告"""
    products = load_products()

    if not products:
        return "📦 当前没有监控任何商品"

    report_lines = ["📊 每日价格报告", f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"]

    for p in products:
        platform_emoji = {'taobao': '🛒', 'jd': '📱', 'pinduoduo': '🛍️'}.get(p['platform'], '📦')
        price_info = f"¥{p['price']}" if p.get('price') else "暂无价格"
        report_lines.append(f"{platform_emoji} {p.get('title', '未知商品')}")
        report_lines.append(f"   当前价格: {price_info}")

        if p.get('lowest_price'):
            report_lines.append(f"   历史最低: ¥{p['lowest_price']}")

        if p.get('price_change'):
            change = p['price_change']
            emoji = '📉' if change < 0 else '📈' if change > 0 else '➡️'
            report_lines.append(f"   {emoji} 变化: {change:+.2f}")

        report_lines.append("")

    return "\n".join(report_lines)


def main():
    report = generate_report()
    print(report)


if __name__ == '__main__':
    main()
