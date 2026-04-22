#!/usr/bin/env python3
"""Zread.ai 项目文档抓取脚本 (Playwright 版本)

使用 Playwright 处理 SPA 动态内容，通过点击导航链接获取各页面完整数据。
"""

from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

if TYPE_CHECKING:
    from playwright.sync_api._generated import Page, Playwright, Browser


class ZreadPlaywrightScraper:
    def __init__(self, output_dir: str = "archive", headless: bool = True):
        self.output_dir = Path(__file__).parent.parent / output_dir
        self.headless = headless
        self.playwright: Playwright | None = None
        self.browser: Browser | None = None
        self.page: Page | None = None
        self.base_url: str | None = None
        self.project_name: str | None = None

    def _init_browser(self) -> None:
        if not self.playwright:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(headless=self.headless)
            self.page = self.browser.new_page(user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    def _close_browser(self) -> None:
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

    def __enter__(self) -> "ZreadPlaywrightScraper":
        self._init_browser()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self._close_browser()

    def parse_url(self, url: str) -> Tuple[str, str, int, str]:
        match = re.search(r"zread\.ai/([^/]+)/([^/]+)/?(\d+)?(?:-([^/?]+))?", url)
        if match:
            author = match.group(1)
            project = match.group(2)
            page_id = int(match.group(3)) if match.group(3) else 1
            slug = match.group(4) or ""
            project_name = f"{author}-{project}"
            base_url = f"https://zread.ai/{author}/{project}"
            return base_url, project_name, page_id, slug
        return url, "unknown-project", 1, ""

    def navigate_to_project(self, base_url: str) -> bool:
        """导航到项目首页，并等待页面加载完成"""
        self.base_url = base_url
        if self.page is None:
            return False
        try:
            self.page.goto(base_url, wait_until="domcontentloaded", timeout=30000)
            self.page.wait_for_timeout(3000)
            return True
        except Exception as e:
            print(f"导航失败: {e}")
            return False

    def discover_pages(self) -> Dict[int, Tuple[str, str, str]]:
        """从侧边栏发现所有页面链接"""
        pages: Dict[int, Tuple[str, str, str]] = {}
        print("正在发现页面...")

        if self.page is None:
            return pages

        # 获取所有导航链接
        links = self.page.query_selector_all('a[href]')
        for link in links:
            href = link.get_attribute('href')
            text_content = link.text_content()
            text = text_content.strip() if text_content else ""
            # 匹配 /author/project/1-slug 格式
            match = re.search(r"/([^/]+)/([^/]+)/(\d+)-([^/?]+)", str(href))
            if match:
                page_id = int(match.group(3))
                slug = match.group(4)
                full_url = f"https://zread.ai{href}"
                if page_id not in pages:
                    pages[page_id] = (full_url, text, slug)
                    print(f"  ✓ 发现页面 {page_id}: {text}")

        print(f"共发现 {len(pages)} 个页面\n")
        return pages

    def navigate_to_page(self, page_id: int, link_text: str) -> Optional[str]:
        """通过点击导航链接导航到指定页面"""
        if self.page is None:
            return None

        try:
            # 尝试通过链接文本点击
            link = self.page.get_by_role('link', name=re.compile(f"^{re.escape(link_text)}$", re.IGNORECASE)).first
            if link and link.is_visible():
                link.click()
                self.page.wait_for_timeout(2000)
                return self.page.content()
        except Exception:
            pass
        
        # 备用方案：直接使用 goto
        try:
            url = f"{self.base_url}/{page_id}"
            self.page.goto(url, wait_until="domcontentloaded", timeout=30000)
            self.page.wait_for_timeout(2000)
            return self.page.content()
        except Exception as e:
            print(f"  导航失败: {e}")
            return None

    def _extract_page_title(self, soup: BeautifulSoup, page_id: int) -> str:
        h1 = soup.find("h1")
        if h1:
            text = h1.get_text(strip=True).replace("Report Issue", "").strip()
            if text:
                return text
        h2s = soup.find_all("h2")
        if h2s:
            return h2s[0].get_text(strip=True)
        return f"Page {page_id}"

    def parse_content(self, html: str) -> dict:
        soup = BeautifulSoup(html, "html.parser")
        title = self._extract_page_title(soup, 1)
        sections_list: List[dict] = []
        result = {"title": title, "sections": sections_list}
        sections = soup.find_all("h2")
        for section in sections:
            section_title = section.get_text(strip=True)
            section_title = re.sub(r"\[#\]$", "", section_title).strip()
            section_id = section.get("id", "")
            content_list: List[str] = []
            next_elem = section.find_next_sibling()
            while next_elem and next_elem.name != "h2":
                if next_elem.name in ["p", "div", "ul", "ol", "table", "pre", "blockquote"]:
                    text = next_elem.get_text(strip=False)
                    if text.strip():
                        content_list.append(text.strip())
                next_elem = next_elem.find_next_sibling()
            sections_list.append({"id": section_id, "title": section_title, "content": "\n\n".join(content_list)})
        code_blocks: List[str] = []
        for pre in soup.find_all("pre"):
            code = pre.get_text(strip=False)
            if code.strip():
                code_blocks.append(code.strip())
        result["code_blocks"] = code_blocks
        return result

    def save_markdown(self, project: str, page_id: int, data: dict, url: str) -> Path:
        md_dir = self.output_dir / project / "docs"
        md_dir.mkdir(parents=True, exist_ok=True)
        slug = re.sub(r"[^a-z0-9]+", "-", data["title"].lower()).strip("-")
        if not slug:
            slug = f"page-{page_id}"
        filename = f"{page_id:02d}-{slug}.md"
        filepath = md_dir / filename
        md_content: List[str] = [f"# {data['title']}", "", f"> 来源: {url}", f"> 抓取时间: {time.strftime('%Y-%m-%d %H:%M:%S')}", "", "---", ""]
        for section in data["sections"]:
            if section["title"]:
                md_content.append(f"## {section['title']}")
                md_content.append("")
            if section["content"]:
                md_content.append(section["content"])
                md_content.append("")
        if data["code_blocks"]:
            md_content.extend(["---", "", "## 代码示例", ""])
            for i, code in enumerate(data["code_blocks"], 1):
                md_content.extend([f"### 示例 {i}", "```", code, "```", ""])
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(md_content))
        return filepath

    def save_json(self, project: str, page_id: int, data: dict, url: str) -> Path:
        json_dir = self.output_dir / project / "data" / "pages"
        json_dir.mkdir(parents=True, exist_ok=True)
        slug = re.sub(r"[^a-z0-9]+", "-", data["title"].lower()).strip("-")
        if not slug:
            slug = f"page-{page_id}"
        filename = f"{page_id:02d}-{slug}.json"
        filepath = json_dir / filename
        data["page_id"] = page_id
        data["url"] = url
        data["scraped_at"] = time.strftime('%Y-%m-%d %H:%M:%S')
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return filepath

    def generate_index(self, project: str, results: List[dict]) -> None:
        index = {
            "project": project,
            "scraped_at": time.strftime('%Y-%m-%d %H:%M:%S'),
            "total_pages": len(results),
            "success_count": sum(1 for r in results if r["status"] == "success"),
            "pages": results,
        }
        index_file = self.output_dir / project / "data" / "index.json"
        index_file.parent.mkdir(parents=True, exist_ok=True)
        with open(index_file, "w", encoding="utf-8") as f:
            json.dump(index, f, ensure_ascii=False, indent=2)

        md_index: List[str] = [f"# {project} - 完整文档索引", "", f"> 抓取时间: {time.strftime('%Y-%m-%d %H:%M:%S')}", f"> 共 {len(results)} 个文档页面", "", "## 文档目录", "", "| ID | 标题 | 状态 |", "|----|------|------|"]
        for r in sorted(results, key=lambda x: x["page_id"]):
            status = "✅" if r["status"] == "success" else "❌"
            md_index.append(f"| {r['page_id']} | {r['title']} | {status} |")

        md_index_file = self.output_dir / project / "README.md"
        with open(md_index_file, "w", encoding="utf-8") as f:
            f.write("\n".join(md_index))

        print(f"\n完整索引已保存: {index_file}")
        print(f"Markdown 索引: {md_index_file}")

    def scrape_project(self, base_url: str, delay: float = 1.0) -> bool:
        """抓取整个项目的所有页面"""
        base_url, project_name, _, _ = self.parse_url(base_url)
        self.project_name = project_name

        print(f"抓取项目: {project_name}")
        print(f"基础 URL: {base_url}")
        print("=" * 70)

        if not self.navigate_to_project(base_url):
            print("❌ 无法访问项目")
            return False

        pages = self.discover_pages()
        if not pages:
            print("❌ 未发现任何页面")
            return False

        results: List[dict] = []

        for idx, (page_id, page_info) in enumerate(sorted(pages.items()), 1):
            url, title, slug = page_info
            print(f"[{idx:2d}/{len(pages)}] #{page_id}: {title} ", end="", flush=True)

            html = self.navigate_to_page(page_id, title)
            if html:
                data = self.parse_content(html)
                if data["title"]:
                    title = data["title"]
                
                self.save_markdown(project_name, page_id, data, url)
                self.save_json(project_name, page_id, data, url)
                results.append({"page_id": page_id, "url": url, "title": title, "status": "success"})
                print(f"✓ ({len(data['sections'])} 章节)")
            else:
                print("✗ 抓取失败")
                results.append({"page_id": page_id, "url": url, "title": title, "status": "failed"})

            time.sleep(delay)

        print("=" * 70)
        success = sum(1 for r in results if r["status"] == "success")
        print(f"抓取完成: 成功 {success}/{len(results)} 个页面")

        self.generate_index(project_name, results)
        return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Zread.ai 文档抓取脚本 (Playwright 版本)")
    parser.add_argument("url", help="要抓取的 zread.ai 项目 URL")
    parser.add_argument("-o", "--output", type=str, default="archive", help="输出目录")
    parser.add_argument("-d", "--delay", type=float, default=1.0, help="页面请求间隔(秒)")
    args = parser.parse_args()

    with ZreadPlaywrightScraper(output_dir=args.output, headless=True) as scraper:
        scraper.scrape_project(args.url, delay=args.delay)


if __name__ == "__main__":
    main()
