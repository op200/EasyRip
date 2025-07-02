from pathlib import Path
import re
from typing import Iterable

from ...global_val import GlobalVal
from ...easyrip_log import log
from .ass import Ass, Script_info_data, parse_ass_text
from .font import Font_type, Font, load_fonts, subset_font, get_font_path_from_registry
from ..utils import UTF8_BOM, get_base62_time


def _bold_italic_to_font_type(bold: bool | int, italic: bool | int) -> Font_type:
    if bold:
        return Font_type.Bold_Italic if italic else Font_type.Bold
    else:
        return Font_type.Italic if italic else Font_type.Regular


def subset(
    sub_path_list: Iterable[str | Path],
    font_path_list: Iterable[str | Path],
    output_dir: str | Path = Path("subset"),
    *,
    use_win_font: bool = False,
    use_libass_spec: bool = False,
    drop_unrander: bool = True,
    drop_unkow_data: bool = True,
    strict: bool = False,
) -> bool:
    return_res: bool = True

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

    def get_font_new_name(org_name: str):
        if org_name not in family__affix:
            family__affix[org_name] = f"__subset_{get_base62_time()}__"
        return family__affix[org_name] + org_name

    # 解析 ASS 并生成子字符集
    font_sign__subset_str: dict[tuple[str, Font_type], str] = {}
    for _ass_path in sub_path_list:
        sub = Ass(_ass_path := Path(_ass_path))

        # Styles
        style__font_sign: dict[str, tuple[str, Font_type]] = {}
        for style in sub.style.data:
            # 获取
            style__font_sign[style.Name] = (
                style.Fontname,
                _bold_italic_to_font_type(style.Bold, style.Italic),
            )

            # 修改
            style.Fontname = get_font_new_name(style.Fontname)

        # Events
        for event in sub.event.data:
            default_font_sign: tuple[str, Font_type]

            # 获取每行的默认字体
            if event.Style not in style__font_sign:
                if "Default" in style__font_sign:
                    log.warning(
                        "The style {} not in Styles. Defaulting to the style 'Default'",
                        event.Style,
                    )
                    default_font_sign = style__font_sign["Default"]
                    return_res = not strict
                else:
                    log.error(
                        "The style {} and the style 'Default' not in Styles. Defaulting to the font 'Arial'",
                        event.Style,
                    )
                    default_font_sign = ("Arial", Font_type.Regular)
                    return_res = not strict
            else:
                default_font_sign = style__font_sign[event.Style]

            new_text = ""
            # 解析 Text
            current_font_sign: tuple[str, Font_type] = default_font_sign
            for is_tag, text in parse_ass_text(event.Text, use_libass_spec):
                if is_tag:
                    tag_fn: str | None = None
                    tag_bold: str | None = None
                    tag_italic: str | None = None

                    for tag, value in re.findall(r"\\(fn@|fn|b|i)([^\\}]*)", text):
                        match tag:
                            case "fn@" | "fn":
                                tag_fn = value
                            case "b":
                                tag_bold = value
                            case "i":
                                tag_italic = value

                    new_fontname: str = current_font_sign[0]
                    new_bold: bool
                    new_italic: bool
                    new_bold, new_italic = current_font_sign[1].value

                    if tag_fn is not None:
                        match _tag_fn := tag_fn.strip():
                            case "":
                                new_fontname = default_font_sign[0]
                            case _:
                                new_fontname = _tag_fn

                        # 修改
                        text = text.replace(
                            f"\\fn{tag_fn}", f"\\fn{get_font_new_name(new_fontname)}"
                        ).replace(
                            f"\\fn@{tag_fn}", f"\\fn@{get_font_new_name(new_fontname)}"
                        )

                    if tag_bold is not None:
                        match tag_bold.strip():
                            case "":
                                new_bold = default_font_sign[1].value[0]
                            case "0":
                                new_bold = False
                            case "1":
                                new_bold = True

                    if tag_italic is not None:
                        match tag_italic.strip():
                            case "":
                                new_italic = default_font_sign[1].value[1]
                            case "0":
                                new_italic = False
                            case "1":
                                new_italic = True

                    current_font_sign = (
                        new_fontname,
                        Font_type((new_bold, new_italic)),
                    )

                else:
                    add_text = re.sub(r"\\[nN]", "", text).replace("\\h", "\u00a0")
                    if current_font_sign in font_sign__subset_str:
                        font_sign__subset_str[current_font_sign] += add_text
                    else:
                        font_sign__subset_str[current_font_sign] = add_text

                # 修改
                new_text += text

            # 修改
            event.Text = new_text

        # 保存子集化后的字幕
        sub.script_info.data = [
            Script_info_data(
                raw_str=f"; ---------- Font Subset by {GlobalVal.PROJECT_TITLE} ----------"
            ),
            *(
                Script_info_data(
                    raw_str=f'; Font Subset Mapping: "{v}{k}"   ->   "{k}"'
                )
                for k, v in family__affix.items()
            ),
            Script_info_data(
                raw_str=f"; ---------- {'Font Subset End':^{len(GlobalVal.PROJECT_TITLE) + 20}} ----------"
            ),
        ] + sub.script_info.data
        with (output_dir / _ass_path.name).open("wb") as f:
            f.write(UTF8_BOM)
            f.write(
                sub.__str__(
                    drop_unrander=drop_unrander, drop_unkow_data=drop_unkow_data
                ).encode("utf-8")
            )

    # 加载 Font
    fonts: list[Font] = []
    for _ass_path in font_path_list:
        fonts += load_fonts(_ass_path)

    font_sign__font: dict[tuple[str, Font_type], Font] = {}
    for _font in fonts:
        for family in _font.familys:
            if family not in font_sign__font:
                font_sign__font[(family, _font.font_type)] = _font

    # 子集化映射
    font__subset_str: dict[Font, str] = {}
    for key, val in font_sign__subset_str.items():
        if key not in font_sign__font and use_win_font:
            # 从系统获取
            for _path in get_font_path_from_registry(key[0]):
                for _font in load_fonts(_path):
                    for _family in _font.familys:
                        if _family not in font_sign__font:
                            font_sign__font[(_family, _font.font_type)] = _font

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
                    if (_k := (key[0], Font_type.Bold)) in font_sign__font:
                        _font = font_sign__font[_k]
                    elif (_k := (key[0], Font_type.Bold_Italic)) in font_sign__font:
                        _font = font_sign__font[_k]
                    elif (_k := (key[0], Font_type.Italic)) in font_sign__font:
                        _font = font_sign__font[_k]

                case Font_type.Bold:
                    if (_k := (key[0], Font_type.Bold_Italic)) in font_sign__font:
                        _font = font_sign__font[_k]
                    elif (_k := (key[0], Font_type.Regular)) in font_sign__font:
                        _font = font_sign__font[_k]
                    elif (_k := (key[0], Font_type.Italic)) in font_sign__font:
                        _font = font_sign__font[_k]

                case Font_type.Italic:
                    if (_k := (key[0], Font_type.Regular)) in font_sign__font:
                        _font = font_sign__font[_k]
                    elif (_k := (key[0], Font_type.Bold)) in font_sign__font:
                        _font = font_sign__font[_k]

                case Font_type.Bold_Italic:
                    if (_k := (key[0], Font_type.Bold)) in font_sign__font:
                        _font = font_sign__font[_k]
                    elif (_k := (key[0], Font_type.Regular)) in font_sign__font:
                        _font = font_sign__font[_k]

            # 模糊字重也找不到字体
            if _font is None:
                log.error(
                    "{} not found. Skip it",
                    f"( {key[0]} / {key[1].name} )",
                    deep=strict,
                )
                return_res = False
                continue

        else:
            _font = font_sign__font[key]

        if _font in font__subset_str:
            font__subset_str[_font] += val
        else:
            font__subset_str[_font] = val

        # 映射日志
        mapping_res: str

        if key[0] == _k[0]:
            if key[1] == _k[1]:
                mapping_res = ""
            else:
                mapping_res = f"( _ / {_k[1].name} )"
        else:
            mapping_res = f"( {_k[0]} / {'_' if key[1] == _k[1] else _k[1].name} )"

        if mapping_res:
            mapping_res = " -> " + mapping_res

        log.info(
            "Auto mapping: {}",
            f"( {key[0]} / {key[1].name} ){mapping_res}",
            deep=strict,
        )

    # 子集化字体
    for key, val in font__subset_str.items():
        affix: str
        new_filename: str
        for family in key.familys:
            if family in family__affix:
                affix = family__affix[family]
                new_filename = (
                    affix
                    + family
                    + f".{key.font_type.name}"
                    + (".otf" if key.font.sfntVersion == "OTTO" else ".ttf")
                )
                break
        else:
            log.error("No font name", deep=True)
            return_res = False
            raise Exception()

        new_font = subset_font(key.font, val, affix)
        new_font.save(output_dir / new_filename)

    return return_res
