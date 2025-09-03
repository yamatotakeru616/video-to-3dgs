
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox
import logging
import threading
import queue
from pathlib import Path

import sys
import os

# プロジェクトのルートディレクトリをPythonのパスに追加
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# プロジェクトのコアモジュールをインポート
from core.processing_engine import ProcessingEngine
from utils.config_manager import ConfigManager
from utils.logging_utils import setup_logging, QueueHandler

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Video to 3DGS Preprocessor")
        self.geometry("800x600")

        self.video_paths = []
        self.output_dir = ""

        # --- UI要素の作成 ---
        main_frame = tk.Frame(self, padx=10, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # ファイル選択フレーム
        selection_frame = tk.Frame(main_frame)
        selection_frame.pack(fill=tk.X, pady=5)

        self.btn_select_videos = tk.Button(selection_frame, text="動画ファイルを選択", command=self.select_videos)
        self.btn_select_videos.pack(side=tk.LEFT, padx=5)
        self.lbl_videos = tk.Label(selection_frame, text="動画が選択されていません", anchor="w")
        self.lbl_videos.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 出力先選択フレーム
        output_frame = tk.Frame(main_frame)
        output_frame.pack(fill=tk.X, pady=5)

        self.btn_select_output = tk.Button(output_frame, text="出力先フォルダを選択", command=self.select_output_dir)
        self.btn_select_output.pack(side=tk.LEFT, padx=5)
        self.lbl_output = tk.Label(output_frame, text="出力先が選択されていません", anchor="w")
        self.lbl_output.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 処理開始ボタン
        self.btn_start = tk.Button(main_frame, text="アライメント処理を開始", command=self.start_processing, state=tk.DISABLED)
        self.btn_start.pack(fill=tk.X, pady=10)

        # ログ表示エリア
        log_frame = tk.LabelFrame(main_frame, text="ログ")
        log_frame.pack(fill=tk.BOTH, expand=True)
        self.log_area = scrolledtext.ScrolledText(log_frame, state='disabled', wrap=tk.WORD)
        self.log_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # --- ロギング設定 ---
        self.log_queue = queue.Queue()
        self.queue_handler = QueueHandler(self.log_queue)
        
        # プロジェクト共通のロギング設定を呼び出す
        setup_logging(gui_handler=self.queue_handler)
        self.logger = logging.getLogger()

        self.after(100, self.poll_log_queue)

    def select_videos(self):
        self.video_paths = filedialog.askopenfilenames(
            title="動画ファイルを選択",
            filetypes=[("Video files", "*.mp4 *.mov *.avi"), ("All files", "*.*")]
        )
        if self.video_paths:
            self.lbl_videos.config(text=f"{len(self.video_paths)}個の動画を選択しました: {', '.join(Path(p).name for p in self.video_paths)}")
        else:
            self.lbl_videos.config(text="動画が選択されていません")
        self.update_start_button_state()

    def select_output_dir(self):
        self.output_dir = filedialog.askdirectory(title="出力先フォルダを選択")
        if self.output_dir:
            self.lbl_output.config(text=f"出力先: {self.output_dir}")
        else:
            self.lbl_output.config(text="出力先が選択されていません")
        self.update_start_button_state()

    def update_start_button_state(self):
        if self.video_paths and self.output_dir:
            self.btn_start.config(state=tk.NORMAL)
        else:
            self.btn_start.config(state=tk.DISABLED)

    def start_processing(self):
        if not self.video_paths or not self.output_dir:
            messagebox.showerror("エラー", "動画ファイルと出力先フォルダの両方を選択してください。")
            return

        self.btn_start.config(state=tk.DISABLED)
        self.log_area.config(state='normal')
        self.log_area.delete(1.0, tk.END)
        self.log_area.config(state='disabled')

        # 処理を別スレッドで実行
        self.processing_thread = threading.Thread(
            target=self.run_workflow_thread,
            daemon=True
        )
        self.processing_thread.start()

    def run_workflow_thread(self):
        """コア処理をバックグラウンドで実行するスレッド"""
        try:
            self.logger.info("=== 処理開始 ===")
            
            # 設定ファイルの読み込み
            config_manager = ConfigManager()
            config = config_manager.load_config()

            # 処理エンジンを初期化
            engine = ProcessingEngine(config)

            # GUIから受け取ったパラメータを設定
            params = {
                'videos': self.video_paths,
                'output_dir': self.output_dir,
                'target_images': config.get('initial_frame_extraction', {}).get('target_images', 100),
                'person_confidence': config.get('quality_filter', {}).get('person_confidence', 0.5),
                'area_threshold': config.get('quality_filter', {}).get('area_threshold', 0.15),
            }
            
            # config にも output_dir を渡して VideoExtractor が参照できるようにする
            engine.config['output_dir'] = params['output_dir']

            # 1. 初期フレーム抽出
            self.logger.info("--- ステップ1: 初期フレーム抽出 ---")
            initial_frames = engine._extract_initial_frames(params)
            
            if not initial_frames:
                self.logger.error("フレームが1枚も抽出されませんでした。処理を中断します。")
                raise RuntimeError("フレーム抽出に失敗しました。")

            # 2. 適応的アライメント処理
            self.logger.info("--- ステップ2: 適応的アライメント処理 ---")
            alignment_result = engine._adaptive_alignment_process(initial_frames)
            
            self.logger.info("=== アライメント処理完了 ===")
            self.logger.info(f"アライメント結果: {len(alignment_result.get('components', []))}個のコンポーネントを検出。")
            
            # 3. 最終出力生成 (追加)
            self.logger.info("--- ステップ3: 最終出力生成 ---")
            output_result = engine._generate_final_output(alignment_result, params)
            self.logger.info(f"最終出力が {output_result.get('output_path')} に生成されました。")

            messagebox.showinfo("完了", "アライメント処理とデータ生成が正常に完了しました。")

        except Exception as e:
            self.logger.error(f"処理中にエラーが発生しました: {e}", exc_info=True)
            messagebox.showerror("エラー", f"処理中にエラーが発生しました:\n{e}")
        finally:
            self.btn_start.config(state=tk.NORMAL)

    def poll_log_queue(self):
        """キューからログメッセージをポーリングしてUIに表示"""
        while True:
            try:
                record = self.log_queue.get(block=False)
            except queue.Empty:
                break
            else:
                self.display_log_message(record)
        self.after(100, self.poll_log_queue)

    def display_log_message(self, record):
        self.log_area.config(state='normal')
        self.log_area.insert(tk.END, record + '\n')
        self.log_area.see(tk.END)
        self.log_area.config(state='disabled')

if __name__ == "__main__":
    app = App()
    app.mainloop()
