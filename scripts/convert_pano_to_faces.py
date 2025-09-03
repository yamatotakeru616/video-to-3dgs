"""scripts/convert_pano_to_faces.py
簡易スクリプト: 合成パノラマまたは入力画像から6面を生成して保存する。

使い方:
  # 合成パノラマでテスト
  python scripts/convert_pano_to_faces.py --outdir ./tmp_faces

  # 既存パノラマ画像を変換
  python scripts/convert_pano_to_faces.py --input path/to/pano.jpg --outdir ./out_faces

"""
import argparse
from pathlib import Path
import numpy as np
import cv2
from models.config_models import AppConfig
from core.video_extractor import VideoExtractor


def make_synthetic_equirectangular(w=1024, h=512):
    img = np.zeros((h, w, 3), dtype=np.uint8)
    for x in range(w):
        img[:, x, 0] = int(255 * (x / (w - 1)))
        img[:, x, 1] = int(255 * (1.0 - x / (w - 1)))
        img[:, x, 2] = 128
    return img


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--input', type=str, default=None, help='入力パノラマ画像パス (省略すると合成画像を使用)')
    p.add_argument('--outdir', type=str, default='./tmp_faces', help='出力ディレクトリ')
    p.add_argument('--face-size', type=int, default=512, help='出力 face 解像度')
    args = p.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    if args.input:
        src = Path(args.input)
        if not src.exists():
            print(f'入力ファイルが見つかりません: {src}')
            return
        img = cv2.imread(str(src))
        if img is None:
            print(f'画像を読み込めませんでした: {src}')
            return
    else:
        img = make_synthetic_equirectangular(w=1024, h=512)

    extractor = VideoExtractor(AppConfig())
    faces = extractor._equirectangular_to_cubefaces(img, face_size=args.face_size)

    saved = []
    for name, face in faces.items():
        path = outdir / f'face_{name}.jpg'
        cv2.imwrite(str(path), face)
        saved.append(path)

    print('Saved faces:')
    for pth in saved:
        print(' -', pth)


if __name__ == '__main__':
    main()
