# 各平台反爬机制和应对策略

## 京东 (推荐优先实现)

### 反爬机制
- 价格接口相对开放
- 有简单的频率限制
- 部分接口需要登录

### 解决方案 ✅ 已实现

**价格API (无需登录)**
```
https://p.3.cn/prices/mgets?skuIds=J_{product_id}&type=1
```

返回格式:
```json
[{
  "id": "J_100009",
  "p": "99.90",      // 现价
  "op": "199.00",    // 原价
  "m": "299.00",     // 最高价
  "l": "89.00"       // 最低价
}]
```

**商品详情API**
```
https://api.m.jd.com/client.action?functionId=productDetail&productId={product_id}
```

## 淘宝/天猫

### 反爬机制
- 强反爬，需要登录状态
- 请求签名验证
- 验证码拦截
- User-Agent 和 Cookie 检测

### 解决方案

**方案1: 移动端API (部分可用)**
```
https://api.m.tmall.com/api/mtop.taobao.detail.getprice/3.2/?itemId={id}
```
需要携带有效Cookie，否则返回受限内容。

**方案2: 淘宝联盟API (推荐)**
1. 申请淘宝联盟账号: https://pub.alimama.com/
2. 获取 AppKey 和 AppSecret
3. 调用淘客API获取商品信息

```python
# 淘宝开放平台 SDK
from top import top
from top.api import TbInterface

appkey = 'your_appkey'
appsecret = 'your_appsecret'
```

**方案3: Cookie保持登录状态**
- 使用浏览器插件提取淘宝Cookie
- 将Cookie配置到 `scripts/config.py`
- 定期更新Cookie

## 拼多多

### 反爬机制
- 最强反爬 🛡️
- 设备指纹检测
- 请求签名算法 (AES + MD5)
- IP频率限制严格
- SSL Pinning (App)

### 解决方案

**方案1: 多多客API (商家/推广者)**
> ⚠️ **注意**: 多多客API仅提供给商家和推广者，普通消费者(C端)无法直接申请。

1. 申请多多客账号: https://www.pinduoduo.com/promo/
2. 使用 SDK: `pip install pdd-sdk-py`
3. 调用接口获取商品信息

**普通用户方案: 浏览器自动化 (推荐)**
```python
from playwright.sync_api import sync_playwright

def scrape_pinduoduo(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)
        # 等待价格加载
        page.wait_for_selector('.price', timeout=10000)
        price = page.locator('.price').first.inner_text()
        title = page.locator('.goods-title').inner_text()
        return {'price': price, 'title': title}
```

安装 Playwright:
```bash
pip install playwright
playwright install chromium
```

**方案2: 移动端代理**
```
https://mobile.yangkeduo.com/api-proxy-server/duo_coupon_local_goods/detail
```
需要签名和设备参数。

**方案3: Playwright 模拟浏览器**
```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(url)
    price = page.locator('.price').inner_text()
```

## 通用反爬应对策略

### 1. 请求伪装
```python
USER_AGENTS = [
    'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)...',
    'Mozilla/5.0 (Linux; Android 10; SM-G960F)...',
]

headers = {
    'User-Agent': random.choice(USER_AGENTS),
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Accept': 'application/json',
    'Referer': 'https://www.google.com/',
}
```

### 2. 请求频率控制
```python
import time
import random

def safe_request(url, delay=2):
    time.sleep(random.uniform(delay, delay * 2))
    return requests.get(url)
```

### 3. 代理IP池
```python
proxies = {
    'http': 'http://user:pass@proxy.com:8080',
    'https': 'https://user:pass@proxy.com:8080',
}
requests.get(url, proxies=proxies)
```

### 4. Cookie管理
```python
session = requests.Session()
session.headers.update(headers)
session.cookies.update(cookies_dict)
```

## 配置示例

在 `scripts/config.py` 中配置:

```python
# 京东 (无需配置)
# 直接可用

# 淘宝
TAOBAO_COOKIE = 'cookie字符串'

# 拼多多
PDD_APP_KEY = 'your_app_key'
PDD_APP_SECRET = 'your_app_secret'
```

## 测试命令

```bash
# 解析链接
python scripts/scrape_price.py parse "https://item.jd.com/100009.html"

# 爬取价格 (京东)
python scripts/scrape_price.py jd 100009
```

## 建议优先级

| 平台 | 难度 | 建议 |
|------|------|------|
| 京东 | ⭐ | 优先实现，API稳定 |
| 淘宝 | ⭐⭐⭐ | 配置Cookie或用联盟API |
| 拼多多 | ⭐⭐⭐⭐ | 使用多多客SDK |
