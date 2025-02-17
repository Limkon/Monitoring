#!/usr/bin/env python3
import asyncio
import aiohttp
from bs4 import BeautifulSoup
import re
import random

# 配置参数
QUERY = "免费节点"      # 搜索关键词
NUM_RESULTS = 50       # 搜索结果数量
OUTPUT_FILE = "nodes.txt"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/115.0.0.0 Safari/537.36"
}

# 正则表达式，用于提取常见节点格式
PATTERNS = {
    "IPv4": re.compile(r'((?:\d{1,3}\.){3}\d{1,3}:\d{2,5})'),
    "ss": re.compile(r'(ss://\S+)'),
    "ssr": re.compile(r'(ssr://\S+)'),
    "vmess": re.compile(r'(vmess://\S+)'),
    "trojan": re.compile(r'(trojan://\S+)'),
    "vless": re.compile(r'(vless://\S+)'),
}

async def google_search(session, query, num_results):
    """
    使用 Google 搜索关键词，返回搜索结果中提取的 URL 列表。
    注意：Google 可能存在反爬虫机制，如有需要可配置代理。
    """
    search_url = "https://www.google.com/search"
    params = {
        "q": query,
        "num": num_results
    }
    try:
        async with session.get(search_url, headers=HEADERS, params=params, timeout=10) as response:
            if response.status != 200:
                print("Google 搜索请求失败，状态码：", response.status)
                return []
            text = await response.text()
    except Exception as e:
        print("请求 Google 搜索异常：", e)
        return []
    
    soup = BeautifulSoup(text, "html.parser")
    links = []
    # Google 搜索结果中的链接通常包含在 <a> 标签中，并以 /url?q= 开头
    for a in soup.find_all("a"):
        href = a.get("href")
        if href and "/url?q=" in href:
            url = href.split("/url?q=")[1].split("&")[0]
            links.append(url)
    # 去重后返回
    return list(dict.fromkeys(links))

async def fetch_page(session, url):
    """
    异步访问一个 URL 并返回页面内容；异常时返回空字符串
    """
    try:
        async with session.get(url, headers=HEADERS, timeout=10) as response:
            if response.status == 200:
                return await response.text()
            else:
                print(f"访问 {url} 失败，状态码：{response.status}")
                return ""
    except Exception as e:
        print(f"访问 {url} 异常：{e}")
        return ""

def extract_nodes(text):
    """
    从文本中提取常见节点信息，返回一个 set 集合
    """
    nodes = set()
    for key, pattern in PATTERNS.items():
        matches = pattern.findall(text)
        for match in matches:
            nodes.add(match.strip())
    return nodes

async def main():
    connector = aiohttp.TCPConnector(limit=10)  # 限制并发连接数
    async with aiohttp.ClientSession(connector=connector) as session:
        print("正在使用 Google 搜索关键词：", QUERY)
        urls = await google_search(session, QUERY, NUM_RESULTS)
        print(f"共获得 {len(urls)} 个链接")

        tasks = []
        for url in urls:
            tasks.append(fetch_page(session, url))
            # 在调度请求时随机延迟，降低请求频率
            await asyncio.sleep(random.uniform(0.5, 1.0))
        
        pages = await asyncio.gather(*tasks)
        all_nodes = set()
        for idx, page in enumerate(pages, 1):
            if page:
                nodes = extract_nodes(page)
                if nodes:
                    print(f"[{idx}] 提取到 {len(nodes)} 个节点")
                    all_nodes.update(nodes)
                else:
                    print(f"[{idx}] 没有提取到节点信息")
        
        if all_nodes:
            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                for node in sorted(all_nodes):
                    f.write(node + "\n")
            print(f"\n爬虫完成，共提取到 {len(all_nodes)} 个节点，结果已保存到 {OUTPUT_FILE}")
        else:
            print("未提取到任何节点信息。")

if __name__ == "__main__":
    asyncio.run(main())
