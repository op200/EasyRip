"""Self-contained regression tests that do not rely on repository media assets."""

import shutil
import subprocess
import tempfile
import unittest
from collections import UserDict, UserList
from collections.abc import Mapping, Sequence
from io import StringIO
from pathlib import Path
from typing import Annotated, Final, Literal, NotRequired, Self, TypedDict
from unittest.mock import patch

from prompt_toolkit.completion import CompleteEvent
from prompt_toolkit.document import Document

from easyrip.easyrip_command import Cmd_type, Opt_type, get_help_doc
from easyrip.easyrip_config.config import config
from easyrip.easyrip_log import Log, log
from easyrip.easyrip_main import get_web_server_params, run_command
from easyrip.easyrip_mlang import Global_lang_val, Lang_tag, gettext
from easyrip.easyrip_mlang.lang_tag_val import Lang_tag_val
from easyrip.easyrip_mlang.translator import translate_subtitles
from easyrip.easyrip_prompt import (
    CustomPromptLexer,
    SmartPathCompleter,
    easyrip_prompt,
    fuzzy_filter_and_sort,
    highlight_fuzzy_match,
)
from easyrip.easyrip_web import http_server, third_party_api
from easyrip.easyrip_web.http_server import MainHTTPRequestHandler
from easyrip.ripper.media_info import Media_info, Stream_error
from easyrip.ripper.param import Audio_codec, Muxer, Preset_name
from easyrip.ripper.ripper import Ripper
from easyrip.ripper.sub_and_font import Ass
from easyrip.ripper.sub_and_font.ass import (
    Ass_generate_error,
    Ass_time,
    Attach_type,
    Attachment_data,
    Attachments,
    Event_data,
)
from easyrip.ripper.sub_and_font.subset import subset
from easyrip.utils import (
    AES,
    check_ver,
    int_to_base62,
    non_ascii_str_len,
    obj_fmt,
    read_text,
    shlex_split,
    time_str_to_sec,
    type_match,
    uudecode_ssa,
    uuencode_ssa,
)

ASS_CONTENT: Final = """[Script Info]
Title: Generated test subtitle

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,32,&H00FFFFFF,&H000000FF,&H00000000,&H64000000,0,0,0,0,100,100,0,0,1,2,0,2,20,20,20,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Comment: 0,0:00:00.00,0:00:00.20,Default,,0,0,0,,Ignored comment
Dialogue: 0,0:00:00.00,0:00:00.20,Default,,0,0,0,,Hello {\\b1}world{\\b0}\\Nsecond line

[Custom Data]
value: retained unless requested otherwise
"""


class SelfContainedTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._temp_dir = tempfile.TemporaryDirectory(prefix="easyrip-test-")
        self.work_dir = Path(self._temp_dir.name)
        Ripper.ripper_list.clear()
        log.print_level = log.LogLevel.none
        log.write_level = log.LogLevel.none

    def tearDown(self) -> None:
        Ripper.ripper_list.clear()
        self._temp_dir.cleanup()

    def write_ass(self, name: str = "generated.zh-Hans.ass") -> Path:
        path = self.work_dir / name
        path.write_text(ASS_CONTENT, encoding="utf-8-sig", newline="\n")
        return path

    def create_media(self, name: str = "generated.mkv") -> Path:
        ffmpeg = shutil.which("ffmpeg")
        if ffmpeg is None:
            self.skipTest("ffmpeg is not available on PATH")

        path = self.work_dir / name
        subprocess.run(
            [
                ffmpeg,
                "-hide_banner",
                "-loglevel",
                "error",
                "-f",
                "lavfi",
                "-i",
                "testsrc2=size=64x48:rate=12",
                "-f",
                "lavfi",
                "-i",
                "sine=frequency=1000:sample_rate=48000",
                "-t",
                "0.25",
                "-c:v",
                "ffv1",
                "-c:a",
                "pcm_s16le",
                "-shortest",
                "-y",
                path,
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        return path


class TestGeneratedSubtitle(SelfContainedTestCase):
    def test_ass_round_trip_and_font_analysis(self) -> None:
        ass = Ass(self.write_ass())

        self.assertEqual(len(ass.styles.data), 1)
        self.assertEqual(len(ass.events.data), 2)
        self.assertIn("Custom Data", str(ass))
        self.assertNotIn("Ignored comment", ass.__str__(drop_non_render=True))
        self.assertNotIn("Custom Data", ass.__str__(drop_unkow_data=True))

        font_info = ass.get_font_info()
        self.assertEqual({font_name for font_name, _ in font_info}, {"Arial"})
        all_characters = set().union(*font_info.values())
        self.assertTrue({"H", "w", "s"}.issubset(all_characters))

    def test_event_tag_parser_modes(self) -> None:
        text = r"plain\{escaped{\b1}tag"

        self.assertEqual(
            Event_data.parse_text(text, use_libass_spec=True),
            [(False, r"plain\{escaped"), (True, r"{\b1}"), (False, "tag")],
        )
        self.assertEqual(
            Event_data.parse_text(text, use_libass_spec=False),
            [(False, "plain\\"), (True, r"{escaped{\b1}"), (False, "tag")],
        )

    def test_ass_rejects_missing_or_invalid_files(self) -> None:
        with self.assertRaises(Ass_generate_error):
            Ass(self.work_dir / "missing.ass")

        invalid_ass = self.work_dir / "invalid.ass"
        invalid_ass.write_text("[Events]\nFormat: Layer\n", encoding="utf-8")
        with self.assertRaises(Ass_generate_error):
            Ass(invalid_ass)

    def test_subset_writes_subtitle_when_fonts_are_unavailable(self) -> None:
        source = self.write_ass()
        output_dir = self.work_dir / "subset"

        self.assertFalse(subset([source], [], output_dir, strict=False))
        output = output_dir / source.name
        self.assertTrue(output.is_file())
        self.assertIn("Font Subset Info", read_text(output))

    def test_attachment_sections_and_cached_data_conversion(self) -> None:
        attachments = Attachments(
            data=[
                Attachment_data(
                    type=Attach_type.Fonts, name="font.ttf", org_data=b"123456"
                ),
                Attachment_data(
                    type=Attach_type.Graphics, name="image.bin", org_data=b"abcdef"
                ),
            ]
        )
        rendered = attachments.to_ass_str()
        self.assertIn("[Fonts]", rendered)
        self.assertIn("[Graphics]", rendered)
        self.assertNotIn("font.ttf", attachments.to_ass_str(drop_fonts=True))
        self.assertNotIn("image.bin", attachments.to_ass_str(drop_graphics=True))


class TestGeneratedMedia(SelfContainedTestCase):
    def setUp(self) -> None:
        super().setUp()
        if shutil.which("ffprobe") is None:
            self.skipTest("ffprobe is not available on PATH")

    def test_media_info_from_generated_media(self) -> None:
        media = self.create_media()
        info = Media_info.from_path(media)

        self.assertEqual((info.video[0].width, info.video[0].height), (64, 48))
        self.assertEqual(info.video[0].r_frame_rate, (12, 1))
        self.assertGreater(info.video[0].duration, 0)
        self.assertEqual(len(info.audio), 1)
        self.assertEqual(info.audio[0].sample_rate, 48000)

    def test_copy_command_uses_generated_input_and_output_directory(self) -> None:
        media = self.create_media()
        output_dir = self.work_dir / "output"
        output_dir.mkdir()

        self.assertTrue(
            run_command(
                [
                    "-i",
                    str(media),
                    "-o",
                    "copied",
                    "-o:dir",
                    str(output_dir),
                    "-preset",
                    "copy",
                    "-auto-infix",
                    "0",
                ]
            )
        )
        self.assertEqual(len(Ripper.ripper_list), 1)
        self.assertTrue(Ripper.ripper_list[0].run())
        self.assertTrue((output_dir / "copied.mkv").is_file())

    def test_preset_command_construction_and_invalid_audio(self) -> None:
        media = self.create_media()
        x265 = Ripper(
            [media],
            ["x265"],
            self.work_dir,
            Preset_name.x265slow,
            {
                "muxer": "mkv",
                "r": "auto",
                "c:a": "libopus",
                "b:a": "96k",
                "x265-params": "crf=20:hme=0",
                "track-name": "['0:video', '1:audio']",
            },
        )
        self.assertIn("libx265", x265.option.encoder_format_str_list[0])
        self.assertIn("libopus", x265.option.encoder_format_str_list[0])
        self.assertIn("mkvmerge", "\n".join(x265.option.muxer_format_str_list))

        custom = Ripper(
            [media],
            ["custom"],
            self.work_dir,
            Preset_name.custom,
            {"custom:format": 'ffmpeg -i "{input}" "{output}"'},
        )
        self.assertIn("ffmpeg", custom.option.encoder_format_str_list[0])

        with self.assertRaises(ValueError):
            Ripper(
                [media],
                ["bad"],
                self.work_dir,
                Preset_name.copy,
                {"c:a": "unsupported"},
            )

        video_only = self.work_dir / "video-only.mkv"
        ffmpeg = shutil.which("ffmpeg")
        assert ffmpeg is not None
        subprocess.run(
            [
                ffmpeg,
                "-f",
                "lavfi",
                "-i",
                "color=size=16x16",
                "-t",
                "0.1",
                "-c:v",
                "ffv1",
                "-y",
                video_only,
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        with self.assertRaises(Stream_error):
            Ripper(
                [video_only],
                ["audio"],
                self.work_dir,
                Preset_name.copy,
                {"c:a": "copy"},
            )

    def test_media_info_tolerates_missing_optional_probe_fields(self) -> None:
        class Probe:
            def __init__(self, data: str) -> None:
                self.data = data

            def communicate(self) -> tuple[str, str]:
                return (self.data, "")

        video = '{"streams": [{"width": "8", "height": "6", "r_frame_rate": "24/1", "tags": {"DURATION": "00:00:01.50"}}]}'
        audio = '{"streams": [{"index": 1}]}'
        with patch(
            "easyrip.ripper.media_info.subprocess.Popen",
            side_effect=(Probe(video), Probe(audio)),
        ):
            info = Media_info.from_path("virtual.mkv")

        self.assertEqual(info.video[0].duration, 1.5)
        self.assertEqual(info.audio[0].sample_rate, 0)
        self.assertEqual(info.audio[0].sample_fmt, "")

    def test_all_safe_encoder_presets_build_commands(self) -> None:
        media = self.create_media()
        presets = (
            Preset_name.x264fast,
            Preset_name.ffv1,
            Preset_name.h264_nvenc,
            Preset_name.svtav1,
            Preset_name.vvenc,
            Preset_name.flac,
        )
        for preset in presets:
            with self.subTest(preset=preset):
                ripper = Ripper(
                    [media],
                    [preset.value],
                    self.work_dir,
                    preset,
                    {"muxer": "mkv", "c:a": "copy", "pix_fmt": "yuv420p"},
                )
                self.assertTrue(ripper.option.encoder_format_str_list)

        subset_option = Ripper(
            [self.write_ass()],
            ["subset"],
            self.work_dir,
            Preset_name.subset,
            {"muxer": "mkv"},
        )
        self.assertEqual(subset_option.option.encoder_format_str_list, [])


class TestPureUtilities(unittest.TestCase):
    def test_aes_ssa_time_and_version_helpers(self) -> None:
        plaintext = b"123456789012345678"
        key = b"0123456789abcdef"

        self.assertEqual(AES.decrypt(AES.encrypt(plaintext, key), key), plaintext)
        self.assertEqual(uudecode_ssa(uuencode_ssa(plaintext)), plaintext)
        self.assertEqual(time_str_to_sec("01:02:03.5"), 3723.5)
        self.assertTrue(check_ver("1.0.0", "1.0.0-rc.1"))
        self.assertFalse(check_ver("1.0.0-rc.1", "1.0.0"))

    def test_type_matching_formatting_and_text_encodings(self) -> None:
        class User(TypedDict):
            name: str
            age: NotRequired[int]

        self.assertTrue(type_match({"name": "Ada"}, User))
        self.assertFalse(type_match({"name": 1}, User))
        self.assertTrue(type_match([1, 2], list[int]))
        self.assertFalse(type_match([1, "2"], list[int]))
        self.assertTrue(type_match(UserList([1]), Sequence[int]))
        self.assertTrue(type_match(UserDict(answer=42), Mapping[str, int]))
        self.assertTrue(type_match("ok", Literal["ok", "no"]))
        self.assertTrue(type_match(1, Annotated[int, "metadata"]))

        self.assertEqual(int_to_base62(0), "0")
        self.assertEqual(int_to_base62(62), "10")
        self.assertEqual(non_ascii_str_len("A中"), 3)
        self.assertEqual(shlex_split('"a b" -x value'), ["a b", "-x", "value"])
        self.assertIn("answer", obj_fmt({"answer": [1, 2]}, width=12))

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            utf8_path = root / "utf8.txt"
            utf16_path = root / "utf16.txt"
            utf8_path.write_bytes(b"\xef\xbb\xbfhello")
            utf16_path.write_text("world", encoding="utf-16")
            self.assertEqual(read_text(utf8_path), "hello")
            self.assertEqual(read_text(utf16_path), "world")

    def test_ass_value_objects_and_invalid_versions(self) -> None:
        start = Ass_time.from_str("0:01:02.34")
        self.assertEqual(str(start), "00:01:02.34")
        self.assertEqual((start + Ass_time(ms=660)).total_ms(), 63_000)
        self.assertLess(Ass_time(ms=1), Ass_time(ms=2))

        attachment = Attachment_data(
            type=Attach_type.Fonts,
            name="generated.ttf",
            org_data=b"123456",
        )
        self.assertEqual(attachment.data_to_bytes(), b"123456")
        self.assertEqual(
            attachment.data_to_bytes(), uudecode_ssa(attachment.data_to_str())
        )
        attachment.set_data(b"abcdef")
        self.assertEqual(attachment.data_to_bytes(), b"abcdef")

        with self.assertRaises(ValueError):
            check_ver("not-a-version", "1.0.0")


class TestLanguageAndCommandMetadata(unittest.TestCase):
    def test_language_tags_matching_and_translation_lookup(self) -> None:
        hans_cn = Lang_tag.from_str("zh-Hans-CN")
        hant_tw = Lang_tag.from_str("zh-Hant-TW")
        self.assertEqual(str(hans_cn), "zh-Hans-CN")
        self.assertEqual(
            hans_cn.match((hant_tw, Lang_tag.from_str("zh-Hans-HK"))),
            Lang_tag.from_str("zh-Hans-HK"),
        )
        self.assertIsNone(Lang_tag.from_str("en").match((hans_cn,)))
        self.assertEqual(
            Global_lang_val.language_tag_to_local_str("zh-Hans-CN"),
            "中文-简体-中国大陆",
        )
        self.assertEqual(
            gettext({"en": "English", "zh-Hans-CN": "中文"}, lang_tag=hans_cn), "中文"
        )
        self.assertEqual(gettext("{}", "value", lang_tag=hans_cn), "value")
        self.assertEqual(
            Lang_tag_val(en_name="English"),
            Lang_tag_val(en_name="English", local_name="EN"),
        )
        with self.assertRaises(ValueError):
            Lang_tag_val(en_name="")
        self.assertIs(Lang_tag.from_str("").language, Lang_tag.Language.Unknown)

    def test_language_match_priority_and_invalid_tag_order(self) -> None:
        source = Lang_tag.from_str("zh-Hans-CN")
        by_region = Lang_tag.from_str("zh-Hant-CN")
        by_script = Lang_tag.from_str("zh-Hans-HK")
        self.assertEqual(
            source.match(
                (by_region, by_script), priority=Lang_tag.Match_priority.region
            ),
            by_region,
        )
        self.assertIsNone(source.match((by_region,), is_incomplete_match=False))
        self.assertEqual(
            Lang_tag.from_str("en").match(
                (by_region,), is_allow_mismatch_language=True
            ),
            by_region,
        )
        with self.assertRaises(ValueError):
            Lang_tag.from_str("zh-CN-Hans")

    def test_command_and_preset_metadata(self) -> None:
        self.assertIs(Cmd_type.from_str("help"), Cmd_type.help)
        self.assertIs(Opt_type.from_str("-o:dir"), Opt_type._o_dir)
        self.assertIsNone(Opt_type.from_str("-missing"))
        self.assertIn("Easy Rip Commands", get_help_doc())
        self.assertIn("x265", Preset_name.x265slow.to_help_string())
        self.assertIn("crf", Preset_name.x265slow.get_param_name_set(set()))
        self.assertIs(Audio_codec["opus"], Audio_codec.libopus)
        self.assertEqual(Muxer("unknown"), Muxer.mkv)
        self.assertEqual(
            get_web_server_params("localhost:1234@secret"),
            ("localhost", 1234, "secret"),
        )
        self.assertFalse(get_web_server_params("not-a-server"))


class TestCommandRouting(SelfContainedTestCase):
    def test_non_media_commands_and_invalid_options(self) -> None:
        with patch("easyrip.easyrip_main.os.chdir") as chdir:
            self.assertTrue(run_command(["cd", str(self.work_dir)]))
            chdir.assert_called_once_with(str(self.work_dir))

        self.assertTrue(run_command(["mkdir", str(self.work_dir / "created")]))
        self.assertTrue((self.work_dir / "created").is_dir())
        self.assertTrue(run_command(["list", "clear"]))
        self.assertFalse(run_command(["-i", "missing.mkv", "-preset", "invalid"]))
        self.assertFalse(run_command(["run", "unsupported"]))

    def test_run_and_translate_route_to_injected_dependencies(self) -> None:
        with patch("easyrip.easyrip_main.run_ripper_list") as run_rippers:
            self.assertTrue(run_command(["run", "-multithreading", "1"]))
            run_rippers.assert_called_once_with(
                is_exit_when_run_finished=False,
                shutdow_sec_str=None,
                enable_multithreading=True,
            )

        translated_path = self.work_dir / "translated.zh-Hant.ass"
        with (
            patch("easyrip.easyrip_main.Path.cwd", return_value=self.work_dir),
            patch(
                "easyrip.easyrip_main.translate_subtitles",
                return_value=[(translated_path, "translated")],
            ),
        ):
            self.assertTrue(run_command(["translate", "zh-Hans", "zh-Hant"]))
        self.assertEqual(read_text(translated_path), "translated")

    def test_help_log_and_config_routes(self) -> None:
        self.assertTrue(run_command(["help"]))
        self.assertTrue(run_command(["help", "-preset", "x265slow"]))
        self.assertTrue(run_command(["log", "warning", "message"]))
        self.assertTrue(run_command(["version"]))
        with patch.object(config, "show_config_list") as show_config:
            self.assertTrue(run_command(["config", "list"]))
            show_config.assert_called_once()
        self.assertFalse(run_command(["config", "unknown"]))

    def test_info_prompt_and_auto_subtitle_routes(self) -> None:
        ass = self.write_ass("episode.zh-Hans.ass")
        media = self.create_media("episode.mkv")
        with patch("easyrip.easyrip_main.Media_info.from_path") as media_info:
            self.assertTrue(run_command(["mediainfo", str(media)]))
            media_info.assert_called_once_with(str(media))

        self.assertTrue(
            run_command(["assinfo", str(ass), "-use-libass-spec", "0", "-show-chars-len", "1"])
        )

        prompt_custom = self.work_dir / "custom.toml"
        prompt_history = self.work_dir / "history.txt"
        prompt_history.write_text("version\n", encoding="utf-8")
        with (
            patch.object(easyrip_prompt, "PROMPT_CUSTOM_FILE", prompt_custom),
            patch.object(easyrip_prompt, "PROMPT_HISTORY_FILE", prompt_history),
            patch.object(easyrip_prompt, "_easyrip_prompt__prompt_custom_data", None),
        ):
            self.assertTrue(run_command(["prompt", "add", "quick", "version"]))
            self.assertTrue(run_command(["prompt", "show"]))
            self.assertTrue(run_command(["prompt", "history"]))
            self.assertTrue(run_command(["prompt", "history_clear"]))
            self.assertFalse(prompt_history.exists())

        with patch.object(Ripper, "add_ripper") as add_ripper:
            self.assertTrue(
                run_command(
                    [
                        "-i",
                        str(media),
                        "-o",
                        "encoded-?{start=3,padding=2}",
                        "-o:dir",
                        str(self.work_dir),
                        "-preset",
                        "x264",
                        "-sub",
                        "auto:zh-Hans",
                    ]
                )
            )
            add_ripper.assert_called_once()
            self.assertEqual(add_ripper.call_args.args[1], ["encoded-03"])


class TestLogging(SelfContainedTestCase):
    def test_log_levels_print_and_write_html(self) -> None:
        html_file = self.work_dir / "test-log.html"
        logger = Log(
            html_file=html_file,
            print_level=Log.LogLevel.debug,
            write_level=Log.LogLevel.debug,
        )
        output = StringIO()

        logger.debug("debug {}", 1, stream=output)
        logger.info("info", stream=output)
        logger.warning("warning", stream=output)
        logger.error("error", stream=output)
        logger.send("server", stream=output, is_server=True, http_send_header="test>")
        logger._do_log(
            Log.LogLevel.none,
            Log.LogMode.normal,
            "ignored",
            stream=output,
            print_level=Log.LogLevel.debug,
            write_level=Log.LogLevel.debug,
        )

        self.assertIn("[DEBUG]", output.getvalue())
        html = html_file.read_text(encoding="utf-8")
        self.assertIn("[INFO]", html)
        self.assertIn("[Send]", html)


class TestPromptAndConfig(SelfContainedTestCase):
    def test_prompt_storage_and_completion(self) -> None:
        prompt_history = self.work_dir / "history.txt"
        prompt_custom = self.work_dir / "custom.toml"
        with (
            patch.object(easyrip_prompt, "PROMPT_HISTORY_FILE", prompt_history),
            patch.object(easyrip_prompt, "PROMPT_CUSTOM_FILE", prompt_custom),
            patch.object(easyrip_prompt, "_easyrip_prompt__prompt_custom_data", None),
        ):
            self.assertTrue(easyrip_prompt.add_custom_prompt("demo", "version"))
            self.assertFalse(easyrip_prompt.add_custom_prompt("demo", "help"))
            self.assertEqual(easyrip_prompt.get_custom_prompt(), {"demo": "version"})
            self.assertTrue(easyrip_prompt.del_custom_prompt("demo"))
            self.assertFalse(easyrip_prompt.del_custom_prompt("missing"))

        (self.work_dir / "two words.txt").touch()
        (self.work_dir / "folder").mkdir()
        completions = list(
            SmartPathCompleter().get_completions(
                Document(str(self.work_dir / "two")),
                complete_event=CompleteEvent(),
            )
        )
        self.assertEqual(len(completions), 1)
        self.assertIn("two words.txt", completions[0].text)
        self.assertEqual(
            fuzzy_filter_and_sort(["beta", "alpha"], ""), ["alpha", "beta"]
        )
        self.assertTrue(highlight_fuzzy_match("alphabet", "ap"))
        self.assertTrue(CustomPromptLexer().lex_document(Document("help -i file"))(0))

    def test_config_reads_writes_in_temporary_directory(self) -> None:
        config_dir = self.work_dir / "config"
        with (
            patch(
                "easyrip.easyrip_config.config.get_CONFIG_DIR", return_value=config_dir
            ),
            patch.object(config, "_config", None),
        ):
            config.init()
            self.assertTrue(config.set_user_profile("language", "zh-Hans-CN"))
            self.assertEqual(config.get_user_profile("language"), "zh-Hans-CN")
            self.assertFalse(config.set_user_profile("refresh_progress_sec", "fast"))
            self.assertEqual(config.get_user_profile("unknown", "fallback"), "fallback")

    def test_config_regeneration_and_prompt_completer_edges(self) -> None:
        config_dir = self.work_dir / "config"
        prompt_custom = self.work_dir / "custom.toml"
        with (
            patch(
                "easyrip.easyrip_config.config.get_CONFIG_DIR", return_value=config_dir
            ),
            patch.object(config, "_config", None),
        ):
            config.init()
            config.regenerate_config()
            self.assertTrue((config_dir / "config.json").is_file())

        with (
            patch.object(easyrip_prompt, "PROMPT_CUSTOM_FILE", prompt_custom),
            patch.object(
                easyrip_prompt, "_easyrip_prompt__prompt_custom_data", {"build": "version"}
            ),
        ):
            from easyrip.easyrip_prompt import CustomPromptCompleter

            completions = list(
                CustomPromptCompleter().get_completions(
                    Document("bu"), CompleteEvent()
                )
            )
            self.assertEqual(completions[0].text, "version")
        self.assertEqual(highlight_fuzzy_match("alpha", "z")[0][1], "alpha")


class _Response:
    def __init__(self, body: bytes, status: int = 200) -> None:
        self.body = body
        self.status = status

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def read(self) -> bytes:
        return self.body


class TestMockedExternalServices(SelfContainedTestCase):
    def test_release_api_parsers_and_caches(self) -> None:
        with patch.object(
            third_party_api,
            "open_req",
            return_value=_Response(b'{"tag_name": "v1.2.3"}'),
        ):
            self.assertEqual(
                third_party_api.github.get_latest_release_ver(
                    "https://example.invalid"
                ),
                "1.2.3",
            )

        with patch.object(
            third_party_api,
            "open_req",
            return_value=_Response(b'{"version": "7.1"}'),
        ):
            self.assertEqual(
                third_party_api.ffmpeg.get_latest_release_ver(flush_cache=True), "7.1"
            )

        xml = b"<root><latest-source><version>101.0</version></latest-source></root>"
        with patch.object(third_party_api, "open_req", return_value=_Response(xml)):
            self.assertEqual(
                third_party_api.mkvtoolnix.get_latest_release_ver(flush_cache=True),
                "101.0",
            )

        with patch.object(third_party_api, "open_req", side_effect=OSError("offline")):
            self.assertIsNone(
                third_party_api.github.get_latest_release_ver("https://example.invalid")
            )
            self.assertIsNone(
                third_party_api.ffmpeg.get_latest_release_ver(flush_cache=True)
            )

    def test_http_crypto_helpers(self) -> None:
        original_key = MainHTTPRequestHandler.aes_key
        try:
            MainHTTPRequestHandler.aes_key = None
            self.assertEqual(MainHTTPRequestHandler.str_to_aes('"plain"'), '"plain"')
            self.assertEqual(MainHTTPRequestHandler.aes_to_str('"plain"'), "plain")

            MainHTTPRequestHandler.aes_key = b"0123456789abcdef"
            encrypted = MainHTTPRequestHandler.str_to_aes('"secret"')
            self.assertNotEqual(encrypted, '"secret"')
            self.assertEqual(MainHTTPRequestHandler.aes_to_str(encrypted), "secret")
        finally:
            MainHTTPRequestHandler.aes_key = original_key

    def test_open_request_uses_configured_and_system_proxies(self) -> None:
        class Opener:
            def open(self, request: object) -> object:
                return request

        with (
            patch("easyrip.easyrip_config.config.config.get_user_profile", return_value="{'https': 'http://proxy'}"),
            patch("urllib.request.build_opener", return_value=Opener()) as build_opener,
        ):
            request = third_party_api.urllib.request.Request("https://example.invalid")
            self.assertIs(third_party_api.open_req(request), request)
            self.assertTrue(build_opener.called)

        with (
            patch("easyrip.easyrip_config.config.config.get_user_profile", return_value="auto"),
            patch("urllib.request.getproxies", return_value={"http": "http://system"}),
            patch("urllib.request.build_opener", return_value=Opener()),
        ):
            request = third_party_api.urllib.request.Request("https://example.invalid")
            self.assertIs(third_party_api.open_req(request), request)

    def test_server_initialization_without_listening(self) -> None:
        class Server:
            server_port = 4321

            def serve_forever(self) -> None:
                raise KeyboardInterrupt

        class ImmediateThread:
            def __init__(self, *, target, daemon: bool) -> None:
                self.target = target
                self.daemon = daemon

            def start(self) -> None:
                self.target()

        hook_called: list[bool] = []
        with (
            patch.object(http_server, "HTTPServer", return_value=Server()),
            patch.object(http_server, "Thread", ImmediateThread),
        ):
            http_server.run_server(
                "127.0.0.1",
                0,
                "password",
                after_start_server_hook=lambda: hook_called.append(True),
            )

        self.assertTrue(hook_called)
        self.assertEqual(MainHTTPRequestHandler.password, "password")
        self.assertIsNotNone(MainHTTPRequestHandler.token)
        self.assertFalse(http_server.Event.is_run_command)

    def test_subtitle_translation_uses_mocked_converter(self) -> None:
        source = self.write_ass("episode.zh-Hans.ass")
        (self.work_dir / "ignored.en.srt").write_text("ignored", encoding="utf-8")

        with patch.object(
            third_party_api.zhconvert,
            "translate",
            side_effect=lambda *, org_text, target_lang: (
                f"{target_lang.value}:{org_text}"
            ),
        ) as translate:
            translated = translate_subtitles(
                self.work_dir,
                "zh-Hans",
                "zh-Hant",
                file_intersection_selector=(source,),
                enable_multithreading=False,
            )

        self.assertEqual(translated[0][0].name, "episode.zh-Hant.ass")
        self.assertTrue(translated[0][1].startswith("Traditional:"))
        translate.assert_called_once()
