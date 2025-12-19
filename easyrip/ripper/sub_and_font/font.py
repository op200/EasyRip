import enum
import itertools
import os
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final

from fontTools import subset
from fontTools.ttLib import TTCollection, TTFont
from fontTools.ttLib.tables._n_a_m_e import NameRecord, makeName, table__n_a_m_e
from fontTools.ttLib.ttFont import TTLibError

from ...easyrip_log import log
from ...easyrip_mlang import Mlang_exception


class Font_error(Mlang_exception):
    pass


class Font_type(enum.Enum):
    Regular = (False, False)
    Bold = (True, False)
    Italic = (False, True)
    Bold_Italic = (True, True)


@dataclass(slots=True)
class Font:
    pathname: str
    font: TTFont
    familys: set[str] = field(default_factory=set[str])
    font_type: Font_type = Font_type.Regular

    def __hash__(self) -> int:
        return hash(self.pathname)

    def __del__(self) -> None:
        self.font.close()


def load_fonts(
    path: str | Path,
    *,
    lazy: bool = True,
    strict: bool = False,
) -> list[Font]:
    """strict: Skip UnicodeDecodeError font file"""
    if isinstance(path, str):
        path = Path(path)

    res_font_list: Final[list[Font]] = []

    for file in path.iterdir() if path.is_dir() else (path,):
        if not (
            file.is_file()
            and (suffix := file.suffix.lower()) in {".ttf", ".otf", ".ttc"}
        ):
            continue

        try:
            for font in (
                list[TTFont](TTCollection(file=file, lazy=lazy))
                if suffix == ".ttc"
                else [TTFont(file=file, lazy=lazy)]
            ):
                skip_this_font: bool = False
                table_name: table__n_a_m_e | None = font.get("name")

                if table_name is None:
                    log.warning(f"No 'name' table found in font {file}")
                    continue

                res_font = Font(str(file), font)
                is_regular: bool = False
                is_bold: bool = False
                is_italic: bool = False

                for record in table_name.names:
                    name_id = int(record.nameID)

                    if name_id not in {1, 2}:
                        continue

                    try:
                        name_str: str = record.toUnicode()
                    except UnicodeDecodeError as e:
                        error_text = f"Unicode decode error in font \"{file}\": {e}: '{record.toUnicode('replace')}'. Skip this {'font' if strict else 'name record'}."
                        if strict:
                            log.error(error_text, is_format=False)
                            skip_this_font = True
                            break
                        log.warning(error_text, is_format=False)
                        continue

                    match name_id:
                        case 1:  # Font Family Name
                            res_font.familys.add(name_str)

                        case 2:  # Font Subfamily Name
                            if record.langID not in {0, 1033}:
                                continue
                            for subfamily in name_str.split():
                                match subfamily.lower():
                                    case "regular" | "normal":
                                        is_regular = True
                                    case "bold":
                                        is_bold = True
                                    case "italic" | "oblique":
                                        is_italic = True

                if skip_this_font:
                    continue

                if not res_font.familys:
                    log.warning(f"Font {file} has no family names. Skip this font")
                    continue

                if is_regular:
                    if is_bold or is_italic:
                        log.error(
                            'Font "{}" is Regular but Bold={} and Italic={}. Skip this font',
                            file,
                            is_bold,
                            is_italic,
                        )
                        continue
                    res_font.font_type = Font_type.Regular

                elif is_bold or is_italic:
                    res_font.font_type = Font_type((is_bold, is_italic))

                else:
                    res_font.font_type = Font_type.Regular
                    log.warning(
                        f'Font "{file}" does not have an English subfamily name. Defaulting to Regular'
                    )

                res_font_list.append(res_font)

        except TTLibError as e:
            log.error(f'Failed to load font file "{file}": {e}')
        except Exception as e:
            log.error(f'Unexpected error when load font "{file}": {e}')

    return res_font_list


def load_windows_fonts(
    *,
    lazy: bool = True,
    strict: bool = False,
) -> list[Font]:
    paths: tuple[str, ...] = (
        os.path.join(os.environ["SYSTEMROOT"], "Fonts"),
        os.path.join(os.environ["LOCALAPPDATA"], "Microsoft/Windows/Fonts"),
    )

    return list(
        itertools.chain.from_iterable(
            load_fonts(path, lazy=lazy, strict=strict) for path in paths
        )
    )


def subset_font(font: Font, subset_str: str, affix: str) -> tuple[TTFont, bool]:
    subset_font = deepcopy(font.font)

    # 检查哪些字符不存在于字体中
    try:
        cmap = subset_font.getBestCmap()
        if cmap is None:
            raise Exception("cmap is None")
        available_chars = set(map(chr, cmap))
    except Exception as e:
        raise Font_error("Can not read best cmap from '{}'", font.pathname) from e
    input_chars = set(subset_str)
    missing_chars = input_chars - available_chars

    if missing_chars:
        # 将缺失字符按 Unicode 码点排序
        sorted_missing = sorted(missing_chars, key=lambda c: ord(c))
        missing_info = ", ".join(f"'{c}' (U+{ord(c):04X})" for c in sorted_missing)
        log.warning(
            'The font "{}" does not contain these characters: {}',
            f"{font.familys} / {font.font_type.name}",
            missing_info,
        )

    # 创建子集化选项
    options = subset.Options()
    options.hinting = True  # 保留 hinting
    options.name_IDs = []  # 不保留 name 表记录

    # 创建子集化器
    subsetter = subset.Subsetter(options=options)

    # 设置要保留的字符
    subsetter.populate(text=subset_str)

    # 执行子集化
    subsetter.subset(subset_font)

    # 修改 Name Record
    affix_ascii = affix.encode("ascii")
    affix_utf16be = affix.encode("utf-16-be")
    table_name: table__n_a_m_e | None = font.font.get("name")
    subset_table_name: table__n_a_m_e | None = subset_font.get("name")

    # 这两个都是复制的，所以不可能是 None
    assert table_name is not None
    assert subset_table_name is not None

    subset_table_name.names = list[NameRecord]()  # 重写 name table
    for record in table_name.names:
        name_id = int(record.nameID)

        if name_id not in {0, 1, 2, 3, 4, 5, 6}:
            continue

        _prefix = affix_utf16be if record.getEncoding() == "utf_16_be" else affix_ascii
        match name_id:
            case 1 | 3 | 4 | 6:
                record.string = _prefix + record.string
            case 5:
                record.string += _prefix

        subset_table_name.names.append(
            makeName(
                record.string,
                record.nameID,
                record.platformID,
                record.platEncID,
                record.langID,
            )
        )

    subset_font.close()
    return subset_font, not missing_chars
