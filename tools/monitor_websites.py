import os
import sys
import requests
import time
import logging
import traceback
from datetime import datetime, timezone
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# --- 配置日志 ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class MonitorConfig:
    """监控配置类"""
    # 免费容器(如 Render/Koyeb)冷启动需要较长时间，建议设为 30 秒
    REQUEST_TIMEOUT = 30
    README_FILENAME = "README.md"
    # 伪装为真实的 Chrome 浏览器，防止被 Cloudflare / WAF 拦截报 403
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    MAX_WORKERS = 8
    # 是否自动从文件剔除 404 网址？建议设为 False，防止误删正在维护的站点
    AUTO_REMOVE_404 = False

class WebsiteMonitor:
    """网站状态监控核心类"""

    def __init__(self, url_filename: str):
        self.url_filename = Path(url_filename)
        self.readme_filename = Path(MonitorConfig.README_FILENAME)

    def normalize_url(self, url: str) -> str:
        """标准化 URL"""
        url = url.strip()
        try:
            parsed_url = urlparse(url)
            if not parsed_url.scheme:
                return "https://" + url
            return url
        except Exception:
            return url

    def looks_like_url(self, url_str: str) -> bool:
        """简单的 URL 格式验证"""
        if not isinstance(url_str, str) or not url_str.strip():
            return False
        try:
            parsed_url = urlparse(url_str.strip())
            return bool(parsed_url.netloc and '.' in parsed_url.netloc) and \
                   bool(parsed_url.scheme or parsed_url.path or parsed_url.netloc)
        except ValueError:
            return False

    def process_url_file(self) -> list:
        """读取并清洗 URL 文件，去重并排序"""
        if not self.url_filename.exists():
            logger.error(f"❌ 错误: 文件 {self.url_filename} 未找到。")
            return []

        try:
            content = self.url_filename.read_text(encoding='utf-8')
            initial_urls = [line.strip() for line in content.splitlines() if line.strip()]
        except Exception as e:
            logger.error(f"❌ 读取 {self.url_filename} 时发生错误: {e}")
            return []

        valid_format_urls = [url for url in initial_urls if self.looks_like_url(url)]
        normalized_urls = [self.normalize_url(url) for url in valid_format_urls]
        
        # 去重并保持原始顺序
        unique_urls = []
        seen = set()
        for url in normalized_urls:
            if url not in seen:
                seen.add(url)
                unique_urls.append(url)

        return unique_urls

    def _get_session(self) -> requests.Session:
        """创建一个带轻量重试的请求会话"""
        session = requests.Session()
        # 网络抖动时最多重试 1 次
        retries = Retry(total=1, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retries)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        return session

    def check_website_status(self, url: str) -> dict:
        """检查单个网站的状态"""
        headers = {
            'User-Agent': MonitorConfig.USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        result = {
            "url": url, 
            "status_code": None, 
            "response_time": "N/A",
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"), 
            "error": None, 
            "status": "❓ 未知状态"
        }
        
        session = self._get_session()
        try:
            start_time = time.time()
            response = session.get(url, timeout=MonitorConfig.REQUEST_TIMEOUT, headers=headers, allow_redirects=True)
            end_time = time.time()
            
            response_time_ms = (end_time - start_time) * 1000
            result["status_code"] = response.status_code
            result["response_time"] = f"{response_time_ms:.0f} ms"
            
            if response.url.rstrip('/') != url.rstrip('/'):
                result["final_url"] = response.url

            if 200 <= response.status_code < 300:
                result["status"] = "✅ 正常"
            elif 300 <= response.status_code < 400:
                result["status"] = f"↪️ 重定向 ({response.status_code})"
            elif response.status_code == 401 or response.status_code == 403:
                # 很多私有项目报 401/403 实际上服务是存活的
                result["status"] = f"🔒 鉴权/防护 ({response.status_code})"
            elif response.status_code == 404:
                result["status"] = "🚫 未找到 (404)"
            else:
                result["status"] = f"⚠️ 异常 ({response.status_code})"
            
            final_url_info = f" | 最终URL: {result['final_url']}" if "final_url" in result else ""
            logger.info(f"{result['status']} - {url} | Code: {result['status_code']} | Time: {result['response_time']}{final_url_info}")

        except requests.Timeout:
            result["status"] = "❌ 唤醒超时"
            result["error"] = f"超过 {MonitorConfig.REQUEST_TIMEOUT} 秒未响应"
        except requests.exceptions.SSLError as e:
            result["status"] = "❌ SSL证书错误"
            result["error"] = "证书过期或无效"
        except requests.exceptions.ConnectionError:
            result["status"] = "❌ 连接拒绝/失联"
            result["error"] = "无法建立网络连接"
        except Exception as e:
            result["status"] = "❌ 异常"
            result["error"] = str(e).splitlines()[0] if str(e) else "未知错误"

        if result["error"]:
            logger.warning(f"{result['status']} - {url} | 原因: {result.get('error')}")
            
        return result

    def get_status_priority(self, status_str: str) -> int:
        """状态优先级排序：正常的排前面，异常排后面"""
        if not status_str: return 9
        if status_str.startswith("✅"): return 0
        if status_str.startswith("↪️"): return 1
        if status_str.startswith("🔒"): return 2
        if status_str.startswith("⚠️"): return 3
        if status_str.startswith("🚫"): return 4
        if status_str.startswith("❌"): return 5
        return 6

    def update_readme(self, results: list):
        """更新 README.md 表格"""
        if not results:
            logger.warning("⚠️ 没有结果可以更新。")
            return

        # 排序：优先显示正常状态的站点
        results.sort(key=lambda r: (self.get_status_priority(r.get('status', '❓')), r['url']))

        now_utc = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
        readme_content = f"# 🌐 网站存活状态监控\n\n> 最后检查时间：`{now_utc}`\n\n"
        
        table_header = "| 站点链接 | 状态 | 响应码 | 响应耗时 | 检查时间 (UTC) |\n"
        table_alignment = "|:---|:---:|:---:|:---:|:---:|\n"
        readme_content += table_header + table_alignment

        rows_md = []
        for result in results:
            status_code = result.get('status_code') or '-'
            response_time = result['response_time']
            timestamp = result['timestamp']
            status = result.get('status', '❓')

            url_raw = result['url']
            url_markdown = f"[{url_raw}]({url_raw})"
            if 'final_url' in result and result['final_url'] != result['url']:
                url_markdown += f"<br><sub>↳ 转至: [{result['final_url']}]({result['final_url']})</sub>"

            row = f"| {url_markdown} | {status} | `{status_code}` | {response_time} | {timestamp} |"
            rows_md.append(row)
        
        readme_content += "\n".join(rows_md) + "\n\n"
        readme_content += f"---\n*监控引擎基于 GitHub Actions 自动化触发*\n"

        try:
            self.readme_filename.write_text(readme_content, encoding="utf-8")
            logger.info(f"✅ 已将监控状态 ({len(results)} 个站点) 成功更新至 {self.readme_filename}")
        except IOError as e:
            logger.error(f"❌ 写入 {self.readme_filename} 失败: {e}")

    def run(self):
        """执行主调度"""
        logger.info(f"--- 步骤 1: 读取 URL 列表 [{self.url_filename}] ---")
        urls_to_check = self.process_url_file()
        if not urls_to_check:
            logger.warning(f"⚠️ 文件中未发现有效 URL，任务退出。")
            sys.exit(0)

        logger.info(f"准备巡检 {len(urls_to_check)} 个站点，并发线程数: {MonitorConfig.MAX_WORKERS}...")
        
        results_map = {}
        with ThreadPoolExecutor(max_workers=MonitorConfig.MAX_WORKERS) as executor:
            future_to_url = {executor.submit(self.check_website_status, url): url for url in urls_to_check}
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    results_map[url] = future.result()
                except Exception as exc:
                    results_map[url] = {
                        "url": url, "status": "❌ 线程处理崩溃", "status_code": None,
                        "response_time": "N/A", "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                        "error": str(exc)
                    }

        ordered_results = [results_map[url] for url in urls_to_check if url in results_map]

        logger.info(f"\n--- 步骤 2: 刷新并渲染 {self.readme_filename} ---")
        self.update_readme(ordered_results)

        # 步骤 3: 404 处理（默认只告警不自动删除，更加安全）
        if MonitorConfig.AUTO_REMOVE_404:
            valid_urls = [r['url'] for r in ordered_results if r.get('status_code') != 404]
            if len(valid_urls) < len(urls_to_check):
                self.url_filename.write_text('\n'.join(valid_urls) + '\n', encoding='utf-8')
                logger.info(f"🗑️ 已自动从列表中剔除 404 站点，剩余 {len(valid_urls)} 个。")

        logger.info("\n🎉 状态巡检完成！")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"用法: python {os.path.basename(__file__)} <url_filename>")
        sys.exit(1)
    
    monitor = WebsiteMonitor(sys.argv[1])
    monitor.run()
