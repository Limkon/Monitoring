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
from typing import List, Dict, Optional, Union

# --- 配置日志 ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class MonitorConfig:
    """监控配置类"""
    REQUEST_TIMEOUT = 10
    README_FILENAME = "README.md"
    USER_AGENT = "WebsiteStatusMonitor/1.0 (+https://github.com/your_username/your_repo)"
    MAX_WORKERS = 10

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

    def process_url_file(self) -> List[str]:
        """读取并清洗 URL 文件，去除重复项"""
        if not self.url_filename.exists():
            logger.error(f"❌ 错误: 文件 {self.url_filename} 未找到。")
            return []

        try:
            content = self.url_filename.read_text(encoding='utf-8')
            initial_urls = [line.strip() for line in content.splitlines()]
        except Exception as e:
            logger.error(f"❌ 读取 {self.url_filename} 时发生错误: {e}")
            return []

        valid_format_urls = [url for url in initial_urls if self.looks_like_url(url)]
        normalized_urls = [self.normalize_url(url) for url in valid_format_urls]
        
        # 去重并保持顺序
        unique_urls = []
        seen = set()
        for url in normalized_urls:
            if url not in seen:
                seen.add(url)
                unique_urls.append(url)

        # 检查是否需要更新文件
        current_file_ideal_lines = []
        try:
            current_content = self.url_filename.read_text(encoding='utf-8')
            current_file_ideal_lines = [line.strip() for line in current_content.splitlines() if line.strip()]
        except Exception:
            pass

        if unique_urls != current_file_ideal_lines:
            logger.info(f"🔄 正在更新 {self.url_filename}...")
            try:
                self.url_filename.write_text('\n'.join(unique_urls) + '\n', encoding='utf-8')
                logger.info(f"✅ {self.url_filename} 已成功更新，包含 {len(unique_urls)} 个URL。")
            except IOError as e:
                logger.error(f"❌ 更新 {self.url_filename} 时写入错误: {e}")
                return initial_urls # 写入失败返回原始列表，尽量继续
        else:
            logger.info(f"✅ {self.url_filename} 无需结构性更改，已是最新。")
        
        return unique_urls

    def check_website_status(self, url: str) -> Dict:
        """检查单个网站的状态"""
        headers = {'User-Agent': MonitorConfig.USER_AGENT}
        result = {
            "url": url, 
            "status_code": None, 
            "response_time": "N/A",
            "timestamp": datetime.now(timezone.utc).isoformat(), 
            "error": None, 
            "status": "❓ 未知状态"
        }
        
        try:
            start_time = time.time()
            response = requests.get(url, timeout=MonitorConfig.REQUEST_TIMEOUT, headers=headers, allow_redirects=True)
            end_time = time.time()
            
            response_time_ms = (end_time - start_time) * 1000
            result["status_code"] = response.status_code
            result["response_time"] = f"{response_time_ms:.2f} ms"
            
            if response.url != url:
                result["final_url"] = response.url

            if 200 <= response.status_code < 300:
                result["status"] = "✅ 正常"
            elif 300 <= response.status_code < 400:
                result["status"] = f"↪️ 重定向 ({response.status_code})"
            elif response.status_code == 404:
                result["status"] = "🚫 未找到 (404)"
            else:
                result["status"] = f"⚠️ 异常 (状态: {response.status_code})"
            
            final_url_info = f" | 最终URL: {result['final_url']}" if "final_url" in result else ""
            logger.info(f"{result['status']} - {url} | Code: {result['status_code']} | Time: {result['response_time']}{final_url_info}")

        except requests.Timeout:
            result["status"] = "❌ 太慢 (超时)"
            result["error"] = "请求超时"
        except requests.exceptions.SSLError as e:
            result["status"] = "❌ SSL错误"
            result["error"] = f"SSL问题: {str(e).splitlines()[0]}"
        except requests.exceptions.ConnectionError as e:
            result["status"] = "❌ 连接错误"
            result["error"] = f"连接问题: {str(e).splitlines()[0]}"
        except requests.RequestException as e:
            result["status"] = "❌ 请求错误"
            result["error"] = f"请求问题: {str(e).splitlines()[0]}"
        except Exception as e:
            result["status"] = "❌ 内部处理错误"
            result["error"] = f"意外错误: {str(e).splitlines()[0]}"
            logger.error(f"--- 检查 {url} 时发生意外错误 ---")
            logger.error(traceback.format_exc())

        if result["error"]:
            logger.warning(f"{result['status']} - {url} | 错误: {result.get('error')}")
            
        return result

    def get_status_priority(self, status_str: str) -> int:
        """获取状态优先级用于排序"""
        if not status_str: status_str = "❓"
        if status_str.startswith("❌"): return 0
        if status_str.startswith("🚫"): return 1
        if status_str.startswith("⚠️"): return 2
        if status_str.startswith("↪️"): return 3
        if status_str.startswith("❓"): return 4
        if status_str.startswith("✅"): return 5
        return 6

    def update_readme(self, results: List[Dict]):
        """更新 README.md 文件"""
        if not results:
            logger.warning("⚠️ 没有结果可以更新到README。")
            content = f"# 网站状态监控\n\n最后检查时间: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"
            content += "当前没有监控任何网站，或所有监控结果均为空。\n"
            content += f"\n\n由 {MonitorConfig.USER_AGENT} 监控\n"
            try:
                self.readme_filename.write_text(content, encoding="utf-8")
                logger.info(f"✅ 已使用空状态更新 {self.readme_filename}。")
            except IOError as e:
                logger.error(f"❌ 写入空的 {self.readme_filename} 时发生错误: {e}")
            return

        # 排序结果
        results.sort(key=lambda r: (self.get_status_priority(r.get('status', '❓')), r['url']))

        readme_content = f"# 网站状态监控\n\n最后检查时间: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"
        
        table_header = "| <small>URL</small> | <small>状态</small> | <small>状态码</small> | <small>响应时间</small> | <small>最后检查 (UTC)</small> |\n"
        table_alignment = "|:-----|:-------|:----------|:---------------|:--------------------|\n"
        readme_content += table_header + table_alignment

        rows_md = []
        for result in results:
            status_code_display = f"<small>{result.get('status_code', 'N/A')}</small>"
            response_time_display = f"<small>{result['response_time']}</small>"
            timestamp_display = f"<small>{result['timestamp']}</small>"
            status_display = f"<small>{result.get('status', '❓')}</small>"

            url_display_raw = result['url']
            url_markdown = f"[{url_display_raw}]({url_display_raw})"
            if 'final_url' in result and result['final_url'] != result['url']:
                url_markdown += f"<br><sub>↳ 最终: [{result['final_url']}]({result['final_url']})</sub>"
            
            url_display_final = f"<small>{url_markdown}</small>"

            row = f"| {url_display_final} | {status_display} | {status_code_display} | {response_time_display} | {timestamp_display} |"
            rows_md.append(row)
        
        readme_content += "\n".join(rows_md) + "\n"
        readme_content += f"\n\n由 {MonitorConfig.USER_AGENT} 监控\n"

        try:
            self.readme_filename.write_text(readme_content, encoding="utf-8")
            logger.info(f"✅ 已将最新的网站状态 ({len(results)} 个站点，已排序) 更新到 {self.readme_filename}。")
        except IOError as e:
            logger.error(f"❌ 写入 {self.readme_filename} 时发生错误: {e}")

    def run(self):
        """执行监控流程"""
        logger.info(f"--- 第1步: 处理URL文件: {self.url_filename} ---")
        urls_to_check = self.process_url_file()
        if not urls_to_check:
            logger.warning(f"⚠️ 在 {self.url_filename} 中没有有效的URL可供检查。正在退出。")
            return

        logger.info(f"找到 {len(urls_to_check)} 个唯一且有效的URL进行监控。")
        logger.info(f"\n--- 第2步: 检查网站状态 (最大并发数={MonitorConfig.MAX_WORKERS}) ---")
        
        results_map = {}
        with ThreadPoolExecutor(max_workers=MonitorConfig.MAX_WORKERS) as executor:
            future_to_url = {executor.submit(self.check_website_status, url): url for url in urls_to_check}
            for future in as_completed(future_to_url):
                original_url = future_to_url[future]
                try:
                    result = future.result()
                    results_map[original_url] = result
                except Exception as exc:
                    logger.error(f"❌ URL {original_url} 在线程执行期间产生了一个未能捕获的异常: {exc}")
                    logger.error(traceback.format_exc())
                    error_result = {
                        "url": original_url, "status": "❌ 线程执行错误", 
                        "status_code": None, "response_time": "N/A",
                        "timestamp": datetime.now(timezone.utc).isoformat(), 
                        "error": f"线程内未捕获: {str(exc)}"
                    }
                    results_map[original_url] = error_result

        ordered_results = [results_map[url] for url in urls_to_check if url in results_map]

        logger.info(f"\n--- 第3步: 更新 {self.readme_filename} ---")
        self.update_readme(ordered_results)

        logger.info(f"\n--- 第4步: 更新URL文件 {self.url_filename} (移除404) ---")
        valid_urls_after_check = []
        removed_404_count = 0
        for result_key in urls_to_check:
            result = results_map.get(result_key)
            if result:
                if result.get('status_code') != 404:
                    valid_urls_after_check.append(result['url'])
                else:
                    logger.info(f"🗑️ 标记 {result['url']} 因404将移除。")
                    removed_404_count += 1
            else:
                logger.warning(f"⚠️ URL {result_key} 无检查结果，将保留。")
                valid_urls_after_check.append(result_key)

        if removed_404_count > 0:
            logger.info(f"🔄 更新 {self.url_filename}: 移除 {removed_404_count} 个404 URL。")
            try:
                self.url_filename.write_text('\n'.join(valid_urls_after_check) + '\n', encoding='utf-8')
                logger.info(f"✅ {self.url_filename} 已更新，含 {len(valid_urls_after_check)} URL。")
            except IOError as e:
                logger.error(f"❌ 写入 {self.url_filename} 失败: {e}")
        else:
            logger.info(f"✅ 无404 URL需移除于 {self.url_filename}。")
        
        logger.info("\n监控脚本执行完毕。")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"用法: python {os.path.basename(__file__)} <url_filename>")
        sys.exit(1)
    
    url_source_filename = sys.argv[1]
    monitor = WebsiteMonitor(url_source_filename)
    monitor.run()
