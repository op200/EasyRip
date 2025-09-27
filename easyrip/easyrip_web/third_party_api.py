import urllib.request
import urllib.parse
import json


class zhconvert:
    """繁化姬 API"""

    @classmethod
    def translate(
        cls,
        org_text: str,
        target_lang: str,
    ) -> str:
        """
        target_lang (str):
            * Simplified  簡體化
            * Traditional  繁體化
            * China  中國化
            * Hongkong  香港化
            * Taiwan  台灣化
            * Pinyin  拼音化
            * Bopomofo  注音化
            * Mars  火星化
            * WikiSimplified  維基簡體化
            * WikiTraditional  維基繁體化
        """

        from ..easyrip_mlang import gettext
        from ..easyrip_log import log

        if target_lang not in {
            "Simplified",  # 簡體化
            "Traditional",  # 繁體化
            "China",  # 中國化
            "Hongkong",  # 香港化
            "Taiwan",  # 台灣化
            "Pinyin",  # 拼音化
            "Bopomofo",  # 注音化
            "Mars",  # 火星化
            "WikiSimplified",  # 維基簡體化
            "WikiTraditional",  # 維基繁體化
        }:
            raise Exception(
                gettext("Language not supported by {}: {}").format(
                    cls.__name__, target_lang
                )
            )

        log.info(
            gettext(
                "Translating into '{target_lang}' using '{api_name}'",
                is_format=False,
            ).format(target_lang=target_lang, api_name=cls.__name__),
            is_format=False,
        )

        req = urllib.request.Request(
            url="https://api.zhconvert.org/convert",
            data=urllib.parse.urlencode(
                {"text": org_text, "converter": target_lang}
            ).encode("utf-8"),
        )

        with urllib.request.urlopen(req) as response:
            for _ in range(5):  # 尝试重连
                if response.getcode() != 200:
                    continue

                res = json.loads(response.read().decode("utf-8"))

                res_data: dict = res.get("data", {})

                text = res_data.get("text")
                if not isinstance(text, str):
                    raise Exception("The 'text' in response is not a 'str'")
                return text

            else:
                raise Exception(f"HTTP error: {response.getcode()}")
