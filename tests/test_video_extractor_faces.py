import unittest
import numpy as np
from models.config_models import AppConfig
from core.video_extractor import VideoExtractor


class TestVideoExtractorFaces(unittest.TestCase):
    def test_equirectangular_to_cubefaces(self):
        # 合成 equirectangular 画像を生成 (H=256, W=512)
        h, w = 256, 512
        # 横方向に色が変化するグラデーションを持たせる
        eqp = np.zeros((h, w, 3), dtype=np.uint8)
        for x in range(w):
            eqp[:, x, 0] = int(255 * (x / (w - 1)))
            eqp[:, x, 1] = int(255 * (1.0 - x / (w - 1)))
            eqp[:, x, 2] = 128

        extractor = VideoExtractor(AppConfig())
        faces = extractor._equirectangular_to_cubefaces(eqp, face_size=64)

        # 6 面が返ること
        self.assertEqual(len(faces), 6)
        expected_keys = {'front', 'right', 'back', 'left', 'up', 'down'}
        self.assertEqual(set(faces.keys()), expected_keys)

        for name, img in faces.items():
            # 形状と型を確認
            self.assertEqual(img.shape, (64, 64, 3))
            self.assertEqual(img.dtype, np.uint8)


if __name__ == '__main__':
    unittest.main()
