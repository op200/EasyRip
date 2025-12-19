import re
from collections.abc import Iterable
from io import BytesIO
from pathlib import Path
from typing import Final

import fontTools

from ... import global_val
from ...easyrip_log import log
from ...utils import get_base62_time, non_ascii_str_len
from .ass import (
    Ass,
    Attach_type,
    Attachment_data,
    Event_data,
    Event_type,
    Script_info_data,
)
from .font import Font, Font_type, load_fonts, load_windows_fonts, subset_font


def _bold_italic_to_font_type(bold: bool | int, italic: bool | int) -> Font_type:
    if bold:
        return Font_type.Bold_Italic if italic else Font_type.Bold
    return Font_type.Italic if italic else Font_type.Regular


def subset(
    sub_path_list: Iterable[str | Path],
    font_path_list: Iterable[str | Path],
    output_dir: str | Path = Path("subset"),
    *,
    font_in_sub: bool = False,
    use_win_font: bool = False,
    use_libass_spec: bool = False,
    drop_non_render: bool = True,
    drop_unkow_data: bool = True,
    strict: bool = False,
) -> bool:
    DEFAULT_STYLE_NAME = "Default"

    return_res: bool = True

    subset_sub_dict: dict[str, tuple[Path, Ass]] = {}
    subset_font_bytes_and_name_dict: dict[str, list[tuple[str, bytes]]] = {}

    output_dir = Path(output_dir)

    lock_file = output_dir / "subset-lock"
    if output_dir.is_dir():
        if lock_file.is_file():
            lock_file.unlink()
            for item in output_dir.iterdir():
                if item.is_file() and item.suffix.lower() in {".ass", ".ttf", ".otf"}:
                    try:
                        item.unlink()
                    except Exception as e:
                        log.warning("Error deleting {}: {}", item.name, e)
                        return_res = False
        if not any(output_dir.iterdir()):
            lock_file.touch()
        else:
            log.warning('There are other files in this directory "{}"', output_dir)
            return_res = False
    else:
        output_dir.mkdir()
        lock_file.touch()

    family__affix: dict[str, str] = {}

    def get_font_new_name(org_name: str) -> str:
        """
        输入字体名，返回子集化后的字体名

        注意: 用这个函数生成子集化字体名，任何需要子集化的字体名都需要经过这个函数
        """
        if org_name not in family__affix:
            family__affix[org_name] = f"__subset_{get_base62_time()}__"
        return family__affix[org_name] + org_name

    # 解析 ASS 并生成子字符集
    font_sign__subset_str: dict[tuple[str, Font_type], dict[str, str]] = {}
    for _ass_path in sub_path_list:
        path_and_sub = Ass(_ass_path := Path(_ass_path))
        _ass_path_abs = str(_ass_path.absolute())

        # Styles
        style__font_sign: dict[str, tuple[str, Font_type]] = {}
        for style in path_and_sub.styles.data:
            _is_vertical: bool = style.Fontname[0] == "@"
            _font_name: str = style.Fontname[1:] if _is_vertical else style.Fontname
            # 获取
            style__font_sign[style.Name] = (
                _font_name,
                _bold_italic_to_font_type(style.Bold, style.Italic),
            )

            # 修改
            style.Fontname = (
                f"{'@' if _is_vertical else ''}{get_font_new_name(_font_name)}"
            )

        # Events
        for event in path_and_sub.events.data:
            if event.type != Event_type.Dialogue:
                continue

            default_font_sign: tuple[str, Font_type]

            # 获取每行的默认字体
            if event.Style not in style__font_sign:
                if DEFAULT_STYLE_NAME in style__font_sign:
                    log.warning(
                        "The style '{}' not in Styles. Defaulting to the style '{}'",
                        event.Style,
                        DEFAULT_STYLE_NAME,
                    )
                    default_font_sign = style__font_sign[DEFAULT_STYLE_NAME]
                    return_res = not strict
                else:
                    log.warning(
                        "The style '{}' and the style 'Default' not in Styles. Defaulting to no font",
                        event.Style,
                    )
                    default_font_sign = ("", Font_type.Regular)
                    return_res = not strict
            else:
                default_font_sign = style__font_sign[event.Style]

            new_text = ""
            # 解析 Text
            current_font_sign: tuple[str, Font_type] = default_font_sign
            for is_tag, text in Event_data.parse_text(event.Text, use_libass_spec):
                if is_tag:
                    tag_fn_org: str | None = None
                    tag_fn: str | None = None
                    tag_bold: str | None = None
                    tag_italic: str | None = None

                    for tag, value in re.findall(
                        r"\\\s*(fn|b(?![a-zA-Z])|i(?![a-zA-Z])|r)([^\\}]*)", text
                    ):
                        assert isinstance(tag, str) and isinstance(value, str)

                        proc_value = value.strip()
                        if proc_value.startswith("("):
                            proc_value = proc_value[1:]
                            if (_index := proc_value.find(")")) != -1:
                                proc_value = proc_value[:_index]
                            proc_value = proc_value.strip()

                        match tag:
                            case "fn":
                                tag_fn_org, tag_fn = value, proc_value
                            case "b":
                                tag_bold = proc_value
                            case "i":
                                tag_italic = proc_value
                            case "r":
                                r_value = proc_value if "(" in value else value.rstrip()
                                if r_value in style__font_sign:
                                    current_font_sign = style__font_sign[r_value]
                                else:
                                    # 空为还原样式, 非样式表内样式名效果同空, 但发出不规范警告
                                    current_font_sign = default_font_sign
                                    if r_value != "":
                                        log.warning(
                                            "The \\r style '{}' not in Styles", r_value
                                        )

                    new_fontname: str = current_font_sign[0]
                    new_bold: bool
                    new_italic: bool
                    new_bold, new_italic = current_font_sign[1].value

                    if tag_fn is not None:
                        match tag_fn:
                            case "":
                                new_fontname = default_font_sign[0]
                            case _:
                                _is_vertical: bool = tag_fn.startswith("@")
                                new_fontname = tag_fn[1:] if _is_vertical else tag_fn

                                # 修改
                                text = text.replace(
                                    f"\\fn{tag_fn_org}",
                                    f"\\fn{'@' if _is_vertical else ''}{get_font_new_name(new_fontname)}",
                                )

                    if tag_bold is not None:
                        match tag_bold:
                            case "":
                                new_bold = default_font_sign[1].value[0]
                            case "0":
                                new_bold = False
                            case "1":
                                new_bold = True
                            case _:
                                log.error(
                                    "Illegal format: '{}' in file \"{}\" in line: {}",
                                    f"\\b{tag_bold}",
                                    _ass_path,
                                    event.Text,
                                )
                                return_res = not strict

                    if tag_italic is not None:
                        match tag_italic:
                            case "":
                                new_italic = default_font_sign[1].value[1]
                            case "0":
                                new_italic = False
                            case "1":
                                new_italic = True
                            case _:
                                log.error(
                                    "Illegal format: '{}' in file \"{}\" in line: {}",
                                    f"\\i{tag_italic}",
                                    _ass_path,
                                    event.Text,
                                )
                                return_res = not strict

                    current_font_sign = (
                        new_fontname,
                        Font_type((new_bold, new_italic)),
                    )

                elif current_font_sign[0]:  # 空字符串为不使用字体
                    add_text = re.sub(r"\\[nN]", "", text).replace("\\h", "\u00a0")

                    if current_font_sign not in font_sign__subset_str:
                        font_sign__subset_str[current_font_sign] = {}

                    if _ass_path_abs in font_sign__subset_str[current_font_sign]:
                        font_sign__subset_str[current_font_sign][_ass_path_abs] += (
                            add_text
                        )
                    else:
                        font_sign__subset_str[current_font_sign][_ass_path_abs] = (
                            add_text
                        )

                # 修改
                new_text += text

            # 修改
            event.Text = new_text

        # 修改子集化后的字幕
        family__affix_k_max_na_len: int = max(
            map(non_ascii_str_len, family__affix.keys())
        )
        path_and_sub.script_info.data = [
            Script_info_data(
                raw_str=f"Font Subset Info: {global_val.PROJECT_TITLE} & {fontTools.__name__} v{fontTools.__version__}"
            ),
            Script_info_data(
                raw_str=f"Font Subset Setting: {
                    '  '.join(
                        f'{k} {v}'
                        for k, v in {
                            '-subset-font-in-sub': '1' if font_in_sub else '0',
                            '-subset-use-win-font': '1' if use_win_font else '0',
                            '-subset-use-libass-spec': '1' if use_libass_spec else '0',
                            '-subset-drop-non-render': '1' if drop_non_render else '0',
                            '-subset-drop-unkow-data': '1' if drop_unkow_data else '0',
                            '-subset-strict': '1' if strict else '0',
                        }.items()
                    )
                }"
            ),
            *(
                Script_info_data(
                    raw_str=f'Font Subset Mapping: {f'"{k}"':<{2 + family__affix_k_max_na_len - (non_ascii_str_len(k) - len(k))}}   -->   "{v}{k}"'
                )
                for k, v in family__affix.items()
            ),
        ] + path_and_sub.script_info.data
        subset_sub_dict[_ass_path_abs] = (output_dir / _ass_path.name, path_and_sub)

    # 加载 Font
    fonts: Final[list[Font]] = []
    for _path in font_path_list:
        fonts.extend(load_fonts(_path, strict=strict))
    if use_win_font:
        fonts.extend(load_windows_fonts(strict=strict))

    font_sign__font: dict[tuple[str, Font_type], Font] = {}
    family_lower__family = {}  # 存储小写 family 用于判断 ASS 的大小写不敏感语法
    for _font in fonts:
        for family in _font.familys:
            family_lower__family[family.lower()] = family
            font_sign__font[(family, _font.font_type)] = _font

    # 子集化映射
    font__subset_str: dict[Font, dict[str, str]] = {}
    for key, val in font_sign__subset_str.items():
        _k: tuple[str, Font_type] = key
        if key not in font_sign__font:
            if strict:
                log.error("{} not found. Skip it", key, deep=strict)
                return_res = False
                continue

            # 模糊字重
            _font = None
            match key[1]:
                case Font_type.Regular:
                    if (
                        (_k := (key[0], Font_type.Bold)) in font_sign__font
                        or (_k := (key[0], Font_type.Italic)) in font_sign__font
                        or (_k := (key[0], Font_type.Bold_Italic)) in font_sign__font
                    ):
                        _font = font_sign__font[_k]

                case Font_type.Bold:
                    if (
                        (_k := (key[0], Font_type.Regular)) in font_sign__font
                        or (_k := (key[0], Font_type.Bold_Italic)) in font_sign__font
                        or (_k := (key[0], Font_type.Italic)) in font_sign__font
                    ):
                        _font = font_sign__font[_k]

                case Font_type.Italic:
                    if (
                        (_k := (key[0], Font_type.Regular)) in font_sign__font
                        or (_k := (key[0], Font_type.Bold_Italic)) in font_sign__font
                        or (_k := (key[0], Font_type.Bold)) in font_sign__font
                    ):
                        _font = font_sign__font[_k]

                case Font_type.Bold_Italic:
                    if (
                        (_k := (key[0], Font_type.Bold)) in font_sign__font
                        or (_k := (key[0], Font_type.Italic)) in font_sign__font
                        or (_k := (key[0], Font_type.Regular)) in font_sign__font
                    ):
                        _font = font_sign__font[_k]

            # 模糊字重也找不到字体
            if _font is None:
                _want_font_sign_str = f"( {key[0]} / {key[1].name} )"
                if (_f_low := key[0].lower()) in family_lower__family:
                    log.error(
                        "{} not found. Skip it. Perhaps you want the {}",
                        _want_font_sign_str,
                        f"'{family_lower__family[_f_low]}'",
                        deep=strict,
                    )
                else:
                    log.error(
                        "{} not found. Skip it",
                        _want_font_sign_str,
                        deep=strict,
                    )
                return_res = False
                continue

        else:
            _font = font_sign__font[key]

        if _font in font__subset_str:
            for k, v in val.items():
                if k in font__subset_str[_font]:
                    font__subset_str[_font][k] += v
                else:
                    font__subset_str[_font][k] = v
        else:
            font__subset_str[_font] = val

        # 映射日志
        mapping_res: str = ""

        if key[0] == _k[0]:
            if key[1] != _k[1]:
                mapping_res = f"( _ / {_k[1].name} )"
        else:
            mapping_res = f"( {_k[0]} / {'_' if key[1] == _k[1] else _k[1].name} )"

        if mapping_res:
            mapping_res = " -> " + mapping_res

        log.info(
            "Font family auto mapping: {}",
            f"( {key[0]} / {key[1].name} ){mapping_res}",
            deep=(strict and bool(mapping_res)),
        )
        log.debug(
            f"{_font.pathname}: {_font.familys} {_font.font_type.name}",
            is_format=False,
        )

    # 子集化字体
    for key, val in font__subset_str.items():
        _affix: str
        _basename: str
        _infix: str
        _suffix: str
        for family in key.familys:
            if family in family__affix:
                _affix = family__affix[family]
                _basename = family
                _infix = key.font_type.name
                _suffix = "otf" if key.font.sfntVersion == "OTTO" else "ttf"
                break
        else:
            raise AssertionError("No font name")

        if font_in_sub:
            for org_path_abs, s in val.items():
                new_font, is_subset_success = subset_font(key, s, _affix)

                if strict and is_subset_success is False:
                    return_res = False

                with BytesIO() as buffer:
                    new_font.save(buffer)
                    if org_path_abs not in subset_font_bytes_and_name_dict:
                        subset_font_bytes_and_name_dict[org_path_abs] = []
                    subset_font_bytes_and_name_dict[org_path_abs].append(
                        (
                            f"{_affix}{_basename}_{'B' if key.font_type in {Font_type.Bold, Font_type.Bold_Italic} else ''}{'I' if key.font_type in {Font_type.Italic, Font_type.Bold_Italic} else ''}0.{_suffix}",
                            buffer.getvalue(),
                        )
                    )
        else:
            new_font, is_subset_success = subset_font(
                key, "".join(v for v in val.values()), _affix
            )

            if strict and is_subset_success is False:
                return_res = False

            new_font.save(output_dir / f"{_affix}{_basename}.{_infix}.{_suffix}")

    # 保存子集化的字幕
    for org_path_abs_1, path_and_sub in subset_sub_dict.items():
        # 内嵌字体
        if font_in_sub:
            for (
                org_path_abs_2,
                font_bytes_and_name_list,
            ) in subset_font_bytes_and_name_dict.items():
                if org_path_abs_1 == org_path_abs_2:
                    for font_bytes_and_name in font_bytes_and_name_list:
                        path_and_sub[1].attachments.data.append(
                            Attachment_data(
                                type=Attach_type.Fonts,
                                name=font_bytes_and_name[0],
                                org_data=font_bytes_and_name[1],
                            )
                        )

        with path_and_sub[0].open("wt", encoding="utf-8-sig", newline="\n") as f:
            f.write(
                path_and_sub[1].__str__(
                    drop_non_render=drop_non_render, drop_unkow_data=drop_unkow_data
                )
            )

    # 释放文件占用
    for font in font_sign__font.values():
        font.__del__()

    return return_res
