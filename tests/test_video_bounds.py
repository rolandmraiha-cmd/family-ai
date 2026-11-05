import json
from pathlib import Path
import unittest
from unittest.mock import AsyncMock, patch

from test_modules import modules


class VideoBoundsTests(unittest.IsolatedAsyncioTestCase):
    async def run_video(self, durations, *, max_bytes=100):
        self.commands = []
        values = iter(durations)

        async def launch(*args, **kwargs):
            self.commands.append(args)
            output = b""
            if args[0] == "ffprobe":
                output = json.dumps({"format": {"duration": next(values)}}).encode()
            else:
                Path(args[-1]).write_bytes(b"trimmed-video")
            process = AsyncMock()
            process.returncode = 0
            process.communicate.return_value = (output, None)
            return process

        with patch.object(modules.asyncio, "create_subprocess_exec", side_effect=launch):
            return await modules.bounded_video(b"original-video", 5, max_bytes)

    async def test_exact_cap_keeps_original_without_transcoding(self):
        self.assertEqual(await self.run_video(["5.0"]), b"original-video")
        self.assertEqual([c[0] for c in self.commands], ["ffprobe"])

    async def test_provider_padding_is_trimmed_and_result_is_measured(self):
        self.assertEqual(await self.run_video(["5.366667", "5.0"]), b"trimmed-video")
        self.assertEqual([c[0] for c in self.commands], ["ffprobe", "ffmpeg", "ffprobe"])
        command = self.commands[1]
        self.assertEqual(command[command.index("-t") + 1], "5")
        self.assertEqual(command[command.index("-c:v") + 1], "libx264")

    async def test_invalid_or_still_excessive_duration_fails_closed(self):
        for values in [["NaN"], ["0"], ["N/A"], ["6", "5.01"]]:
            with self.subTest(values=values), self.assertRaises(RuntimeError):
                await self.run_video(values)

    async def test_transcoded_file_size_is_bounded(self):
        with self.assertRaises(RuntimeError):
            await self.run_video(["6"], max_bytes=3)


if __name__ == "__main__":
    unittest.main()
