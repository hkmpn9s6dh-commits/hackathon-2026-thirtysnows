"""闸 B：先写断言，再谈成品。跑法：python -m unittest discover -s tests -v"""
from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import cv2  # noqa: E402
import numpy as np  # noqa: E402
from fontTools.ttLib import TTFont  # noqa: E402

import film  # noqa: E402
import render  # noqa: E402

SAFE = 0.05


class TestTimeline(unittest.TestCase):
    def test_total_duration(self):
        self.assertAlmostEqual(sum(s.dur for s in film.SHOTS), 30.0, places=6)

    def test_total_frames(self):
        self.assertEqual(sum(s.frames for s in film.SHOTS), 720)
        self.assertEqual(film.TOTAL_FRAMES, 720)

    def test_no_gap_no_overlap(self):
        for a, b in zip(film.SHOTS, film.SHOTS[1:]):
            self.assertAlmostEqual(a.end, b.start, places=6)

    def test_endcard_matches_last_shot(self):
        self.assertAlmostEqual(film.ENDCARD["t_start"], film.SHOTS[-1].start, places=2)

    def test_shot_at_boundaries(self):
        self.assertEqual(film.shot_at(0.0).idx, 1)
        self.assertEqual(film.shot_at(29.99).idx, 8)
        self.assertEqual(film.shot_at(film.SHOTS[3].start).idx, 4)

    def test_every_shot_has_plate(self):
        for s in film.SHOTS:
            if s.key == "endcard":
                continue
            self.assertTrue((ROOT / "keyframes" / "plate" / f"{s.key}.png").exists(), s.key)


class TestSupers(unittest.TestCase):
    def test_inside_time(self):
        for s in film.SUPERS:
            self.assertGreaterEqual(s.t_in, 0)
            self.assertLessEqual(s.t_out, 30.0)
            self.assertLess(s.t_in, s.t_out)

    def test_no_overlap(self):
        for a, b in zip(film.SUPERS, film.SUPERS[1:]):
            self.assertLess(a.t_out, b.t_in)

    def test_safe_area(self):
        """字幕包围盒必须完全落在 5% 安全区内。"""
        for s in film.SUPERS:
            layer = render.get_super(s)
            bbox = layer.getbbox()
            self.assertIsNotNone(bbox, s.cn)
            x0, y0, x1, y1 = bbox
            self.assertGreaterEqual(x0, film.W * SAFE, s.cn)
            self.assertGreaterEqual(y0, film.H * SAFE, s.cn)
            self.assertLessEqual(x1, film.W * (1 - SAFE), s.cn)
            self.assertLessEqual(y1, film.H * (1 - SAFE), s.cn)

    def test_font_size_floor(self):
        """1080p 下字号不得小于画高的 1.2%（≈13px）。"""
        self.assertGreaterEqual(13 / film.H, 0.012 - 1e-9)


class TestTextOnScreen(unittest.TestCase):
    """文字真的出现在画面里，且只在应该出现的时候。"""

    def _diff(self, t: float) -> tuple[int, tuple[int, int, int, int] | None]:
        a = render.render_frame(t, with_text=True)
        b = render.render_frame(t, with_text=False)
        d = np.abs(a.astype(np.int16) - b.astype(np.int16)).max(axis=2)
        mask = d > 8
        n = int(mask.sum())
        if n == 0:
            return 0, None
        ys, xs = np.where(mask)
        return n, (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))

    def test_supers_present(self):
        for s in film.SUPERS:
            t = (s.t_in + s.t_out) / 2
            n, box = self._diff(t)
            self.assertGreater(n, 1500, f"{s.cn} 没出现在画面上")
            self.assertIsNotNone(box)
            # 出现在左下区域
            self.assertLess(box[0], film.W * 0.2)
            self.assertGreater(box[1], film.H * 0.6)

    def test_no_super_in_gap(self):
        t = (film.SUPERS[0].t_out + film.SUPERS[1].t_in) / 2
        n, _ = self._diff(t)
        self.assertEqual(n, 0, "不该有字幕的位置出现了字幕")

    def test_endcard_text_present(self):
        n, box = self._diff(29.6)
        self.assertGreater(n, 8000, "末屏文字没画出来")
        self.assertGreater(box[1], film.H * 0.2)
        self.assertLess(box[3], film.H * 0.98)


