#!/usr/bin/env python3
"""
Zread.ai 通用项目文档抓取脚本

功能:
- 支持单页抓取
- 支持自动发现并抓取整个项目的所有页面
- 自动保存为 Markdown 和 JSON 格式
- 生成完整项目索引

使用:
  python zread_generic.py https://zread.ai/chrisbanes/tivi/1-overview
  python zread_generic.py https://zread.ai/chrisbanes/tivi --all
  python zread_generic.py <url> -o ./output
"""

import argparse
import json
import re
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests
from bs4 import BeautifulSoup


class ZreadGenericScraper:
    def __init__(self, output_dir: str = "archive"):
        self.output_dir = Path(__file__).parent.parent / output_dir

        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
        )

    def parse_url(self, url: str) -> Tuple[str, str, int, str]:
        """解析 URL，提取项目信息和页面信息"""
        match = re.search(r"zread\.ai/([^/]+)/([^/]+)/(\d+)(?:-([^/?]+))?", url)
        if match:
            author = match.group(1)
            project = match.group(2)
            page_id = int(match.group(3))
            slug = match.group(4) or ""
            project_name = f"{author}-{project}"
            base_url = f"https://zread.ai/{author}/{project}"
            return base_url, project_name, page_id, slug
        else:
            match = re.search(r"zread\.ai/([^/]+)/([^/]+)", url)
            if match:
                project = match.group(1)
                sub = match.group(2)
                base_url = f"https://zread.ai/{project}/{sub}"
                return base_url, f"{project}-{sub}", 1, ""
        return url, "unknown-project", 1, ""

    def discover_pages(self, base_url: str, max_pages: int = 100) -> Dict[int, Tuple[str, str]]:
        """自动发现项目所有页面（通过实际请求验证内容）"""
        pages = {}
        print(f"正在发现页面 (最多 {max_pages} 个)...")

        # 首先获取页面 1 的内容作为基准
        r = self.session.get(f"{base_url}/1", timeout=10)
        if r.status_code != 200:
            print("  项目首页无法访问")
            return pages

        # 连续失败超过 3 次则停止
        consecutive_failures = 0
        max_consecutive_failures = 3

        for page_id in range(1, max_pages + 1):
            url = f"{base_url}/{page_id}"
            try:
                r = self.session.get(url, timeout=10)
                if r.status_code == 200:
                    # 检查页面是否有实际内容（至少有一个 h2 标签）
                    soup = BeautifulSoup(r.text, "html.parser")
                    h2s = soup.find_all("h2")
                    if len(h2s) > 0:
                        # 从 URL slug 或页面中提取标题
                        title = self._extract_page_title(soup, page_id)
                        pages[page_id] = (url, title)
                        print(f"  ✓ 发现页面 {page_id}: {title}")
                        consecutive_failures = 0
                    else:
                        consecutive_failures += 1
                        print(f"  ? 页面 {page_id}: 无内容")
                else:
                    consecutive_failures += 1
                    print(f"  ✗ 页面 {page_id}: status={r.status_code}")
            except Exception as e:
                consecutive_failures += 1
                print(f"  ✗ 页面 {page_id}: {e}")

            if consecutive_failures >= max_consecutive_failures:
                print(f"  连续 {consecutive_failures} 次失败，停止发现")
                break

        print(f"共发现 {len(pages)} 个页面\n")
        return pages

    def _extract_page_title(self, soup: BeautifulSoup, page_id: int) -> str:
        """从页面内容中提取标题"""
        # 尝试从 h1 提取（但通常是 Overview）
        h1 = soup.find("h1")
        if h1:
            text = h1.get_text(strip=True).replace("Report Issue", "").strip()
            if text and text != "Overview":
                return text

        # 尝试从第一个 h2 提取
        h2s = soup.find_all("h2")
        if h2s:
            first_h2 = h2s[0].get_text(strip=True)
            # 一些常见的开头，我们需要找更像标题的
            if first_h2 not in ["Prerequisites", "Key Features at a Glance"]:
                return first_h2

        # 如果都不行，使用通用标题
        return f"Page {page_id}"

    def fetch_page(self, url: str) -> Optional[str]:
        """抓取页面内容"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"  Error: {e}")
            return None

    def parse_content(self, html: str) -> dict:
        """解析HTML内容，提取结构化数据"""
        soup = BeautifulSoup(html, "html.parser")

        # 提取页面标题
        title = self._extract_page_title(soup, 1)

        result = {"title": title, "sections": []}

        sections = soup.find_all("h2")
        for section in sections:
            section_title = section.get_text(strip=True)
            section_title = re.sub(r"\[#\]$", "", section_title).strip()
            section_id = section.get("id", "")

            content = []
            next_elem = section.find_next_sibling()
            while next_elem and next_elem.name != "h2":
                if next_elem.name in ["p", "div", "ul", "ol", "table", "pre", "blockquote"]:
                    text = next_elem.get_text(strip=False)
                    if text.strip():
                        content.append(text.strip())
                next_elem = next_elem.find_next_sibling()

            result["sections"].append(
                {"id": section_id, "title": section_title, "content": "\n\n".join(content)}
            )

        code_blocks = []
        for pre in soup.find_all("pre"):
            code = pre.get_text(strip=False)
            if code.strip():
                code_blocks.append(code.strip())
        result["code_blocks"] = code_blocks

        return result

    def save_markdown(self, project: str, page_id: int, data: dict, url: str) -> Path:
        """保存为Markdown格式"""
        md_dir = self.output_dir / project / "docs"
        md_dir.mkdir(parents=True, exist_ok=True)

        # 从标题生成 slug
        slug = re.sub(r"[^a-z0-9]+", "-", data["title"].lower()).strip("-")
        if not slug:
            slug = f"page-{page_id}"

        filename = f"{page_id:02d}-{slug}.md"
        filepath = md_dir / filename

        md_content = [f"# {data['title']}", ""]
        md_content.append(f"> 来源: {url}")
        md_content.append(f"> 抓取时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        md_content.append("")
        md_content.append("---")
        md_content.append("")

        for section in data["sections"]:
            if section["title"]:
                md_content.append(f"## {section['title']}")
                md_content.append("")
            if section["content"]:
                md_content.append(section["content"])
                md_content.append("")

        if data["code_blocks"]:
            md_content.append("---")
            md_content.append("")
            md_content.append("## 代码示例")
            md_content.append("")
            for i, code in enumerate(data["code_blocks"], 1):
                md_content.append(f"### 示例 {i}")
                md_content.append("```")
                md_content.append(code)
                md_content.append("```")
                md_content.append("")

        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(md_content))

        return filepath

    def save_json(self, project: str, page_id: int, data: dict, url: str) -> Path:
        """保存为JSON格式"""
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

    def generate_index(self, project: str, results: List[dict]):
        """生成项目索引"""
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

        # Markdown 索引
        md_index = [f"# {project} - 完整文档索引", ""]
        md_index.append(f"> 抓取时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        md_index.append(f"> 共 {len(results)} 个文档页面")
        md_index.append("")
        md_index.append("## 文档目录")
        md_index.append("")
        md_index.append("| ID | 标题 | 状态 |")
        md_index.append("|----|------|------|")

        for r in sorted(results, key=lambda x: x["page_id"]):
            status = "✅" if r["status"] == "success" else "❌"
            md_index.append(f"| {r['page_id']} | {r['title']} | {status} |")

        md_index_file = self.output_dir / project / "README.md"
        with open(md_index_file, "w", encoding="utf-8") as f:
            f.write("\n".join(md_index))

        print(f"\n完整索引已保存: {index_file}")
        print(f"Markdown 索引: {md_index_file}")

    def scrape_single(self, url: str) -> bool:
        """抓取单页文档"""
        base_url, project, page_id, slug = self.parse_url(url)

        print(f"抓取: {url}")
        print(f"项目: {project}")
        print("=" * 70)

        html = self.fetch_page(url)
        if not html:
            print("❌ 页面抓取失败")
            return False

        data = self.parse_content(html)
        print(f"标题: {data['title']}")
        print(f"章节数: {len(data['sections'])}")
        print(f"代码块数: {len(data['code_blocks'])}")

        filepath = self.save_markdown(project, page_id, data, url)
        self.save_json(project, page_id, data, url)
        print(f"✅ 已保存: {filepath}")
        print("=" * 70)
        return True

    def scrape_project(self, base_url: str, delay: float = 1.0, max_pages: int = 100) -> bool:
        """抓取整个项目的所有页面"""
        base_url, project, _, _ = self.parse_url(base_url + "/1")

        print(f"抓取项目: {project}")
        print(f"基础 URL: {base_url}")
        print("=" * 70)

        pages = self.discover_pages(base_url, max_pages)
        if not pages:
            print("❌ 未发现任何页面")
            return False

        results = []

        for idx, (page_id, (url, title)) in enumerate(sorted(pages.items()), 1):
            print(f"[{idx:2d}/{len(pages)}] #{page_id}: ", end="", flush=True)

            html = self.fetch_page(url)
            if html:
                data = self.parse_content(html)
                # 使用发现阶段的标题（更准确）
                if title and title != f"Page {page_id}":
                    data["title"] = title
                print(data["title"])

                self.save_markdown(project, page_id, data, url)
                self.save_json(project, page_id, data, url)
                results.append({"page_id": page_id, "url": url, "title": data["title"], "status": "success"})
            else:
                print("❌ 抓取失败")
                results.append({"page_id": page_id, "url": url, "title": title, "status": "failed"})

            time.sleep(delay)

        print("=" * 70)
        success = sum(1 for r in results if r["status"] == "success")
        print(f"抓取完成: 成功 {success}/{len(results)} 个页面")

        self.generate_index(project, results)
        return True


def main():
    parser = argparse.ArgumentParser(
        description="Zread.ai 通用文档抓取脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python zread_generic.py https://zread.ai/chrisbanes/tivi/1-overview
  python zread_generic.py https://zread.ai/chrisbanes/tivi --all
  python zread_generic.py <url> --all -o ./my-archive
        """,
    )

    parser.add_argument("url", help="要抓取的 zread.ai 页面或项目 URL")
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default="archive",
        help="输出目录, 默认: archive",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="抓取整个项目的所有页面",
    )
    parser.add_argument(
        "-d",
        "--delay",
        type=float,
        default=1.0,
        help="页面请求间隔(秒), 默认: 1.0",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=100,
        help="最大页面数, 默认: 100",
    )

    args = parser.parse_args()

    scraper = ZreadGenericScraper(output_dir=args.output)

    if args.all:
        scraper.scrape_project(args.url, delay=args.delay, max_pages=args.max_pages)
    else:
        scraper.scrape_single(args.url)


if __name__ == "__main__":
    main()
