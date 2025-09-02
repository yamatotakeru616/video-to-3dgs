# 360° Video to 3DGS Dataset Generator

360度動画から3D Gaussian Splatting用の高品質データセットを自動生成するGUIアプリケーション

## 機能概要

- 複数360度動画からの適応的フレーム抽出
- YOLO画像品質フィルタリング（人物除外等）
- RealityScan連携自動アライメント
- CUDA高速処理対応
- リアルタイム進捗・時間予測
- 3DGS最適化出力（COLMAP、カメラCSV、点群PLY）

## 環境構築

```bash
# プロジェクトセットアップ
python scripts/setup_environment.py

# または手動セットアップ
uv sync
uv sync --extra dev
```

## 使用方法

```bash
# アプリケーション起動
uv run python src/main_app.py

# またはスクリプト経由
uv run python -m src.main_app
```

## 出力形式

```
output/
├── images/           # 高解像度JPEG画像
├── sparse/           # COLMAP形式データ
│   ├── cameras.txt
│   ├── images.txt  
│   └── points3D.txt
├── dense/           # 点群PLYファイル
├── camera_params.csv # PostShot用カメラパラメータ
├── processing_log.txt
└── quality_report.html
```

## システム要件

- Python 3.11+
- CUDA対応GPU（推奨）
- RealityScan/RealityCapture
- 16GB+ RAM
- 十分なストレージ容量

## ライセンス

MIT License
"# video-to-3dgs"  
