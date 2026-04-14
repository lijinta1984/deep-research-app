import asyncio
import json
import uuid
from datetime import datetime

import httpx
from loguru import logger
from openai import AsyncOpenAI

from backend.api.dependencies import settings
from backend.research.prompts import PASS_1_SYSTEM, PASS_2_SYSTEM, PASS_3_SYSTEM
from backend.research.schemas import (
    Pass1Output,
    Pass2Output,
    Pass3Output,
    ScrapedSource,
    SearchTreeNode,
)


class ResearchEngine:
    """Core 3-pass research engine using Firecrawl + Kimi K2."""

    def __init__(self) -> None:
        self.llm = AsyncOpenAI(
            api_key=settings.moonshot_api_key,
            base_url="https://api.moonshot.cn/v1",
        )
        self.firecrawl_api_key = settings.firecrawl_api_key
        self.firecrawl_base = "https://api.firecrawl.dev/v1"
        self.model = "moonshot-v1-128k"
        self.sources: list[ScrapedSource] = []
        self.tree_nodes: list[SearchTreeNode] = []

    async def _call_kimi(self, system_prompt: str, user_content: str) -> str:
        """Call Kimi K2 with exponential backoff retry."""
        for attempt in range(3):
            try:
                response = await self.llm.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content},
                    ],
                    max_tokens=4096,
                    temperature=0.2,
                )
                content = response.choices[0].message.content or ""
                return content.strip()
            except Exception as exc:
                wait_time = 2**attempt
                logger.warning(
                    "Kimi K2 call failed (attempt {}/3): {} — retrying in {}s",
                    attempt + 1,
                    exc,
                    wait_time,
                )
                if attempt == 2:
                    raise
                await asyncio.sleep(wait_time)
        return ""

    async def _call_kimi_with_validation(
        self,
        system_prompt: str,
        user_content: str,
        model_class: type,
    ) -> dict:
        """Call Kimi K2 and validate JSON response. Retry once on failure."""
        raw = await self._call_kimi(system_prompt, user_content)
        parsed = self._try_parse_json(raw)
        if parsed is not None:
            try:
                model_class.model_validate(parsed)
                return parsed
            except Exception:
                pass

        retry_msg = (
            user_content
            + "\n\nYour previous response failed JSON validation. "
            "Return only valid JSON matching the schema. "
            "No preamble, no markdown fences."
        )
        raw = await self._call_kimi(system_prompt, retry_msg)
        parsed = self._try_parse_json(raw)
        if parsed is not None:
            model_class.model_validate(parsed)
            return parsed
        raise ValueError("Kimi K2 returned invalid JSON after retry")

    @staticmethod
    def _try_parse_json(text: str) -> dict | None:
        """Try to parse JSON from text, stripping markdown fences if present."""
        text = text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            lines = lines[1:]  # remove opening fence
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines).strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return None

    async def _firecrawl_search(self, query: str, limit: int = 3) -> list[dict]:
        """Search Firecrawl for URLs matching a query."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f"{self.firecrawl_base}/search",
                    headers={"Authorization": f"Bearer {self.firecrawl_api_key}"},
                    json={"query": query, "limit": limit},
                )
                resp.raise_for_status()
                data = resp.json()
                return data.get("data", [])
        except Exception as exc:
            logger.error("Firecrawl search failed for '{}': {}", query, exc)
            return []

    async def _firecrawl_scrape(self, url: str) -> dict | None:
        """Scrape a URL via Firecrawl and return markdown content."""
        for attempt in range(2):
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    resp = await client.post(
                        f"{self.firecrawl_base}/scrape",
                        headers={
                            "Authorization": f"Bearer {self.firecrawl_api_key}",
                        },
                        json={"url": url, "formats": ["markdown"]},
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    return data.get("data", {})
            except Exception as exc:
                if attempt == 0:
                    logger.warning("Scrape retry for {}: {}", url, exc)
                    await asyncio.sleep(1)
                else:
                    logger.error("Scrape failed permanently for {}: {}", url, exc)
                    return None
        return None

    def _truncate_content(self, content: str, max_words: int = 8000) -> str:
        """Strip content over max_words words."""
        words = content.split()
        if len(words) > max_words:
            return " ".join(words[:max_words])
        return content

    async def _scrape_urls(
        self,
        urls: list[str],
        pass_number: int,
    ) -> list[ScrapedSource]:
        """Scrape multiple URLs concurrently and return ScrapedSource objects."""
        tasks = [self._firecrawl_scrape(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        scraped: list[ScrapedSource] = []
        for url, result in zip(urls, results):
            if isinstance(result, Exception) or result is None:
                scraped.append(
                    ScrapedSource(
                        url=url,
                        title="",
                        markdown_content="",
                        scraped_at=datetime.utcnow(),
                        pass_number=pass_number,
                        word_count=0,
                        scrape_success=False,
                    )
                )
                continue
            md = result.get("markdown", "")
            title = result.get("metadata", {}).get("title", url)
            md = self._truncate_content(md)
            source = ScrapedSource(
                url=url,
                title=title,
                markdown_content=md,
                scraped_at=datetime.utcnow(),
                pass_number=pass_number,
                word_count=len(md.split()),
                scrape_success=True,
            )
            scraped.append(source)
        return scraped

    def _generate_search_queries(self, topic: str) -> list[str]:
        """Generate 5-8 search queries from a research topic."""
        queries = [
            topic,
            f"{topic} latest developments 2024",
            f"{topic} key players and companies",
            f"{topic} challenges and limitations",
            f"{topic} market analysis",
            f"{topic} expert opinions",
            f"{topic} statistics and data",
            f"{topic} future outlook predictions",
        ]
        return queries[:8]

    async def run_pass_1(
        self,
        query: str,
        max_sources: int,
        progress_callback: object = None,
    ) -> tuple[Pass1Output, list[ScrapedSource], list[SearchTreeNode]]:
        """PASS 1 — Broad Search."""
        logger.info("Starting Pass 1 for query: {}", query)
        root_id = str(uuid.uuid4())
        tree_nodes: list[SearchTreeNode] = []

        search_queries = self._generate_search_queries(query)
        sources_per_query = max(1, min(3, max_sources // len(search_queries)))

        search_tasks = [
            self._firecrawl_search(q, limit=sources_per_query)
            for q in search_queries
        ]
        search_results = await asyncio.gather(*search_tasks, return_exceptions=True)

        all_urls: list[str] = []
        seen_urls: set[str] = set()
        for i, (sq, result) in enumerate(zip(search_queries, search_results)):
            query_node_id = str(uuid.uuid4())
            tree_nodes.append(
                SearchTreeNode(
                    id=query_node_id,
                    label=sq,
                    node_type="query",
                    pass_number=1,
                    parent_id=root_id,
                )
            )
            if isinstance(result, Exception):
                logger.error("Search failed for '{}': {}", sq, result)
                continue
            for item in result:
                url = item.get("url", "")
                if url and url not in seen_urls and len(all_urls) < max_sources:
                    seen_urls.add(url)
                    all_urls.append(url)
                    tree_nodes.append(
                        SearchTreeNode(
                            id=str(uuid.uuid4()),
                            label=item.get("title", url)[:60],
                            node_type="source",
                            pass_number=1,
                            parent_id=query_node_id,
                            url=url,
                        )
                    )

        scraped = await self._scrape_urls(all_urls, pass_number=1)
        self.sources.extend(scraped)

        successful = [s for s in scraped if s.scrape_success and s.markdown_content]
        if not successful:
            raise ValueError("No sources could be scraped in Pass 1")

        context_parts: list[str] = []
        for s in successful:
            context_parts.append(
                f"### Source: {s.title}\nURL: {s.url}\n\n{s.markdown_content}\n\n---"
            )
        combined_content = (
            f"Research Topic: {query}\n\n"
            + "\n".join(context_parts)
        )

        result_dict = await self._call_kimi_with_validation(
            PASS_1_SYSTEM, combined_content, Pass1Output
        )
        output = Pass1Output.model_validate(result_dict)
        logger.info(
            "Pass 1 complete: {} findings, {} gaps",
            len(output.synthesis.key_findings),
            len(output.gaps),
        )
        return output, scraped, tree_nodes

    async def run_pass_2(
        self,
        pass_1_output: Pass1Output,
        max_sources_per_gap: int = 2,
        progress_callback: object = None,
    ) -> tuple[Pass2Output, list[ScrapedSource], list[SearchTreeNode]]:
        """PASS 2 — Gap Resolution."""
        logger.info("Starting Pass 2: resolving {} gaps", len(pass_1_output.gaps))
        tree_nodes: list[SearchTreeNode] = []

        sorted_gaps = sorted(
            pass_1_output.gaps,
            key=lambda g: {"high": 0, "medium": 1, "low": 2}[g.priority],
        )

        all_gap_sources: list[ScrapedSource] = []
        for gap in sorted_gaps:
            gap_node_id = str(uuid.uuid4())
            tree_nodes.append(
                SearchTreeNode(
                    id=gap_node_id,
                    label=gap.question[:60],
                    node_type="gap",
                    pass_number=2,
                    parent_id=None,
                )
            )

            results = await self._firecrawl_search(
                gap.question, limit=max_sources_per_gap
            )
            urls = [r.get("url", "") for r in results if r.get("url")]
            for r in results:
                url = r.get("url", "")
                if url:
                    tree_nodes.append(
                        SearchTreeNode(
                            id=str(uuid.uuid4()),
                            label=r.get("title", url)[:60],
                            node_type="source",
                            pass_number=2,
                            parent_id=gap_node_id,
                            url=url,
                        )
                    )

            scraped = await self._scrape_urls(urls, pass_number=2)
            all_gap_sources.extend(scraped)

        self.sources.extend(all_gap_sources)

        successful = [
            s for s in all_gap_sources if s.scrape_success and s.markdown_content
        ]
        gap_content_parts: list[str] = []
        for s in successful:
            gap_content_parts.append(
                f"### Source: {s.title}\nURL: {s.url}\n\n{s.markdown_content}\n\n---"
            )

        user_msg = (
            "## Existing Synthesis from Pass 1\n"
            + pass_1_output.synthesis.model_dump_json(indent=2)
            + "\n\n## Original Gaps\n"
            + json.dumps(
                [g.model_dump() for g in pass_1_output.gaps], indent=2
            )
            + "\n\n## New Scraped Content for Gap Resolution\n"
            + "\n".join(gap_content_parts)
        )

        result_dict = await self._call_kimi_with_validation(
            PASS_2_SYSTEM, user_msg, Pass2Output
        )
        output = Pass2Output.model_validate(result_dict)
        logger.info(
            "Pass 2 complete: {} gaps resolved, {} remaining",
            len(output.gaps_resolved),
            len(output.remaining_gaps),
        )
        return output, all_gap_sources, tree_nodes

    async def run_pass_3(
        self,
        query: str,
        pass_1_output: Pass1Output,
        pass_2_output: Pass2Output | None,
        all_sources: list[ScrapedSource],
    ) -> Pass3Output:
        """PASS 3 — Final Synthesis."""
        logger.info("Starting Pass 3: final synthesis")

        source_list = []
        for s in all_sources:
            if s.scrape_success:
                source_list.append(
                    {"url": s.url, "title": s.title, "pass": s.pass_number}
                )

        user_msg = (
            f"## Original Research Query\n{query}\n\n"
            f"## Pass 1 Output\n{pass_1_output.model_dump_json(indent=2)}\n\n"
        )
        if pass_2_output:
            user_msg += (
                f"## Pass 2 Output\n{pass_2_output.model_dump_json(indent=2)}\n\n"
            )
        user_msg += f"## All Sources\n{json.dumps(source_list, indent=2)}"

        result_dict = await self._call_kimi_with_validation(
            PASS_3_SYSTEM, user_msg, Pass3Output
        )
        output = Pass3Output.model_validate(result_dict)
        logger.info("Pass 3 complete: final report generated")
        return output

    async def run(
        self,
        query: str,
        depth: int = 2,
        max_sources: int = 10,
        progress_callback: object = None,
    ) -> dict:
        """Run the full multi-pass research pipeline."""
        self.sources = []
        self.tree_nodes = []

        root_node = SearchTreeNode(
            id=str(uuid.uuid4()),
            label=query,
            node_type="root",
            pass_number=1,
        )

        # Pass 1
        pass_1_output, pass_1_sources, pass_1_tree = await self.run_pass_1(
            query, max_sources, progress_callback
        )
        for node in pass_1_tree:
            if node.parent_id is None or node.node_type == "query":
                if node.node_type == "query":
                    node.parent_id = root_node.id

        pass_2_output: Pass2Output | None = None
        pass_2_tree: list[SearchTreeNode] = []

        # Pass 2 (if depth >= 2 and there are gaps)
        if depth >= 2 and len(pass_1_output.gaps) > 0:
            pass_2_output, pass_2_sources, pass_2_tree = await self.run_pass_2(
                pass_1_output,
                max_sources_per_gap=2,
                progress_callback=progress_callback,
            )
            for node in pass_2_tree:
                if node.parent_id is None and node.node_type == "gap":
                    node.parent_id = root_node.id

            # Early stop if no remaining gaps
            if pass_2_output and len(pass_2_output.remaining_gaps) == 0:
                logger.info("No remaining gaps — skipping further passes")

        # Pass 3 (always runs)
        pass_3_output = await self.run_pass_3(
            query, pass_1_output, pass_2_output, self.sources
        )

        # Build tree
        all_tree_nodes = pass_1_tree + pass_2_tree
        root_node.children = self._build_tree_children(root_node.id, all_tree_nodes)
        tree = root_node

        return {
            "pass_1_output": pass_1_output,
            "pass_2_output": pass_2_output,
            "pass_3_output": pass_3_output,
            "sources": self.sources,
            "tree": tree,
        }

    def _build_tree_children(
        self, parent_id: str, nodes: list[SearchTreeNode]
    ) -> list[SearchTreeNode]:
        """Recursively build tree children."""
        children: list[SearchTreeNode] = []
        for node in nodes:
            if node.parent_id == parent_id:
                node.children = self._build_tree_children(node.id, nodes)
                children.append(node)
        return children
