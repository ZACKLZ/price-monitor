#!/usr/bin/env python3
"""
价格爬取核心脚本
支持淘宝、京东、拼多多

方案:
1. 京东: 使用官方API (p.3.cn)
2. 淘宝/天猫: Playwright 浏览器自动化
3. 拼多多: Playwright 浏览器自动化
"""

import json
import sys
import re
import os
import time
import random
from urllib.parse import urlparse

try:
    import requests
except ImportError:
    print("请先安装 requests: pip install requests")
    sys.exit(1)

PLATFORMS = {
    'taobao': {
        'name': '淘宝',
        'patterns': [
            r'item\.taobao\.com.*id=(\d+)',
            r'taobao\.com.*id=(\d+)',
        ]
    },
    'tmall': {
        'name': '天猫',
        'patterns': [
            r'detail\.tmall\.com.*id=(\d+)',
            r'tmall\.com.*id=(\d+)',
        ]
    },
    'jd': {
        'name': '京东',
        'patterns': [
            r'item\.jd\.com.*/(\d+)\.html',
            r'jd\.com.*/(\d+)\.html',
        ]
    },
    'pinduoduo': {
        'name': '拼多多',
        'patterns': [
            r'mobile\.yangkeduo\.com.*goods_id=(\d+)',
            r'yangkeduo\.com.*goods_id=(\d+)',
            r'pinduoduo\.com.*goods_id=(\d+)',
        ]
    }
}

USER_AGENTS = [
    'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (Linux; Android 10; SM-G960F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.152 Mobile Safari/537.36',
]


def get_headers():
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept': 'application/json, text/plain, */*',
    }


def detect_platform(url: str) -> tuple[str, str]:
    """检测平台和商品ID"""
    for platform, info in PLATFORMS.items():
        for pattern in info['patterns']:
            match = re.search(pattern, url)
            if match:
                return platform, match.group(1)
    raise ValueError(f"无法识别的商品链接: {url}")


def scrape_jd_price(product_id: str) -> dict:
    """京东价格爬取 - 使用官方API"""
    try:
        url = f'https://p.3.cn/prices/mgets?skuIds=J_{product_id}&type=1'
        resp = requests.get(url, headers=get_headers(), timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data and len(data) > 0:
            price_info = data[0]
            return {
                'platform': 'jd',
                'product_id': product_id,
                'price': float(price_info.get('p', 0)),
                'original_price': float(price_info.get('op', 0)) if price_info.get('op') else None,
                'lowest_price': float(price_info.get('l', 0)) if price_info.get('l') else None,
                'highest_price': float(price_info.get('m', 0)) if price_info.get('m') else None,
                'status': 'success',
            }
    except Exception as e:
        return {'platform': 'jd', 'product_id': product_id, 'status': 'error', 'error': str(e)}
    return {'platform': 'jd', 'product_id': product_id, 'status': 'no_data'}


def scrape_with_playwright(url: str, platform: str) -> dict:
    """
    使用 Playwright 浏览器自动化爬取
    支持淘宝、天猫、拼多多
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return {
            'platform': platform,
            'status': 'error',
            'error': '请先安装 playwright: pip install playwright && playwright install chromium'
        }

    result = {
        'platform': platform,
        'status': 'error',
        'url': url,
        'error': '未找到价格元素'
    }

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
                locale='zh-CN'
            )
            page = context.new_page()

            # 设置超时
            page.set_default_timeout(30000)

            # 访问页面
            page.goto(url, wait_until='networkidle')

            # 随机延迟
            time.sleep(random.uniform(2, 4))

            if platform in ('taobao', 'tmall'):
                # 淘宝/天猫价格选择器
                try:
                    # 尝试多个可能的选择器
                    selectors = [
                        '.price span',           # 常见价格 class
                        '.tm-price',             # 天猫价格
                        '.originPrice',          # 原价
                        '[class*="price"]',      # 包含 price 的 class
                        '.goods-price',          # 商品价格
                    ]
                    price = None
                    for sel in selectors:
                        try:
                            elements = page.locator(sel).all()
                            for el in elements:
                                text = el.inner_text()
                                # 匹配价格格式
                                price_match = re.search(r'[\d.]+', text)
                                if price_match and float(price_match.group()) > 0:
                                    price = float(price_match.group())
                                    break
                        except:
                            continue
                        if price:
                            break

                    # 获取标题
                    title_selectors = ['.tb-title h3', '.goods-title', '[class*="title"]', 'h3']
                    title = ''
                    for sel in title_selectors:
                        try:
                            title = page.locator(sel).first.inner_text()
                            break
                        except:
                            continue

                    if price:
                        result = {
                            'platform': platform,
                            'product_id': '',
                            'price': price,
                            'title': title.strip() if title else '',
                            'status': 'success',
                        }
                except Exception as e:
                    result['error'] = str(e)

            elif platform == 'pinduoduo':
                try:
                    # 拼多多价格选择器
                    selectors = [
                        '.goods-price .price',
                        '.price-content',
                        '[class*="price"] .value',
                    ]
                    price = None
                    for sel in selectors:
                        try:
                            el = page.locator(sel).first
                            text = el.inner_text()
                            price_match = re.search(r'[\d.]+', text)
                            if price_match:
                                price = float(price_match.group())
                                break
                        except:
                            continue

                    # 获取标题
                    title = ''
                    for sel in ['.goods-name', '.goods-title', '[class*="name"]']:
                        try:
                            title = page.locator(sel).first.inner_text()
                            break
                        except:
                            continue

                    if price:
                        result = {
                            'platform': platform,
                            'product_id': '',
                            'price': price,
                            'title': title.strip() if title else '',
                            'status': 'success',
                        }
                except Exception as e:
                    result['error'] = str(e)

            browser.close()

    except Exception as e:
        result['error'] = str(e)

    return result


def scrape_product(platform: str, product_id: str = None, url: str = None) -> dict:
    """爬取商品价格"""
    # 京东直接用API
    if platform == 'jd':
        time.sleep(random.uniform(1, 2))
        return scrape_jd_price(product_id)

    # 淘宝/天猫/拼多多用 Playwright
    if platform in ('taobao', 'tmall', 'pinduoduo'):
        if url:
            return scrape_with_playwright(url, platform)

    return {'status': 'error', 'message': f'不支持的平台: {platform}'}


def main():
    if len(sys.argv) < 2:
        print("用法:")
        print("  python scrape_price.py parse <url>     # 解析链接")
        print("  python scrape_price.py jd <product_id>  # 京东价格")
        print("  python scrape_price.py taobao <url>     # 淘宝/天猫价格")
        print("  python scrape_price.py pinduoduo <url>  # 拼多多价格")
        sys.exit(1)

    if sys.argv[1] == 'parse':
        url = sys.argv[2]
        try:
            platform, product_id = detect_platform(url)
            result = {
                'platform': platform,
                'product_id': product_id,
                'platform_name': PLATFORMS[platform]['name']
            }
            print(json.dumps(result, ensure_ascii=False, indent=2))
        except ValueError as e:
            print(f"错误: {e}")
            sys.exit(1)
        return

    platform = sys.argv[1]

    if platform == 'jd':
        if len(sys.argv) < 3:
            print("用法: python scrape_price.py jd <product_id>")
            sys.exit(1)
        result = scrape_product('jd', product_id=sys.argv[2])
    else:
        # 淘宝/拼多多直接传URL
        if len(sys.argv) < 3:
            print(f"用法: python scrape_price.py {platform} <url>")
            sys.exit(1)
        result = scrape_product(platform, url=sys.argv[2])

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
