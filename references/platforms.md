# 各平台价格获取方案

## 京东 ✅ 可用

**官方价格 API (无需登录)**

```
https://p.3.cn/prices/mgets?skuIds=J_{product_id}&type=1
```

返回格式:
```json
[{
  "p": "99.90",      // 现价
  "op": "199.00",    // 原价
  "m": "299.00",     // 最高价
  "l": "89.00"       // 最低价
}]
```

**优点**: 无需任何 Key，直接请求
**缺点**: 偶尔超时（网络问题）

---

## 淘宝/天猫 ⚠️ 需 Playwright

**问题**: 淘宝开放平台已不对个人用户开放 API 申请

**解决方案**: 使用 Playwright 浏览器自动化

```python
from playwright.sync_api import sync_playwright

def scrape_taobao(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until='networkidle')
        # 解析价格和标题
        price = page.locator('.price span').first.inner_text()
        title = page.locator('.tb-title h3').inner_text()
        return {'price': price, 'title': title}
```

---

## 拼多多 ⚠️ 需 Playwright

**问题**: 多多客 API 仅面向商家推广者，普通用户无法申请

**解决方案**: 使用 Playwright 浏览器自动化

```python
def scrape_pinduoduo(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until='networkidle')
        price = page.locator('.goods-price .price').first.inner_text()
        return {'price': price}
```

---

## 安装依赖

```bash
# 安装 Python 依赖
pip install requests playwright

# 安装浏览器
playwright install chromium
```

---

## 使用方法

```bash
# 解析商品链接
python scripts/scrape_price.py parse "https://item.jd.com/100009.html"

# 京东价格
python scripts/scrape_price.py jd 100009

# 淘宝/天猫价格
python scripts/scrape_price.py taobao "https://item.taobao.com/item.htm?id=xxx"

# 拼多多价格
python scripts/scrape_price.py pinduoduo "https://mobile.yangkeduo.com/goods.html?goods_id=xxx"
```

---

## 对比总结

| 平台 | 方案 | 难度 | 稳定性 |
|------|------|------|--------|
| 京东 | 官方 API | ⭐ | 高 |
| 淘宝 | Playwright | ⭐⭐ | 中 |
| 拼多多 | Playwright | ⭐⭐⭐ | 中 |
