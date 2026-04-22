#!/usr/bin/env python3
"""
Zread.ai 项目文档抓取脚本
https://zread.ai/android/nowinandroid

功能:
- 自动抓取 Now in Android 完整29页文档
- 同时保存为 Markdown 和 JSON 格式
- 自动生成文档索引
- 支持自定义输出目录和请求延迟
"""

import argparse
import json
import re
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests
from bs4 import BeautifulSoup


# Now in Android 完整页面列表 (id -> (slug, title))
NIAD_PAGES: Dict[int, Tuple[str, str]] = {
    1: ("overview", "Overview"),
    2: ("quick-start", "Quick Start"),
    3: ("project-structure", "Project Structure"),
    4: ("gradle-conventions", "Gradle Conventions"),
    5: ("ci-cd", "CI/CD"),
    6: ("architecture-overview", "Architecture Overview"),
    7: ("data-layer-and-offline-first", "Data Layer & Offline First"),
    8: ("domain-layer-and-use-cases", "Domain Layer & Use Cases"),
    9: ("ui-layer-and-jetpack-compose", "UI Layer & Jetpack Compose"),
    10: ("navigation-with-compose", "Navigation with Compose"),
    11: ("modularization-strategy", "Modularization Strategy"),
    12: ("dynamic-feature-modules", "Dynamic Feature Modules"),
    13: ("app-modules-and-dependency-graph", "App Modules & Dependency Graph"),
    14: ("core-modules", "Core Modules"),
    15: ("feature-module-api-impl-pattern", "Feature Module API/Impl Pattern"),
    16: ("foryou-feature-walkthrough", "For You Feature Walkthrough"),
    17: ("interests-feature-walkthrough", "Interests Feature Walkthrough"),
    18: ("workmanager-sync-pipeline", "WorkManager Sync Pipeline"),
    19: ("baseline-profiles", "Baseline Profiles"),
    20: ("screenshot-testing-with-roborazzi", "Screenshot Testing with Roborazzi"),
    21: ("local-testing-strategy", "Local Testing Strategy"),
    22: ("instrumented-testing-strategy", "Instrumented Testing Strategy"),
    23: ("ui-state-production-patterns", "UI State Production Patterns"),
    24: ("ui-state-consumption-patterns", "UI State Consumption Patterns"),
    25: ("data-streaming-patterns", "Data Streaming Patterns"),
    26: ("kotlin-cds-and-error-handling", "Kotlin CDs & Error Handling"),
    27: ("compose-performance", "Compose Performance"),
    28: ("accessibility", "Accessibility"),
    29: ("design-system", "Design System"),
}


