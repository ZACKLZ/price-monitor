#!/usr/bin/env python3
"""
价格爬取核心脚本
支持淘宝、京东、拼多多

反爬策略:
1. 京东: 使用官方价格API (p.3.cn)
2. 淘宝: 使用移动端接口或联盟API
3. 拼多多: 使用多多客SDK或App签名
"""

import json
import sys
import re
import os
import time
import random
from urllib.parse import urlparse
from datetime import datetime

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

# 模拟移动端 User-Agent
USER_AGENTS = [
    'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (Linux; Android 10; SM-G960F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.152 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36',
]


def get_headers():
    """获取随机化的请求头"""
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept': 'application/json, text/plain, */*',
        'Referer': 'https://www.google.com/',
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
        # 京东价格接口 (无需登录)
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
                'raw': price_info
            }
    except Exception as e:
        return {
            'platform': 'jd',
            'product_id': product_id,
            'status': 'error',
            'error': str(e)
        }

    return {'platform': 'jd', 'product_id': product_id, 'status': 'no_data'}


def scrape_jd_detail(product_id: str) -> dict:
    """获取京东商品详情"""
    try:
        # 京东商品信息接口
        url = f'https://api.m.jd.com/client.action?functionId=productDetail&productId={product_id}'

        headers = get_headers()
        headers['Referer'] = 'https://item.jd.com/'

        resp = requests.get(url, headers=headers, timeout=10)
        data = resp.json()

        if data.get('result'):
            result = data['result']
            return {
                'title': result.get('productName', ''),
                'shop': result.get('shopInfo', {}).get('name', ''),
                'image': result.get('imageList', [{}])[0].get('url', '') if result.get('imageList') else '',
            }
    except Exception as e:
        pass

    return {}


def scrape_taobao(product_id: str) -> dict:
    """淘宝/天猫价格爬取"""
    try:
        # 淘宝移动端价格接口
        url = f'https://api.m.tmall.com/api/mtop.taobao.detail.getprice/3.2/'

        headers = get_headers()
        headers['Referer'] = 'https://m.tmall.com/'

        params = {
            'itemId': product_id,
            'detail_v': '3.0',
        }

        resp = requests.get(url, headers=headers, params=params, timeout=10)

        # 尝试备用接口
        if resp.status_code != 200:
            # 淘宝老接口
            url2 = f'https://m.tmall.com/h5/mtop.taobao.detail.getprice/3.2/'
            resp = requests.get(url2, headers=headers, params=params, timeout=10)

        if resp.status_code == 200:
            data = resp.json()
            return {
                'platform': 'taobao',
                'product_id': product_id,
                'price': data.get('data', {}).get('price', {}).get('data', {}).get('price', 0),
                'title': data.get('data', {}).get('itemInfoModel', {}).get('title', ''),
                'status': 'success'
            }

    except Exception as e:
        pass

    # 返回占位数据，需要用户配置cookie
    return {
        'platform': 'taobao',
        'product_id': product_id,
        'price': None,
        'title': None,
        'status': 'need_cookie',
        'message': '淘宝需要登录cookie才能获取价格，请在 scripts/config.py 中配置'
    }


def scrape_pinduoduo(product_id: str) -> dict:
    """拼多多价格爬取 - 使用App签名"""
    try:
        # 拼多多移动端API
        url = 'https://mobile.yangkeduo.com/api-proxy-server/duo_coupon_local_goods/detail'

        headers = get_headers()
        headers['Referer'] = 'https://mobile.yangkeduo.com/'
        headers['Content-Type'] = 'application/json'

        data = {
            'goods_id': product_id,
            'pdduid': random.randint(1000000000000, 9999999999999),
            'version': '1.0.0',
        }

        resp = requests.post(url, headers=headers, json=data, timeout=10)

        if resp.status_code == 200:
            result = resp.json()
            # 拼多多返回格式需要分析
            return {
                'platform': 'pinduoduo',
                'product_id': product_id,
                'price': result.get('goods', {}).get('group_price') or result.get('price'),
                'title': result.get('goods', {}).get('goods_name', ''),
                'status': 'success',
                'raw': result
            }

    except Exception as e:
        pass

    return {
        'platform': 'pinduoduo',
        'product_id': product_id,
        'price': None,
        'title': None,
        'status': 'blocked',
        'message': '拼多多反爬较强，建议配置代理或使用多多客API'
    }


SCRAPERS = {
    'taobao': scrape_taobao,
    'tmall': scrape_taobao,  # 天猫复用淘宝接口
    'jd': scrape_jd_price,
    'pinduoduo': scrape_pinduoduo,
}


def scrape_product(platform: str, product_id: str) -> dict:
    """爬取商品价格"""
    if platform not in SCRAPERS:
        return {'status': 'error', 'message': f'不支持的平台: {platform}'}

    # 添加随机延迟，避免请求过快
    time.sleep(random.uniform(1, 3))

    return SCRAPERS[platform](product_id)


def main():
    if len(sys.argv) < 2:
        print("用法:")
        print("  python scrape_price.py parse <url>  # 解析链接")
        print("  python scrape_price.py <platform> <product_id>  # 获取价格")
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
    product_id = sys.argv[2]

    result = scrape_product(platform, product_id)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
