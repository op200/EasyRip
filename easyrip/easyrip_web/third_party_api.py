import enum
import json
import urllib.error
import urllib.parse
import urllib.request
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
        from ..easyrip_log import log
        from ..easyrip_mlang import gettext

        log.info(
            gettext(
                "Translating into '{target_lang}' using '{api_name}'",
                is_format=False,
            ).format(target_lang=target_lang.value, api_name=cls.__name__),
            is_format=False,
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
            except urllib.error.HTTPError as e:
                sleep(0.5)
                if retry_num == 4:
                    raise e
                log.debug("Attempt to reconnect")
                continue

        raise Exception


class github:
    @staticmethod
    def get_release_ver(release_api_url: str) -> str | None:
        req = urllib.request.Request(release_api_url)

        try:
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode("utf-8"))
                return data.get("tag_name")
        except Exception:
            pass

        return None