class ZreadScraper:
    def __init__(self, base_url: str, project_name: str, output_dir: str = "archive"):
        self.base_url = base_url.rstrip("/")
        self.project_name = project_name
        self.output_dir = Path(output_dir) / project_name
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
        )

        self.pages = NIAD_PAGES

    def fetch_page(self, url: str) -> str:
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

        tables = []
        for table in soup.find_all("table"):
            headers = []
            rows = []
            thead = table.find("thead")
            if thead:
                headers = [th.get_text(strip=True) for th in thead.find_all("th")]
            tbody = table.find("tbody")
            if tbody:
                for row in tbody.find_all("tr"):
                    cells = [td.get_text(strip=True) for td in row.find_all("td")]
                    if cells:
                        rows.append(cells)
            if headers or rows:
                tables.append({"headers": headers, "rows": rows})
        result["tables"] = tables

        code_blocks = []
        for pre in soup.find_all("pre"):
            code = pre.get_text(strip=False)
            if code.strip():
                code_blocks.append(code.strip())
        result["code_blocks"] = code_blocks

        return result

    def save_markdown(self, page_id: int, slug: str, page_title: str, data: dict):
        """保存为Markdown格式"""
        md_dir = self.output_dir / "docs"
        md_dir.mkdir(exist_ok=True)

        filename = f"{page_id:02d}-{slug}.md"
        filepath = md_dir / filename

        md_content = [f"# {page_title}", ""]
        md_content.append(f"> 来源: {self.base_url}/{page_id}-{slug}")
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

    def save_json(self, page_id: int, slug: str, page_title: str, data: dict):
        """保存为JSON格式"""
        json_dir = self.output_dir / "data" / "pages"
        json_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{page_id:02d}-{slug}.json"
        filepath = json_dir / filename

        data["page_id"] = page_id
        data["slug"] = slug
        data["page_title"] = page_title
        data["url"] = f"{self.base_url}/{page_id}-{slug}"
        data["scraped_at"] = time.strftime("%Y-%m-%d %H:%M:%S")

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def scrape_all(self, delay: float = 1.0):
        """抓取所有页面"""
        print(f"开始抓取 {self.project_name} 完整文档 (共 {len(self.pages)} 页)")
        print("=" * 70)

        results = []

        for idx, (page_id, (slug, title)) in enumerate(self.pages.items(), 1):
            print(f"[{idx:2d}/{len(self.pages)}] #{page_id}: {title}")

            url = f"{self.base_url}/{page_id}-{slug}"
            html = self.fetch_page(url)

            if html:
                data = self.parse_content(html)
                self.save_markdown(page_id, slug, title, data)
                self.save_json(page_id, slug, title, data)
                results.append({"page_id": page_id, "slug": slug, "title": title, "status": "success"})
            else:
                results.append({"page_id": page_id, "slug": slug, "title": title, "status": "failed"})

            time.sleep(delay)

        print("=" * 70)
        success = sum(1 for r in results if r["status"] == "success")
        print(f"抓取完成: 成功 {success}/{len(results)} 个页面")

        self.generate_index(results)

        return results

    def generate_index(self, results: list):
        """生成文档索引"""
        index = {
            "project": self.project_name,
            "base_url": self.base_url,
            "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_pages": len(results),
            "success_count": sum(1 for r in results if r["status"] == "success"),
            "pages": results,
        }

        index_file = self.output_dir / "data" / "full-index.json"
        with open(index_file, "w", encoding="utf-8") as f:
            json.dump(index, f, ensure_ascii=False, indent=2)

        md_index = ["# Now in Android - 完整文档索引", ""]
        md_index.append(f"> 抓取时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        md_index.append(f"> 共 {len(results)} 个文档页面")
        md_index.append("")
        md_index.append("## 文档目录")
        md_index.append("")
        md_index.append("| ID | 标题 | 状态 | Markdown | JSON |")
        md_index.append("|----|------|------|----------|------|")

        for page_id, (slug, nav_title) in sorted(self.pages.items()):
            md_file = f"docs/{page_id:02d}-{slug}.md"
            json_file = f"data/pages/{page_id:02d}-{slug}.json"
            status = "✅" if any(r["page_id"] == page_id and r["status"] == "success" for r in results) else "❌"
            md_index.append(f"| {page_id} | {nav_title} | {status} | [查看]({md_file}) | [JSON]({json_file}) |")

        with open(self.output_dir / "FULL_INDEX.md", "w", encoding="utf-8") as f:
            f.write("\n".join(md_index))

        print(f"\n完整索引已保存: {index_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Zread.ai 项目文档抓取脚本 - Now in Android",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python zread_scraper.py                    # 默认配置抓取全部29页
  python zread_scraper.py -d 0.5             # 设置请求间隔为0.5秒
  python zread_scraper.py -o ./my-archive    # 自定义输出目录
        """,
    )

    parser.add_argument(
        "-d",
        "--delay",
        type=float,
        default=1.0,
        help="页面请求间隔(秒), 默认: 1.0",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default="archive",
        help="输出目录, 默认: archive",
    )
    parser.add_argument(
        "-p",
        "--pages",
        type=str,
        help="指定抓取的页面ID, 用逗号分隔, 例如: 1,2,3, 或: 1-5",
    )

    args = parser.parse_args()

    scraper = ZreadScraper(
        base_url="https://zread.ai/android/nowinandroid",
        project_name="nowinandroid",
        output_dir=args.output,
    )

    # 处理自定义页面范围
    if args.pages:
        selected_pages = {}
        for part in args.pages.split(","):
            if "-" in part:
                start, end = map(int, part.split("-"))
                for pid in range(start, end + 1):
                    if pid in NIAD_PAGES:
                        selected_pages[pid] = NIAD_PAGES[pid]
            else:
                pid = int(part.strip())
                if pid in NIAD_PAGES:
                    selected_pages[pid] = NIAD_PAGES[pid]
        scraper.pages = selected_pages
        print(f"自定义抓取范围: {len(selected_pages)} 个页面\n")

    scraper.scrape_all(delay=args.delay)


if __name__ == "__main__":
    main()