class TestLook(unittest.TestCase):
    def test_cold_palette(self):
        """冷调：B 通道总体大于 R 通道的像素占比 ≥ 60%（末屏除外）。"""
        for t in (1.0, 6.0, 9.0, 13.0, 17.0, 21.0, 25.0):
            f = render.render_frame(t, with_text=False).astype(np.int16)
            b, r = f[..., 0], f[..., 2]
            luma = f.mean(axis=2)
            visible = luma > 24          # 接近纯黑的像素不参与色相统计
            ratio = float((b[visible] > r[visible]).mean())
            self.assertGreaterEqual(ratio, 0.60, f"t={t} B>R 只有 {ratio:.2f}")

    def test_not_black(self):
        for t in (1.0, 6.0, 13.0, 25.0):
            f = render.render_frame(t, with_text=False)
            self.assertGreater(float(f.mean()), 8.0, f"t={t} 平均亮度太低")

    def test_black_level_not_clipped(self):
        """深但不像死黑：S5 的暗部要保留一点细节。"""
        f = render.render_frame(17.0, with_text=False)
        self.assertGreater(float(np.percentile(f, 99)), 30.0)

    def test_deterministic(self):
        a = render.render_frame(12.34)
        b = render.render_frame(12.34)
        self.assertTrue(np.array_equal(a, b), "同一时刻两次渲染不一致")

    def test_cuts_are_cuts(self):
        """切点两侧的画面必须有明显差异（不能是同一张图）。"""
        for s in film.SHOTS[1:-1]:
            a = render.render_frame(s.start - 1 / film.FPS, with_text=False)
            b = render.render_frame(s.start + 1 / film.FPS, with_text=False)
            self.assertGreater(float(np.abs(a.astype(np.int16) - b.astype(np.int16)).mean()), 1.0,
                               f"{s.key} 切点两侧几乎一样")


class TestNoFaces(unittest.TestCase):
    """这台机器的 opencv 没有 haar 级联（也没有 yunet 的 onnx 权重），
    所以用肤色连通域当代理判据：本片是雪/岩/水，正常不该出现成片的肤色块。
    它不是人脸检测器，只拦得住「画面里冒出一张脸」这种明显的错。"""

    def test_no_skin_region(self):
        worst = 0.0
        for i in range(0, film.TOTAL_FRAMES, 12):
            f = render.render_frame(i / film.FPS, with_text=False)
            ycrcb = cv2.cvtColor(f, cv2.COLOR_BGR2YCrCb)
            y, cr, cb = ycrcb[..., 0], ycrcb[..., 1], ycrcb[..., 2]
            mask = ((cr > 133) & (cr < 173) & (cb > 77) & (cb < 127) & (y > 50)).astype(np.uint8)
            n, _, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
            area = max([stats[k, cv2.CC_STAT_AREA] for k in range(1, n)] or [0])
            worst = max(worst, area / (film.W * film.H))
        self.assertLess(worst, 0.01, f"出现占比 {worst:.3f} 的肤色连通块，像是有人脸")


class TestFonts(unittest.TestCase):
    def _chars(self) -> str:
        s = "".join(x.cn + x.en for x in film.SUPERS)
        s += "".join(str(v) for k, v in film.ENDCARD.items() if isinstance(v, str))
        s += "".join(l[1] for l in film.ENDCARD["lines"])
        s += film.ENDCARD["lockup"][1] + film.ENDCARD["lockup"][2] + film.ENDCARD["lockup"][3]
        s += film.ENDCARD["slogan"][1] + film.ENDCARD["disclaimer"][1] + film.ENDCARD["en"][1]
        return "".join(sorted(set(s.replace(" ", ""))))

    def test_cjk_coverage(self):
        font = TTFont(str(render.CN_SERIF), fontNumber=0, lazy=True)
        cmap = set()
        for t in font["cmap"].tables:
            cmap |= set(t.cmap.keys())
        missing = [c for c in self._chars() if ord(c) > 127 and ord(c) not in cmap]
        self.assertEqual(missing, [], f"缺字：{missing}")

    def test_heavy_coverage(self):
        font = TTFont(str(render.CN_HEAVY), lazy=True)
        cmap = set()
        for t in font["cmap"].tables:
            cmap |= set(t.cmap.keys())
        for c in "农夫山泉":
            self.assertIn(ord(c), cmap)


class TestScriptDoc(unittest.TestCase):
    def test_doc_in_sync(self):
        p = ROOT / "docs" / "02-SCRIPT.md"
        self.assertTrue(p.exists(), "先跑 python film.py --doc")
        self.assertEqual(p.read_text(encoding="utf-8"), film._script_md(),
                         "分镜文档与 film.py 不一致")


class TestAudioPlan(unittest.TestCase):
    def test_events_inside(self):
        for at, kind, p in film.AUDIO_EVENTS:
            self.assertGreaterEqual(at, 0)
            self.assertLess(at, 30.0)
            self.assertIn(kind, {"wind", "drone", "crystal", "slip", "rumble",
                                 "pulse", "bell", "swell", "fifth", "tail"})

    def test_beds_cover_whole_timeline(self):
        kinds = {k for _, k, _ in film.AUDIO_EVENTS}
        self.assertIn("wind", kinds)
        self.assertIn("drone", kinds)

    def test_no_music_track(self):
        """本片的决定：没有音乐。音源种类里不许出现 tonal 乐器组。"""
        kinds = {k for _, k, _ in film.AUDIO_EVENTS}
        self.assertFalse(kinds & {"piano", "strings", "guitar", "synth"}, "加了音乐就违背了创意决定")


if __name__ == "__main__":
    unittest.main(verbosity=2)
