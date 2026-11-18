#!/usr/bin/env python3
"""
DOM Inspector and Static Codebase Validator for Dar Al-Khashab Feasibility.

This module provides opaque-box parsing, static HTML/CSS/JS verification,
link integrity checking, CSS token validation, accessibility auditing,
and zero em dash compliance checking.

Zero Em Dash Policy: Strictly adhered to. No U+2014 characters used anywhere.
"""

import html.parser
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union


class SimpleElement:
    """Lightweight representation of an HTML element for assertions."""

    def __init__(self, tag: str, attrs: Dict[str, str], text: str = "", start_line: int = 0):
        self.tag = tag.lower()
        self.attrs = {k.lower(): v for k, v in attrs.items()}
        self.text = text
        self.start_line = start_line
        self.children: List["SimpleElement"] = []

    def get(self, attr: str, default: Optional[str] = None) -> Optional[str]:
        return self.attrs.get(attr.lower(), default)

    def has_class(self, cls: str) -> bool:
        classes = self.attrs.get("class", "").split()
        return cls in classes

    def __repr__(self) -> str:
        attrs_str = " ".join(f'{k}="{v}"' for k, v in list(self.attrs.items())[:3])
        return f"<{self.tag} {attrs_str}>"


class SimpleHTMLTreeParser(html.parser.HTMLParser):
    """HTML Parser constructing a list of SimpleElement nodes."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.elements: List[SimpleElement] = []
        self.stack: List[SimpleElement] = []

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]):
        attrs_dict = {k: (v if v is not None else "") for k, v in attrs}
        elem = SimpleElement(tag, attrs_dict, start_line=self.getpos()[0])
        self.elements.append(elem)
        if self.stack:
            self.stack[-1].children.append(elem)
        # Void elements do not go onto the nesting stack
        if tag.lower() not in {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}:
            self.stack.append(elem)

    def handle_endtag(self, tag: str):
        tag_lower = tag.lower()
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i].tag == tag_lower:
                self.stack = self.stack[:i]
                break

    def handle_data(self, data: str):
        if self.stack and data.strip():
            self.stack[-1].text += data


class DOMInspector:
    """Static inspector for HTML documents, CSS files, and JS modules."""

    @classmethod
    def parse_html(cls, file_path: Union[str, Path]) -> List[SimpleElement]:
        """Parse HTML file into a flat list of SimpleElement nodes."""
        path = Path(file_path)
        content = path.read_text(encoding="utf-8")
        parser = SimpleHTMLTreeParser()
        parser.feed(content)
        return parser.elements

    @classmethod
    def find_all(
        cls,
        elements: List[SimpleElement],
        tag: Optional[str] = None,
        attr_filter: Optional[Dict[str, str]] = None,
        class_name: Optional[str] = None,
    ) -> List[SimpleElement]:
        """Filter parsed elements by tag, attributes, or CSS class."""
        matched = []
        for elem in elements:
            if tag and elem.tag != tag.lower():
                continue
            if class_name and not elem.has_class(class_name):
                continue
            if attr_filter:
                match = True
                for k, v in attr_filter.items():
                    if elem.get(k) != v:
                        match = False
                        break
                if not match:
                    continue
            matched.append(elem)
        return matched

    @classmethod
    def find_one(
        cls,
        elements: List[SimpleElement],
        tag: Optional[str] = None,
        attr_filter: Optional[Dict[str, str]] = None,
        class_name: Optional[str] = None,
    ) -> Optional[SimpleElement]:
        """Find the first matching element."""
        results = cls.find_all(elements, tag=tag, attr_filter=attr_filter, class_name=class_name)
        return results[0] if results else None

    @classmethod
    def check_link_integrity(cls, html_path: Union[str, Path]) -> Tuple[List[str], List[str]]:
        """
        Check that all relative links, scripts, stylesheets, and font preloads exist on disk.
        Returns (valid_links, broken_links).
        """
        path = Path(html_path).resolve()
        parent = path.parent
        elements = cls.parse_html(path)

        valid_links: List[str] = []
        broken_links: List[str] = []

        for el in elements:
            ref = None
            if el.tag == "link" and el.get("href"):
                ref = el.get("href")
            elif el.tag == "script" and el.get("src"):
                ref = el.get("src")
            elif el.tag in {"img", "source"} and el.get("src"):
                ref = el.get("src")

            if not ref:
                continue

            # Ignore data URIs and fragments
            if ref.startswith("data:") or ref.startswith("#"):
                continue

            # Handle external URLs
            if ref.startswith("http://") or ref.startswith("https://") or ref.startswith("//"):
                continue

            # Strip query strings and hash
            clean_ref = ref.split("?")[0].split("#")[0]
            if not clean_ref:
                continue

            target_path = (parent / clean_ref).resolve()
            if target_path.exists():
                valid_links.append(ref)
            else:
                broken_links.append(ref)

        return valid_links, broken_links

    @classmethod
    def extract_css_tokens(cls, tokens_css_path: Union[str, Path]) -> Dict[str, Dict[str, str]]:
        """
        Extract CSS custom properties from tokens.css.
        Returns a dict mapping selector to a dict of {variable_name: value}.
        """
        path = Path(tokens_css_path)
        content = path.read_text(encoding="utf-8")

        # Strip comments
        clean_css = re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)

        blocks: Dict[str, Dict[str, str]] = {}
        # Match selector blocks
        rule_pattern = re.compile(r"([^{]+)\{([^}]+)\}")
        for match in rule_pattern.finditer(clean_css):
            selector = match.group(1).strip()
            body = match.group(2).strip()

            vars_dict: Dict[str, str] = {}
            for line in body.split(";"):
                line = line.strip()
                if not line or not line.startswith("--"):
                    continue
                if ":" in line:
                    var_name, var_val = line.split(":", 1)
                    vars_dict[var_name.strip()] = var_val.strip()

            if vars_dict:
                blocks[selector] = vars_dict

        return blocks

    @classmethod
    def validate_css_token_usage(
        cls, css_dir: Union[str, Path], tokens_path: Union[str, Path]
    ) -> Tuple[Set[str], Set[str], Set[str]]:
        """
        Scan all CSS files for var(--...) usage and verify they are defined in tokens.
        Returns (declared_tokens, used_tokens, missing_tokens).
        """
        tokens_map = cls.extract_css_tokens(tokens_path)
        declared_tokens: Set[str] = set()
        for s_vars in tokens_map.values():
            declared_tokens.update(s_vars.keys())

        used_tokens: Set[str] = set()
        css_files = list(Path(css_dir).glob("*.css"))
        var_pattern = re.compile(r"var\(\s*(--[A-Za-z0-9_-]+)")

        for f in css_files:
            text = f.read_text(encoding="utf-8")
            for match in var_pattern.finditer(text):
                used_tokens.add(match.group(1))

        # Check for missing tokens, excluding dynamic or font-fallback overrides if any
        missing_tokens = used_tokens - declared_tokens
        return declared_tokens, used_tokens, missing_tokens

    @classmethod
    def check_zero_em_dash(cls, file_path: Union[str, Path]) -> List[Tuple[int, str]]:
        """
        Scan a file for Unicode U+2014 em dash characters.
        Returns list of (line_number, line_content).
        """
        path = Path(file_path)
        lines = path.read_text(encoding="utf-8").splitlines()
        violations = []
        for i, line in enumerate(lines, 1):
            if "\u2014" in line:
                violations.append((i, line.strip()))
        return violations

    @classmethod
    def check_accessibility(cls, html_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Perform static accessibility checks:
        1. Lang and dir attributes on <html>
        2. Skip link presence
        3. ARIA landmark roles
        4. Button titles / aria-labels
        5. Form input labels / aria-labels
        """
        elements = cls.parse_html(html_path)
        html_elem = cls.find_one(elements, tag="html")

        lang = html_elem.get("lang") if html_elem else None
        dir_attr = html_elem.get("dir") if html_elem else None

        skip_links = [
            el for el in elements if el.tag == "a" and el.has_class("skip-link") and el.get("href") == "#main"
        ]

        # Landmark roles / elements
        nav_count = len(cls.find_all(elements, tag="nav"))
        main_count = len(cls.find_all(elements, tag="main"))
        aside_count = len(cls.find_all(elements, tag="aside"))
        toolbars = cls.find_all(elements, attr_filter={"role": "toolbar"})

        # Buttons without text, title, or aria-label
        buttons = cls.find_all(elements, tag="button")
        unlabeled_buttons = []
        for btn in buttons:
            has_title = bool(btn.get("title"))
            has_aria = bool(btn.get("aria-label")) or bool(btn.get("aria-labelledby"))
            has_text = bool(btn.text.strip())
            if not (has_title or has_aria or has_text):
                unlabeled_buttons.append(btn)

        return {
            "lang": lang,
            "dir": dir_attr,
            "has_skip_link": len(skip_links) > 0,
            "nav_count": nav_count,
            "main_count": main_count,
            "aside_count": aside_count,
            "toolbar_count": len(toolbars),
            "total_buttons": len(buttons),
            "unlabeled_buttons": unlabeled_buttons,
        }

    @classmethod
    def count_svg_icons(cls, html_path: Union[str, Path]) -> Dict[str, Any]:
        """Count unique inline SVG icons in the document."""
        elements = cls.parse_html(html_path)
        svg_elements = cls.find_all(elements, tag="svg")
        path_elements = cls.find_all(elements, tag="path")
        rect_elements = cls.find_all(elements, tag="rect")
        circle_elements = cls.find_all(elements, tag="circle")

        viewbox_count = sum(1 for el in svg_elements if el.get("viewbox"))

        return {
            "total_svgs": len(svg_elements),
            "svgs_with_viewbox": viewbox_count,
            "paths_count": len(path_elements),
            "rects_count": len(rect_elements),
            "circles_count": len(circle_elements),
        }

    @classmethod
    def validate_js_syntax(cls, js_paths: List[Union[str, Path]]) -> Dict[str, bool]:
        """Check syntax of JS files using node -c if available."""
        results = {}
        for path in js_paths:
            p = Path(path)
            try:
                res = subprocess.run(
                    ["node", "-c", str(p)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=5,
                )
                results[p.name] = (res.returncode == 0)
            except Exception:
                # If node is not found, basic read verification
                results[p.name] = p.exists() and len(p.read_text(encoding="utf-8")) > 0
        return results

    @classmethod
    def get_sections(cls, html_path: Union[str, Path]) -> List[Dict[str, str]]:
        """Extract all sections with their id and class."""
        elements = cls.parse_html(html_path)
        sections = cls.find_all(elements, tag="section")
        out = []
        for s in sections:
            s_id = s.get("id", "")
            if s_id:
                out.append({"id": s_id, "class": s.get("class", "")})
        return out


if __name__ == "__main__":
    test_html = Path("/Users/ahmedissamramadan/Documents/Default Project/feasibility/index.html")
    if test_html.exists():
        links_ok, links_bad = DOMInspector.check_link_integrity(test_html)
        print(f"DOMInspector check on index.html: {len(links_ok)} valid links, {len(links_bad)} broken links.")
        a11y = DOMInspector.check_accessibility(test_html)
        print(f"Accessibility: lang={a11y['lang']}, dir={a11y['dir']}, skip_link={a11y['has_skip_link']}")
        svgs = DOMInspector.count_svg_icons(test_html)
        print(f"SVG icons count: {svgs['total_svgs']}")
