import logging
import shutil
import os
from pathlib import Path
import sys
import argparse

from models.config_models import RealityScanConfig
from core.realityscan_interface import RealityScanInterface


def find_realityscan_exe():
    candidates = [
        r"C:\Program Files\Epic Games\RealityScan_2.0\RealityScan.exe",
        r"C:\Program Files\Epic Games\RealityScan\RealityScan.exe",
        r"C:\Program Files (x86)\RealityScan\RealityScan.exe",
    ]
    for p in candidates:
        if Path(p).exists():
            return str(Path(p))
    which = shutil.which('RealityScan.exe') or shutil.which('RealityScan')
    if which:
        return which
    return None


def prepare_images_from_tmp(tmp_dir: Path) -> list:
    faces_dir = tmp_dir
    if not faces_dir.exists():
        raise FileNotFoundError(f"faces folder not found: {faces_dir}")
    images = []
    for p in sorted(faces_dir.glob('*.jpg')):
        images.append({'image_path': str(p.resolve()), 'timestamp': 0.0, 'video_source': str(p.parent)})
    return images


def main():
    logging.basicConfig(level=logging.INFO)
    p = argparse.ArgumentParser()
    p.add_argument('--exe', type=str, default=None, help='RealityScan 実行ファイルのフルパス（省略時は自動検出）')
    p.add_argument('--timeout', type=int, default=120, help='RealityScan タイムアウト秒数')
    args = p.parse_args()

    exe = args.exe or find_realityscan_exe()
    if not exe:
        print('RealityScan executable not found on this machine. Aborting integration test.')
        sys.exit(2)

    print('Using RealityScan executable:', exe)

    # look for tmp_faces created by earlier script
    tmp_faces = Path.cwd() / 'tmp_faces'
    if not tmp_faces.exists():
        print(f"tmp_faces not found at {tmp_faces}. Please run scripts/convert_pano_to_faces.py first or provide face images.")
        sys.exit(3)

    images = prepare_images_from_tmp(tmp_faces)
    if not images:
        print('No face images found in tmp_faces. Aborting.')
        sys.exit(4)

    config = RealityScanConfig(executable_path=exe, timeout_seconds=120)
    config = RealityScanConfig(executable_path=exe, timeout_seconds=args.timeout)
    iface = RealityScanInterface(config)

    try:
        result = iface.run_alignment(images, quality='draft')
        print('Alignment result summary:')
        print(' total_images:', result.get('total_images'))
        print(' components:', len(result.get('components', [])))
        print(' alignment_ratio:', result.get('alignment_ratio'))
        print(' mean_reprojection_error:', result.get('mean_reprojection_error'))
        print(' raw_output_path:', result.get('raw_output_path'))
    except Exception as e:
        print('Integration run failed with exception:', e)
        sys.exit(1)


if __name__ == '__main__':
    main()
