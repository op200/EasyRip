import json
import os
import re
import shutil
import subprocess
import unittest

import easyrip
from easyrip import gettext, log, run_command


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
            easyrip.check_ver("2.9.4+4", easyrip.Global_val.PROJECT_VERSION)
        )

    def test_log(self):
        self.assertEqual(gettext(""), "")
        self.assertEqual(gettext("{}"), "{}")
        gettext(easyrip.Global_lang_val.Extra_text_index.HELP_DOC, is_format=False)

        html_log_file = log.html_filename
        easyrip.init(True)
        self.assertEqual(log.html_filename, gettext(html_log_file))

        log.send("", "msg")
        log.send("", "{}, {}", 1, 2)
        log.info("info")
        log.warning("warning")
        log.error("error {}")
        log.info("info {}", "deep", deep=True)

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
    test_va_basename = "testVideo1080p23.98"
    test_va_suffix = "mkv"
    test_video_output_basename = "testVideoOutput"
    test_audio_output_basename = "testAudioOutput"

    @staticmethod
    def restore():
        if os.path.exists(f"{TestRip.test_video_output_basename}.rip.mp4"):
            os.remove(f"{TestRip.test_video_output_basename}.rip.mp4")

        if os.path.exists(f"{TestRip.test_audio_output_basename}.flac"):
            os.remove(f"{TestRip.test_audio_output_basename}.flac")

        run_command("list clear")

    def setUp(self):
        TestRip.restore()

        self.assertTrue(
            os.path.exists(f"{TestRip.test_va_basename}.{TestRip.test_va_suffix}")
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

    def tearDown(self):
        TestRip.restore()

    def test_x265(self):
        run = run_command

        self.assertTrue(
            run(
                f"-i {TestRip.test_va_basename}.{TestRip.test_va_suffix} -t 0.1 -preset x265slow -hme 0 -r auto -o {TestRip.test_video_output_basename} -muxer mp4 -run"
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
                    f"{TestRip.test_video_output_basename}.v.mp4",
                ],
                stdout=subprocess.PIPE,
                text=True,
                encoding="utf-8",
            ).communicate()[0]
        )
        _info_list: list = _info.get("streams", [])

        _video_info_dict: dict = _info_list[0] if _info_list else dict()

        _fps_str: str = _video_info_dict.get("r_frame_rate", "0") + "/1"
        _fps = [int(s) for s in _fps_str.split("/")]
        r_frame_rate = (_fps[0], _fps[1])

        nb_frames = int(_video_info_dict.get("nb_frames", 0))
        duration = float(_video_info_dict.get("duration", 0))

        log.send(
            "", f"fps: {r_frame_rate}, nb_frames: {nb_frames}, duration: {duration}"
        )

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

        x265_options_dict: dict[str, str | None] = dict()

        for s in x265_options_str.split(" "):
            option = s.split("=")
            x265_options_dict[option[0]] = option[1] if len(option) == 2 else None

        log.send(
            "",
            f"x265 options: \n{json.dumps(x265_options_dict, indent=3)}",
            is_format=False,
        )

        self.assertTrue("no-hme" in x265_options_dict)

    def test_flac(self):
        run = run_command

        self.assertTrue(
            run(
                f"-i {TestRip.test_va_basename}.{TestRip.test_va_suffix} -preset flac -o {TestRip.test_audio_output_basename} -run"
            )
        )
