import io
import itertools
import json
import os
import re
import shutil
import subprocess
import sys
import timeit
import unittest
from pathlib import Path
from typing import Final

import easyrip
import easyrip.easyrip_web
from easyrip import (
    Ass,
    Lang_tag,
    gettext,
    log,
    run_command,
)
from easyrip.easyrip_command import Cmd_type, Opt_type
from easyrip.easyrip_mlang import Lang_tag_val, all_supported_lang_map
from easyrip.easyrip_mlang.global_lang_val import Global_lang_val
from easyrip.ripper.ripper import Ripper
from easyrip.ripper.sub_and_font.font import load_fonts, load_windows_fonts

if sys.stdout.encoding != "UTF-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

log.print_level = log.LogLevel._detail
log.write_level = log.LogLevel.none


def run_command_and_run_ripper_list(cmd: str) -> bool:
    def __run(cmd: str) -> bool:
        if not (run_command(cmd)):
            log.error("Run command failed: {}", cmd)
            return False

        for ripper in Ripper.ripper_list:
            if not ripper.run():
                log.error("Run ripper failed: {}", ripper)
                return False

        return True

    res = __run(cmd)
    Ripper.ripper_list.clear()
    return res


class TestBasic(unittest.TestCase):
    def test_init(self):
        easyrip.init(True)
        easyrip.init()
        easyrip.check_env()

    def test_version(self):
        self.assertTrue(easyrip.check_ver("1.2.3.1", "1.2.3"))
        self.assertFalse(easyrip.check_ver("1.2.3", "1.2.3.1"))
        self.assertTrue(easyrip.check_ver("1.2.3.1", "1.2.3.0"))
        self.assertFalse(easyrip.check_ver("1.2.3.0", "1.2.3.1"))

        self.assertTrue(easyrip.check_ver("1.3.3", "1.2.3"))
        self.assertFalse(easyrip.check_ver("1.2.3", "1.2.3"))
        self.assertFalse(easyrip.check_ver("1.2.3+1", "1.2.3+2"))
        self.assertFalse(easyrip.check_ver("1.2.3+2", "1.2.3+2"))
        self.assertFalse(easyrip.check_ver("1.2.3+0", "1.2.3"))
        self.assertFalse(easyrip.check_ver("1.2.3", "1.2.3+0"))
        self.assertFalse(easyrip.check_ver("1.2", "1.2.0"))
        self.assertFalse(easyrip.check_ver("1.2", "1.2.1"))
        self.assertFalse(easyrip.check_ver("1.2+2", "1.2.1"))
        self.assertFalse(
            easyrip.check_ver("2.9.4+4", easyrip.global_val.PROJECT_VERSION)
        )

    def test_log(self):
        self.assertEqual(gettext(""), "")
        self.assertEqual(gettext("{}"), "{}")

        html_log_file = log.html_filename
        easyrip.init(True)
        self.assertEqual(log.html_filename, gettext(html_log_file))

        # the *val format
        log.send("msg")
        log.send("{}, {}", 1, 2)
        log.info("info")
        log.warning("warning")
        log.error("error {}")
        log.info("info {}", "deep", deep=True)

        # the **kw format
        log.send("{a} - {b} - {a}", a=111, b=222)
        log.send("{a} - {b} - {c}", a=1, b=2)

        # auto close format
        log.debug("{}")
        log.debug("{{}{}}")
        log.debug("{{}}")
        log.debug("{'a': <A.a: 1>, 'b': <A.b: 1>}")

    def test_cmd_doc_gettext_format(self):
        for lang_tag in all_supported_lang_map:
            Global_lang_val.gettext_target_lang = lang_tag

            for v in itertools.chain(
                ("",),
                Cmd_type._member_names_,
                Opt_type._member_names_,
            ):
                run_command(["help", v])

                self.assertEqual(log.debug_num, 0)

    def test_run_cmd(self):
        easyrip.init(True)

        run = run_command

        run("log cmd log info")
        run("log err cmd log error")

        run("config list")

        run("-i inputVideo -o outputName")
        run("-i inputVideo -o outputName -preset flac")
        run("-i inputVideo -preset x264slow -crf 12")
        run("-i inputVideo -preset x265slow -hme 0")
        run("-i inputVideo -preset x265fast4 -x265-params hme=0")
        run("list")


