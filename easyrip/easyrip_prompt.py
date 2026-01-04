import os
import re
from collections.abc import Iterable

from prompt_toolkit.completion import CompleteEvent, Completer, Completion
from prompt_toolkit.document import Document
from prompt_toolkit.formatted_text import StyleAndTextTuples
from prompt_toolkit.history import FileHistory

from .global_val import C_Z, get_CONFIG_DIR


class easyrip_prompt:
    PROMPT_HISTORY_FILE = get_CONFIG_DIR() / "prompt_history.txt"

    @classmethod
    def clear(cls) -> None:
        cls.PROMPT_HISTORY_FILE.unlink(True)


class ConfigFileHistory(FileHistory):
    def store_string(self, string: str) -> None:
        if not string.startswith(C_Z):
            super().store_string(string)


class SmartPathCompleter(Completer):
    def __init__(self) -> None:
        pass

    def _highlight_fuzzy_match(
        self,
        suggestion: str,
        user_input: str,
        style_config: dict | None = None,
    ) -> StyleAndTextTuples:
        """
        高亮显示模糊匹配结果

        Args:
            suggestion: 建议的完整字符串
            user_input: 用户输入的匹配字符
            style_config: 样式配置字典

        Returns:
            包含样式信息的格式化文本

        """
        if style_config is None:
            style_config = {
                "match_char": "class:fuzzymatch.inside.character",
                "match_section": "class:fuzzymatch.inside",
                "non_match": "class:fuzzymatch.outside",
            }

        if not user_input:
            # 用户没有输入，返回原始字符串
            return [(style_config["non_match"], suggestion)]

        # 找到最佳匹配位置
        result = []

        # 简化的模糊匹配算法
        pattern = ".*?".join(map(re.escape, user_input))
        regex = re.compile(pattern, re.IGNORECASE)

        match = regex.search(suggestion)
        if not match:
            # 没有匹配，返回原始字符串
            return [(style_config["non_match"], suggestion)]

        start, end = match.span()
        match_text = suggestion[start:end]

        # 匹配段之前的文本
        if start > 0:
            result.append((style_config["non_match"], suggestion[:start]))

        # 匹配段内部的字符
        input_chars = list(user_input)
        for char in match_text:
            if input_chars and char.lower() == input_chars[0].lower():
                result.append((style_config["match_char"], char))
                input_chars.pop(0)
            else:
                result.append((style_config["match_section"], char))

        # 匹配段之后的文本
        if end < len(suggestion):
            result.append((style_config["non_match"], suggestion[end:]))

        return result

    def _fuzzy_filter_and_sort(self, filenames: list[str], match_str: str) -> list[str]:
        """模糊过滤和排序"""
        if not match_str:
            return sorted(filenames)

        # 构建模糊匹配模式
        pattern = ".*?".join(map(re.escape, match_str))
        regex = re.compile(f"(?=({pattern}))", re.IGNORECASE)

        matches = []
        for filename in filenames:
            regex_matches = list(regex.finditer(filename))
            if regex_matches:
                # 找到最佳匹配（最左、最短）
                best = min(regex_matches, key=lambda m: (m.start(), len(m.group(1))))
                matches.append((best.start(), len(best.group(1)), filename))

        # 按匹配质量排序：先按匹配位置，再按匹配长度
        matches.sort(key=lambda x: (x[0], x[1]))
        return [item[2] for item in matches]

    def get_completions(
        self,
        document: Document,
        complete_event: CompleteEvent,  # noqa: ARG002
    ) -> Iterable[Completion]:
        text = document.text_before_cursor
        input_path = text.strip("\"'")

        try:
            directory = os.path.dirname(input_path) or "."
            basename = os.path.basename(input_path)

            filenames: list[str] = (
                os.listdir(directory) if os.path.isdir(directory) else []
            )

            for filename in self._fuzzy_filter_and_sort(filenames, basename):
                full_name = (
                    filename if directory == "." else os.path.join(directory, filename)
                )

                if os.path.isdir(full_name):
                    filename += "/"

                completion = full_name

                if any(c in r""" !$%&()*:;<=>?[]^`{|}~""" for c in completion):
                    completion = f'"{completion}"'

                yield Completion(
                    text=completion,
                    start_position=-len(text),
                    display=self._highlight_fuzzy_match(filename, basename),
                )

        except OSError:
            pass
