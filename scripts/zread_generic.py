#!/usr/bin/env python3
"""
Zread.ai 通用项目文档抓取脚本

功能:
- 支持任意 zread.ai 项目文档的单页抓取
- 自动保存为 Markdown 格式
- 支持自定义输出目录

使用:
  python zread_generic.py https://zread.ai/chrisbanes/tivi/1-overview
  python zread_generic.py <url> -o ./output
"""

import argparse
import re
import time
from pathlib import Path
from typing import Optional

import requests
from bs4 import BeautifulSoup


class ZreadGenericScraper:
    def __init__(self, output_dir: str = "archive"):
        self.output_dir = Path(__file__).parent.parent / output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
        )

    def parse_url(self, url: str) -> tuple[str, str, str]:
        """解析 URL，提取项目名、页面ID和slug"""
        match = re.search(r"zread\.ai/([^/]+)/([^/]+)/(\d+)-([^/]+)", url)
        if match:
            author = match.group(1)
            project = match.group(2)
            page_id = match.group(3)
            slug = match.group(4)
            return f"{author}-{project}", page_id, slug
        else:
            match = re.search(r"zread\.ai/([^/]+)/([^/]+)", url)
            if match:
                project = match.group(1)
                slug = match.group(2)
                return project, "1", slug
        return "generic", "1", "page"

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

        title_elem = soup.find("h1")
        title = title_elem.get_text(strip=True) if title_elem else "Unknown"
        title = re.sub(r"Report Issue$", "", title).strip()

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

    def save_markdown(self, project: str, page_id: str, slug: str, data: dict, url: str):
        """保存为Markdown格式"""
        md_dir = self.output_dir / project / "docs"
        md_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{page_id}-{slug}.md"
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

    def scrape(self, url: str) -> bool:
        """抓取单页文档"""
        print(f"抓取: {url}")
        print("=" * 70)

        project, page_id, slug = self.parse_url(url)
        print(f"项目: {project}")
        print(f"页面: {page_id}-{slug}")

        html = self.fetch_page(url)
        if not html:
            print("❌ 页面抓取失败")
            return False

        data = self.parse_content(html)
        print(f"标题: {data['title']}")
        print(f"章节数: {len(data['sections'])}")
        print(f"代码块数: {len(data['code_blocks'])}")

        filepath = self.save_markdown(project, page_id, slug, data, url)
        print(f"✅ 已保存: {filepath}")
        print("=" * 70)
        return True


def main():
    parser = argparse.ArgumentParser(
        description="Zread.ai 通用文档抓取脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python zread_generic.py https://zread.ai/chrisbanes/tivi/1-overview
  python zread_generic.py <url> -o ./my-archive
        """,
    )

    parser.add_argument("url", help="要抓取的 zread.ai 页面 URL")
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default="archive",
        help="输出目录, 默认: archive",
    )

    args = parser.parse_args()

    scraper = ZreadGenericScraper(output_dir=args.output)
    scraper.scrape(args.url)


if __name__ == "__main__":
    main()