class TestRip(unittest.TestCase):
    TEST_VA_BASENAME: Final = "testVideo1080p23.98"
    TEST_VA_SUFFIX: Final = "mkv"
    test_media_file_dict: Final[dict[str, list[Path]]] = {}
    """每个函数名对应一个文件 list"""

    @classmethod
    def restore(cls):
        for path in itertools.chain.from_iterable(cls.test_media_file_dict.values()):
            for suffix in (
                ".v.mp4",
                ".va.mp4",
                ".v.mkv",
                ".va.mkv",
                ".flac",
            ):
                output_path = path.with_suffix(path.suffix + suffix)
                output_path.unlink(True)

        run_command("list clear")

    @classmethod
    def setUpClass(cls):
        for method in (
            cls.test_x265,
            cls.test_flac,
            cls.test_c_a_flac,
            cls.test_soft_sub,
        ):
            method_name = method.__name__
            cls.test_media_file_dict[method_name] = [
                Path(f"{cls.TEST_VA_BASENAME}_{method_name}")
            ]

        cls.restore()

    @classmethod
    def tearDownClass(cls):
        cls.restore()

    def setUp(self):
        self.assertTrue(
            os.path.exists(f"{TestRip.TEST_VA_BASENAME}.{TestRip.TEST_VA_SUFFIX}")
        )

        for tool in (
            "ffmpeg",
            "ffprobe",
            "flac",
            "mp4fpsmod",
            "mp4box",
            "mkvpropedit",
            "mkvmerge",
        ):
            self.assertTrue(shutil.which(tool), f"The '{tool}' not found in PATH")

        easyrip.init(True)

    def test_x265(self):
        """测试 hme 关闭，以及其他标准传参"""
        output_basename = TestRip.test_media_file_dict[self.test_x265.__name__][0]

        crf = "22.2"
        qpmin = "3"
        qpmax = "33"
        params: str = f"-hme 0 -crf {crf} -x265-params qpmin={qpmin}:qpmax={qpmax}::"
        self.assertTrue(
            run_command_and_run_ripper_list(
                f"-i {TestRip.TEST_VA_BASENAME}.{TestRip.TEST_VA_SUFFIX} -t 0.1 -preset x265slow {params} -r auto -o {output_basename} -muxer mp4 -quality-detection ssim"
            )
        )

        _info: dict = json.loads(
            subprocess.Popen(
                [
                    "ffprobe",
                    "-v",
                    "31",
                    "-select_streams",
                    "v:0",
                    "-show_streams",
                    "-show_data",
                    "-print_format",
                    "json",
                    f"{output_basename}.v.mp4",
                ],
                stdout=subprocess.PIPE,
                text=True,
                encoding="utf-8",
            ).communicate()[0]
        )
        _info_list: list = _info.get("streams", [])

        _video_info_dict: dict = _info_list[0] if _info_list else {}

        _fps_str: str = _video_info_dict.get("r_frame_rate", "0") + "/1"
        _fps = [int(s) for s in _fps_str.split("/")]
        r_frame_rate = (_fps[0], _fps[1])

        nb_frames = int(_video_info_dict.get("nb_frames", 0))
        duration = float(_video_info_dict.get("duration", 0))

        log.send(f"fps: {r_frame_rate}, nb_frames: {nb_frames}, duration: {duration}")

        self.assertEqual(r_frame_rate[0], 24000)
        self.assertEqual(r_frame_rate[1], 1001)
        self.assertGreater(nb_frames, 0)
        self.assertGreater(duration, 0)

        extradata: str = _video_info_dict.get("extradata", "")

        extradata_list: list[bytes] = [
            bytes.fromhex(c)
            for line in extradata.split("\n")
            if line
            for c in line.split(":")[1].strip().split(" ")[:8]
            if c
        ]

        extradata_str: str = "".join(
            b.decode("utf-8", errors="replace") for b in extradata_list
        )

        if _match := re.search(r"options: (.+no-frame-rc)", extradata_str):
            x265_options_str = str(_match.group(1))
        else:
            self.fail("x265 options not found")

        x265_options_dict: dict[str, str | None] = {}

        for s in x265_options_str.split(" "):
            option = s.split("=")
            x265_options_dict[option[0]] = option[1] if len(option) == 2 else None

        log.send(
            f"x265 options: \n{json.dumps(x265_options_dict, indent=3)}",
            is_format=False,
        )

        self.assertTrue("no-hme" in x265_options_dict)
        self.assertEqual(crf, x265_options_dict["crf"])
        self.assertEqual(qpmin, x265_options_dict["qpmin"])
        self.assertEqual(qpmax, x265_options_dict["qpmax"])

    def test_flac(self):
        output_basename = TestRip.test_media_file_dict[self.test_flac.__name__][0]

        self.assertTrue(
            run_command_and_run_ripper_list(
                f"-i {TestRip.TEST_VA_BASENAME}.{TestRip.TEST_VA_SUFFIX} -preset flac -o {output_basename}"
            )
        )

    def test_c_a_flac(self):
        output_basename = TestRip.test_media_file_dict[self.test_c_a_flac.__name__][0]

        self.assertTrue(
            run_command_and_run_ripper_list(
                f"-i {TestRip.TEST_VA_BASENAME}.{TestRip.TEST_VA_SUFFIX} -p copy -c:a flac -o {output_basename}"
            )
        )

    def test_soft_sub(self):
        output_basename = TestRip.test_media_file_dict[self.test_soft_sub.__name__][0]

        ass_file_list: list[Path] = [
            Path(f"{TestRip.TEST_VA_BASENAME}.{infix}.ass")
            for infix in (
                "zh-Hans",
                "zh-Hant",
            )
        ]

        for ass in ass_file_list:
            self.assertTrue(ass.is_file(), f"Can not find ASS file {ass}")

        self.assertTrue(
            run_command_and_run_ripper_list(
                f"-i {TestRip.TEST_VA_BASENAME}.{TestRip.TEST_VA_SUFFIX} -p copy -c:a libopus -soft-sub auto -o {output_basename}"
            )
        )


