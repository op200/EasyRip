import enum
import json
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree
from time import sleep


class zhconvert:
    """繁化姬 API"""

    class Target_lang(enum.Enum):
        Hans = Simplified = "Simplified"  # 簡體化
        Hant = Traditional = "Traditional"  # 繁體化
        CN = China = "China"  # 中國化
        HK = Hongkong = "Hongkong"  # 香港化
        TW = Taiwan = "Taiwan"  # 台灣化
        Pinyin = "Pinyin"  # 拼音化
        Bopomofo = "Bopomofo"  # 注音化
        Mars = "Mars"  # 火星化
        WikiSimplified = "WikiSimplified"  # 維基簡體化
        WikiTraditional = "WikiTraditional"  # 維基繁體化

    @classmethod
    def translate(
        cls,
        org_text: str,
        target_lang: Target_lang,
    ) -> str:
        """失败抛出异常"""
        from ..easyrip_log import log

        log.info(
            "Translating into '{target_lang}' using '{api_name}'",
            target_lang=target_lang.value,
            api_name=cls.__name__,
        )

        req = urllib.request.Request(
            url="https://api.zhconvert.org/convert",
            data=urllib.parse.urlencode(
                {"text": org_text, "converter": target_lang.value}
            ).encode("utf-8"),
        )

        for retry_num in range(5):
            try:
                with urllib.request.urlopen(req) as response:
                    for _ in range(5):  # 尝试重连
                        if response.getcode() != 200:
                            log.debug("response.getcode() != 200")
                            continue

                        res = json.loads(response.read().decode("utf-8"))

                        res_data: dict = res.get("data", {})

                        text = res_data.get("text")
                        if not isinstance(text, str):
                            raise TypeError("The 'text' in response is not a 'str'")
                        return text

                    raise Exception(f"HTTP error: {response.getcode()}")
            except urllib.error.HTTPError:
                sleep(0.5)
                if retry_num == 4:
                    raise
                log.debug("Attempt to reconnect")
                continue

        raise Exception


class github:
    @classmethod
    def get_latest_release_ver(cls, release_api_url: str) -> str | None:
        """失败返回 None"""
        from ..easyrip_log import log

        req = urllib.request.Request(release_api_url)

        try:
            with urllib.request.urlopen(req) as response:
                data: dict = json.loads(response.read().decode("utf-8"))
                ver = data.get("tag_name")
                if ver is None:
                    return None
                if isinstance(ver, str):
                    return ver.lstrip("v")
                raise ValueError(f"ver = {ver!r}")
        except Exception as e:
            log.debug(
                "'{}' execution failed: {}",
                f"{cls.__name__}.{cls.get_latest_release_ver.__name__}",
                e,
                print_level=log.LogLevel._detail,
            )

        return None


class mkvtoolnix:
    __latest_release_ver_cache: str | None = None

    @classmethod
    def get_latest_release_ver(cls, *, flush_cache: bool = False) -> str | None:
        """失败返回 None"""
        if flush_cache is False and cls.__latest_release_ver_cache is not None:
            return cls.__latest_release_ver_cache

        from ..easyrip_log import log

        req = urllib.request.Request("https://mkvtoolnix.download/latest-release.xml")

        try:
            with urllib.request.urlopen(req) as response:
                xml_tree = xml.etree.ElementTree.XML(response.read().decode("utf-8"))
                if (ver := xml_tree.find("latest-source/version")) is None:
                    log.debug(
                        "'{}' execution failed: {}",
                        f"{cls.__name__}.{cls.get_latest_release_ver.__name__}",
                        f"XML parse faild: {xml.etree.ElementTree.tostring(xml_tree)}",
                        print_level=log.LogLevel._detail,
                    )
                    return None
                cls.__latest_release_ver_cache = ver.text
                return ver.text
        except Exception as e:
            log.debug(
                "'{}' execution failed: {}",
                f"{cls.__name__}.{cls.get_latest_release_ver.__name__}",
                e,
                print_level=log.LogLevel._detail,
            )

        return None
