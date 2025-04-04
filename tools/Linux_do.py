#!/usr/bin/env python3
import asyncio
import random
import re
from playwright.async_api import async_playwright
import aiohttp
from bs4 import BeautifulSoup

# 配置参数
QUERY = "免费节点"
NUM_RESULTS = 50
OUTPUT_FILE = "nodes.txt"

# 代理（如果需要，修改此项）
PROXY_URL = None  # e.g., "http://username:password@proxyserver:port"

# User-Agent 伪装
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"
]

# 正则匹配节点格式
PATTERNS = {
    "IPv4": re.compile(r'((?:\d{1,3}\.){3}\d{1,3}:\d{2,5})'),
    "ss": re.compile(r'(ss://\S+)'),
    "ssr": re.compile(r'(ssr://\S+)'),
    "vmess": re.compile(r'(vmess://\S+)'),
    "trojan": re.compile(r'(trojan://\S+)'),
    "vless": re.compile(r'(vless://\S+)'),
}


async def search_google(query):
    """使用 Playwright 爬取 Google 搜索结果"""
    print(f"[Google] 开始搜索关键词：{query}")
    search_url = f"https://www.google.com/search?q={query}&num={NUM_RESULTS}"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, proxy={"server": PROXY_URL} if PROXY_URL else None)
        page = await browser.new_page()
        
        # 伪装 User-Agent
        user_agent = random.choice(USER_AGENTS)
        await page.set_user_agent(user_agent)

        try:
            await page.goto(search_url, timeout=15000)  # 15 秒超时
            await page.wait_for_load_state("networkidle")

            html = await page.content()
            await browser.close()

            soup = BeautifulSoup(html, "html.parser")
            links = []
            for a in soup.find_all("a"):
                href = a.get("href")
                if href and "/url?q=" in href:
                    url = href.split("/url?q=")[1].split("&")[0]
                    links.append(url)

            unique_links = list(dict.fromkeys(links))
            print(f"[Google] 提取到 {len(unique_links)} 个链接")
            return unique_links

        except Exception as e:
            print(f"[Google] 访问失败：{e}")
            await browser.close()
            return []


async def search_duckduckgo(query):
    """使用 DuckDuckGo 作为备用搜索引擎"""
    print(f"[DuckDuckGo] 开始搜索关键词：{query}")
    search_url = f"https://duckduckgo.com/html/?q={query}"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(search_url, headers={"User-Agent": random.choice(USER_AGENTS)}, timeout=10) as response:
            if response.status != 200:
                print(f"[DuckDuckGo] 访问失败，状态码：{response.status}")
                return []

            text = await response.text()
            soup = BeautifulSoup(text, "html.parser")

            links = []
            for a in soup.find_all("a", class_="result__a"):
                url = a.get("href")
                if url.startswith("/l/?kh=-1&uddg="):
                    url = url.split("uddg=")[1]
                links.append(url)

            unique_links = list(dict.fromkeys(links))
            print(f"[DuckDuckGo] 提取到 {len(unique_links)} 个链接")
            return unique_links


async def fetch_page(session, url):
    """异步访问 URL 并返回页面内容"""
    try:
        async with session.get(url, headers={"User-Agent": random.choice(USER_AGENTS)}, timeout=10) as response:
            if response.status == 200:
                text = await response.text()
                print(f"[{url[:30]}...] 页面获取成功")
                return text
            else:
                print(f"[{url[:30]}...] 请求失败，状态码：{response.status}")
                return ""
    except Exception as e:
        print(f"[{url[:30]}...] 访问异常：{e}")
        return ""


def extract_nodes(text):
    """提取节点信息"""
    nodes = set()
    for pattern in PATTERNS.values():
        matches = pattern.findall(text)
        nodes.update(match.strip() for match in matches)
    return nodes


async def main():
    """主函数"""
    links = await search_google(QUERY)
    if not links:
        print("[Google] 无法获取搜索结果，尝试 DuckDuckGo...")
        links = await search_duckduckgo(QUERY)

    if not links:
        print("[错误] 未能获取任何搜索结果")
        return

    async with aiohttp.ClientSession() as session:
        tasks = [fetch_page(session, url) for url in links]
        pages = await asyncio.gather(*tasks)

    all_nodes = set()
    for page in pages:
        if page:
            nodes = extract_nodes(page)
            all_nodes.update(nodes)

    if all_nodes:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            for node in sorted(all_nodes):
                f.write(node + "\n")
        print(f"\n[完成] 共提取到 {len(all_nodes)} 个节点，结果已保存到 {OUTPUT_FILE}")
    else:
        print("[完成] 没有提取到任何节点信息")


if __name__ == "__main__":
    asyncio.run(main())
