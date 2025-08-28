from copy import deepcopy
from dataclasses import dataclass, field
import enum
from pathlib import Path
import os
import winreg

from fontTools.ttLib import TTFont, TTCollection
from fontTools.ttLib.ttFont import TTLibError
from fontTools.ttLib.tables._n_a_m_e import table__n_a_m_e, NameRecord, makeName
from fontTools import subset

from ...easyrip_log import log


class Font_type(enum.Enum):
    Regular = (False, False)
    Bold = (True, False)
    Italic = (False, True)
    Bold_Italic = (True, True)


@dataclass
class Font:
    pathname: str
    font: TTFont
    familys: list[str] = field(default_factory=list)
    font_type: Font_type = Font_type.Regular

    def __hash__(self) -> int:
        return hash(self.pathname)


def load_fonts(path: str | Path, lazy: bool = True) -> list[Font]:
    if isinstance(path, str):
        path = Path(path)

    res_font_list: list[Font] = []

    for file in path.iterdir() if path.is_dir() else (path,):
        if not (
            file.is_file()
            and ((suffix := file.suffix.lower()) in {".ttf", ".otf", ".ttc"})
        ):
            continue

        try:
            if suffix == ".ttc":
                fonts: list[TTFont] = [
                    font for font in TTCollection(file=file, lazy=lazy)
                ]
            else:
                fonts = [TTFont(file=file, lazy=lazy)]

            for font in fonts:
                table_name: table__n_a_m_e = font.get("name")  # type: ignore

                if table_name is None:
                    log.warning(f"No 'name' table found in font {file}")
                    continue

                res_font = Font(str(file), font)
                is_regular: bool = False
                is_bold: bool = False
                is_italic: bool = False

                for record in table_name.names:
                    record: NameRecord = record
                    name_id = int(record.nameID)

                    if name_id not in {1, 2}:
                        continue

                    name_str: str = record.toUnicode()
                    if not isinstance(name_str, str):
                        log.warning(
                            f"Unexpected type for name string in font {file}: {type(name_str)}"
                        )
                        continue
                    else:
                        name_str = str(name_str)

                    match name_id:
                        case 1:  # Font Family Name
                            res_font.familys.append(name_str)

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

                if not res_font.familys:
                    log.warning(f"Font {file} has no family names. Skip this font")
                    continue

                if is_regular:
                    if is_bold or is_italic:
                        log.error(
                            "Font {} is Regular but Bold={} and Italic={}. Skip this font",
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
                        f"Font {file} does not have an English subfamily name. Defaulting to Regular"
                    )

                res_font_list.append(res_font)

        except TTLibError as e:
            log.warning(f'Error loading font file "{file}": {e}')
        except UnicodeDecodeError as e:
            log.warning(f"Unicode decode error for font {file}: {e}")
        except Exception as e:
            log.error(f"Unexpected error for font {file}: {e}")

    return res_font_list


def get_font_path_from_registry(font_name) -> list[str]:
    """
    通过Windows注册表获取字体文件路径
    :param font_name: 字体名称（如"Arial"）
    :return: 字体文件完整路径，如果找不到返回None
    """
    res: list[str] = []
    try:
        # 打开字体注册表键
        with winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts",
        ) as key:
            i = 0
            while True:
                try:
                    # 枚举所有字体值
                    value_name, value_data, _ = winreg.EnumValue(key, i)
                    i += 1

                    # 检查字体名称是否匹配（去掉可能的"(TrueType)"等后缀）
                    if value_name.startswith(font_name):
                        # 获取字体文件路径
                        fonts_dir = os.path.join(os.environ["SystemRoot"], "Fonts")
                        font_path = os.path.join(fonts_dir, value_data)

                        # 检查文件是否存在
                        if os.path.isfile(font_path):
                            res.append(font_path)
                except OSError:
                    # 没有更多条目时退出循环
                    break
    except Exception as e:
        log.warning("Error accessing registry: {}", e)

    return res


def subset_font(font: Font, subset_str: str, afffix: str) -> tuple[TTFont, bool]:
    subset_font = deepcopy(font.font)

    # 检查哪些字符不存在于字体中
    cmap = subset_font.getBestCmap()
    available_chars = set(chr(key) for key in cmap.keys())
    input_chars = set(subset_str)
    missing_chars = input_chars - available_chars

    if missing_chars:
        # 将缺失字符按Unicode码点排序
        sorted_missing = sorted(missing_chars, key=lambda c: ord(c))
        missing_info = ", ".join(f"'{c}' (U+{ord(c):04X})" for c in sorted_missing)
        log.warning(
            'The font "{}" does not contain these characters: {}',
            f"{font.familys} / {font.font_type.name}",
            missing_info,
        )

    # 创建子集化选项
    options = subset.Options()
    options.drop_tables = ["DSIG", "PCLT", "EBDT", "EBSC"]  # 不移除任何可能有用的表
    options.hinting = True  # 保留 hinting
    options.name_IDs = []  # 不保留 name 表记录
    options.no_subset_tables = subset.Options._no_subset_tables_default + [
        "BASE",
        "mort",
    ]
    # options.drop_tables = []
    options.name_legacy = True
    # options.retain_gids = True
    options.layout_features = ["*"]

    # 创建子集化器
    subsetter = subset.Subsetter(options=options)

    # 设置要保留的字符
    subsetter.populate(text=subset_str)

    # 执行子集化
    subsetter.subset(subset_font)

    # 修改 Name Record
    affix_ascii = afffix.encode("ascii")
    affix_utf16be = afffix.encode("utf-16-be")
    table_name: table__n_a_m_e = font.font.get("name")  # type: ignore
    subset_table_name: table__n_a_m_e = subset_font.get("name")  # type: ignore
    subset_table_name.names = []  # 重写 name table
    for record in table_name.names:
        record: NameRecord = record
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

    return subset_font, not missing_chars