class TestSubset(unittest.TestCase):
    def test_ass_class(self):
        TEST_ASS_NUMBER = 100
        log.info(
            f"Test ASS class {TEST_ASS_NUMBER} times: {
                timeit.timeit(
                    lambda: Ass('test.zh-Hans.ass').__str__(
                        drop_non_render=True,
                        drop_unkow_data=True,
                        drop_fonts=False,
                        drop_graphics=False,
                    ),
                    number=TEST_ASS_NUMBER,
                ):.4f}sec"
        )

    def test_load_font(self):
        self.assertFalse(load_fonts(":&?"))
        self.assertTrue(load_windows_fonts())


class TestThirdPartyApi(unittest.TestCase):
    def test_mkvtoolnix_api(self):
        ver = easyrip.easyrip_web.mkvtoolnix.get_latest_release_ver()
        self.assertIsNotNone(ver)


class TestLanguage(unittest.TestCase):
    def test_str_to_lang_tag(self):
        self.assertIs(Lang_tag.from_str("").language, Lang_tag.Language.Unknown)
        self.assertIs(Lang_tag.from_str("-").language, Lang_tag.Language.Unknown)
        self.assertIs(Lang_tag.from_str("---").language, Lang_tag.Language.Unknown)
        self.assertIs(Lang_tag.from_str("-2-3-").language, Lang_tag.Language.Unknown)

        self.assertEqual(
            Lang_tag.from_str("zh"),
            Lang_tag(
                language=Lang_tag.Language.zh,
                script=Lang_tag.Script.Unknown,
                region=Lang_tag.Region.Unknown,
            ),
        )
        self.assertEqual(
            Lang_tag.from_str("chi"),
            Lang_tag(
                language=Lang_tag.Language.zh,
                script=Lang_tag.Script.Unknown,
                region=Lang_tag.Region.Unknown,
            ),
        )
        self.assertEqual(
            Lang_tag.from_str("zho"),
            Lang_tag(
                language=Lang_tag.Language.zh,
                script=Lang_tag.Script.Unknown,
                region=Lang_tag.Region.Unknown,
            ),
        )
        self.assertEqual(
            Lang_tag.from_str("zh-Hans-CN"),
            Lang_tag(
                language=Lang_tag.Language.zh,
                script=Lang_tag.Script.Hans,
                region=Lang_tag.Region.CN,
            ),
        )

    def test_lang_tag_val(self):
        self.assertIsNotNone(Lang_tag_val.__eq__)
        self.assertIsNotNone(Lang_tag_val.__hash__)
        self.assertEqual(
            {
                Lang_tag_val(en_name="1"),
                Lang_tag_val(en_name="2"),
                Lang_tag_val(en_name="1"),
                Lang_tag_val(en_name="2", local_name="3"),
            }.__len__(),
            2,
        )

    def test_lang_val_to_lang_tag(self):
        self.assertIs(
            Lang_tag.Language.zh,
            Lang_tag.Language(Lang_tag_val(en_name="Chinese")),
        )
