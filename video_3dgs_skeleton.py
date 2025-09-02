# main_app.py - メインアプリケーション
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import queue
import os
from pathlib import Path
from typing import List, Dict, Any
import yaml
import logging
from datetime import datetime, timedelta

from core.processing_engine import ProcessingEngine
from core.time_estimator import ProcessingTimeEstimator
from utils.config_manager import ConfigManager
from utils.logging_utils import setup_logging

class MainApplication:
    """メインGUIアプリケーション"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("360° Video to 3DGS Dataset Generator")
        self.root.geometry("1200x800")
        
        # 設定管理
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load_config()
        
        # 処理エンジン
        self.processing_engine = ProcessingEngine(self.config)
        self.time_estimator = ProcessingTimeEstimator()
        
        # GUI状態管理
        self.selected_videos = []
        self.output_directory = tk.StringVar()
        self.is_processing = False
        self.log_queue = queue.Queue()
        
        # ログ設定
        setup_logging(self.log_queue)
        
        self.setup_gui()
        self.setup_log_monitor()
    
    def setup_gui(self):
        """GUI要素の初期化"""
        # メインフレーム
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 動画選択セクション
        self.setup_video_selection(main_frame)
        
        # 設定セクション
        self.setup_settings_section(main_frame)
        
        # 実行制御セクション
        self.setup_execution_control(main_frame)
        
        # 進捗・ログセクション
        self.setup_progress_section(main_frame)
        
        # ステータスバー
        self.setup_status_bar()
    
    def setup_video_selection(self, parent):
        """動画選択UI"""
        video_frame = ttk.LabelFrame(parent, text="360度動画選択", padding="5")
        video_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # 動画リスト
        self.video_listbox = tk.Listbox(video_frame, height=6)
        self.video_listbox.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=5)
        
        # ボタン群
        ttk.Button(video_frame, text="動画追加", 
                  command=self.add_videos).grid(row=1, column=0, padx=5, pady=5)
        ttk.Button(video_frame, text="削除", 
                  command=self.remove_video).grid(row=1, column=1, padx=5, pady=5)
        
        # 保存先指定
        ttk.Label(video_frame, text="保存先:").grid(row=2, column=0, sticky=tk.W, padx=5)
        ttk.Entry(video_frame, textvariable=self.output_directory, 
                 width=50).grid(row=2, column=1, padx=5, pady=5)
        ttk.Button(video_frame, text="参照", 
                  command=self.select_output_dir).grid(row=2, column=2, padx=5)
    
    def setup_settings_section(self, parent):
        """設定セクション"""
        settings_frame = ttk.LabelFrame(parent, text="処理設定", padding="5")
        settings_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        # YOLO設定
        ttk.Label(settings_frame, text="人物検出感度:").grid(row=0, column=0, sticky=tk.W)
        self.person_confidence = tk.DoubleVar(value=0.5)
        ttk.Scale(settings_frame, from_=0.1, to=0.9, 
                 variable=self.person_confidence, length=200).grid(row=0, column=1, padx=5)
        
        # 面積比閾値
        ttk.Label(settings_frame, text="除外面積比:").grid(row=1, column=0, sticky=tk.W)
        self.area_threshold = tk.DoubleVar(value=0.15)
        ttk.Scale(settings_frame, from_=0.05, to=0.3, 
                 variable=self.area_threshold, length=200).grid(row=1, column=1, padx=5)
        
        # 目標画像数
        ttk.Label(settings_frame, text="初期画像数:").grid(row=2, column=0, sticky=tk.W)
        self.target_images = tk.IntVar(value=2000)
        ttk.Entry(settings_frame, textvariable=self.target_images, 
                 width=10).grid(row=2, column=1, sticky=tk.W, padx=5)
        
        # CUDA使用設定
        self.use_cuda = tk.BooleanVar(value=True)
        ttk.Checkbutton(settings_frame, text="CUDA使用", 
                       variable=self.use_cuda).grid(row=3, column=0, sticky=tk.W)
    
    def setup_execution_control(self, parent):
        """実行制御セクション"""
        exec_frame = ttk.LabelFrame(parent, text="実行制御", padding="5")
        exec_frame.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        # 実行ボタン
        self.execute_button = ttk.Button(exec_frame, text="処理実行", 
                                        command=self.start_processing)
        self.execute_button.grid(row=0, column=0, padx=5, pady=5)
        
        # 停止ボタン
        self.stop_button = ttk.Button(exec_frame, text="停止", 
                                     command=self.stop_processing, state='disabled')
        self.stop_button.grid(row=0, column=1, padx=5, pady=5)
        
        # 設定保存/読込
        ttk.Button(exec_frame, text="設定保存", 
                  command=self.save_settings).grid(row=1, column=0, padx=5, pady=5)
        ttk.Button(exec_frame, text="設定読込", 
                  command=self.load_settings).grid(row=1, column=1, padx=5, pady=5)
    
    def setup_progress_section(self, parent):
        """進捗・ログセクション"""
        progress_frame = ttk.LabelFrame(parent, text="進捗状況", padding="5")
        progress_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # 全体進捗バー
        ttk.Label(progress_frame, text="全体進捗:").grid(row=0, column=0, sticky=tk.W)
        self.overall_progress = ttk.Progressbar(progress_frame, length=400, mode='determinate')
        self.overall_progress.grid(row=0, column=1, columnspan=2, sticky=(tk.W, tk.E), padx=5)
        
        # 現在のフェーズ進捗
        ttk.Label(progress_frame, text="現在フェーズ:").grid(row=1, column=0, sticky=tk.W)
        self.phase_progress = ttk.Progressbar(progress_frame, length=400, mode='determinate')
        self.phase_progress.grid(row=1, column=1, columnspan=2, sticky=(tk.W, tk.E), padx=5)
        
        # 時間情報表示
        time_info_frame = ttk.Frame(progress_frame)
        time_info_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        self.start_time_label = ttk.Label(time_info_frame, text="開始時刻: --")
        self.start_time_label.grid(row=0, column=0, padx=10)
        
        self.elapsed_time_label = ttk.Label(time_info_frame, text="経過時間: --")
        self.elapsed_time_label.grid(row=0, column=1, padx=10)
        
        self.eta_label = ttk.Label(time_info_frame, text="予定終了: --")
        self.eta_label.grid(row=0, column=2, padx=10)
        
        # ログ表示
        ttk.Label(progress_frame, text="処理ログ:").grid(row=3, column=0, sticky=tk.W)
        
        log_frame = ttk.Frame(progress_frame)
        log_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        self.log_text = tk.Text(log_frame, height=15, width=80)
        log_scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
    
    def setup_status_bar(self):
        """ステータスバー"""
        self.status_bar = ttk.Label(self.root, text="準備完了", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.grid(row=1, column=0, sticky=(tk.W, tk.E))
    
    def setup_log_monitor(self):
        """ログ監視タイマー"""
        self.root.after(100, self.check_log_queue)
    
    def check_log_queue(self):
        """ログキューからメッセージを取得してGUIに表示"""
        try:
            while True:
                message = self.log_queue.get_nowait()
                self.log_text.insert(tk.END, f"{message}\n")
                self.log_text.see(tk.END)
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.check_log_queue)
    
    def add_videos(self):
        """動画ファイル追加"""
        filetypes = [
            ("動画ファイル", "*.mp4 *.avi *.mov *.mkv"),
            ("すべてのファイル", "*.*")
        ]
        files = filedialog.askopenfilenames(filetypes=filetypes)
        
        for file in files:
            if file not in self.selected_videos:
                self.selected_videos.append(file)
                self.video_listbox.insert(tk.END, os.path.basename(file))
    
    def remove_video(self):
        """選択動画削除"""
        selection = self.video_listbox.curselection()
        if selection:
            index = selection[0]
            self.selected_videos.pop(index)
            self.video_listbox.delete(index)
    
    def select_output_dir(self):
        """出力ディレクトリ選択"""
        directory = filedialog.askdirectory()
        if directory:
            self.output_directory.set(directory)
    
    def start_processing(self):
        """処理開始"""
        if not self.selected_videos:
            messagebox.showerror("エラー", "動画ファイルを選択してください")
            return
        
        if not self.output_directory.get():
            messagebox.showerror("エラー", "出力ディレクトリを指定してください")
            return
        
        self.is_processing = True
        self.execute_button.config(state='disabled')
        self.stop_button.config(state='normal')
        
        # 処理パラメータ設定
        processing_params = {
            'videos': self.selected_videos,
            'output_dir': self.output_directory.get(),
            'target_images': self.target_images.get(),
            'person_confidence': self.person_confidence.get(),
            'area_threshold': self.area_threshold.get(),
            'use_cuda': self.use_cuda.get()
        }
        
        # バックグラウンド処理開始
        self.processing_thread = threading.Thread(
            target=self.processing_worker,
            args=(processing_params,)
        )
        self.processing_thread.start()
        
        # 進捗監視開始
        self.start_progress_monitoring()
    
    def processing_worker(self, params):
        """バックグラウンド処理ワーカー"""
        try:
            result = self.processing_engine.execute_full_workflow(params)
            self.root.after(0, lambda: self.processing_completed(result))
        except Exception as e:
            self.root.after(0, lambda e=e: self.processing_failed(str(e)))
    
    def start_progress_monitoring(self):
        """進捗監視開始"""
        self.start_time = datetime.now()
        self.update_progress_display()
    
    def update_progress_display(self):
        """進捗表示更新"""
        if not self.is_processing:
            return
        
        # 経過時間計算
        elapsed = datetime.now() - self.start_time
        self.elapsed_time_label.config(text=f"経過時間: {str(elapsed).split('.')[0]}")
        
        # 進捗情報取得
        progress_info = self.processing_engine.get_progress_info()
        
        # 進捗バー更新
        self.overall_progress['value'] = progress_info['overall_progress']
        self.phase_progress['value'] = progress_info['phase_progress']
        
        # 予定終了時刻計算・表示
        if progress_info['overall_progress'] > 0:
            estimated_completion = self.time_estimator.estimate_completion_time(
                progress_info, elapsed
            )
            self.eta_label.config(text=f"予定終了: {estimated_completion.strftime('%H:%M:%S')}")
        
        # ステータス更新
        self.status_bar.config(text=progress_info['current_phase'])
        
        # 1秒後に再更新
        self.root.after(1000, self.update_progress_display)
    
    def stop_processing(self):
        """処理停止"""
        self.processing_engine.stop_processing()
        self.is_processing = False
        self.execute_button.config(state='normal')
        self.stop_button.config(state='disabled')
    
    def processing_completed(self, result):
        """処理完了時の処理"""
        self.is_processing = False
        self.execute_button.config(state='normal')
        self.stop_button.config(state='disabled')
        
        messagebox.showinfo("完了", f"処理が完了しました\n出力先: {result['output_path']}")
    
    def processing_failed(self, error_message):
        """処理失敗時の処理"""
        self.is_processing = False
        self.execute_button.config(state='normal')
        self.stop_button.config(state='disabled')
        
        messagebox.showerror("エラー", f"処理中にエラーが発生しました:\n{error_message}")
    
    def save_settings(self):
        """設定保存"""
        # 実装: 現在の設定をYAMLファイルに保存
        pass
    
    def load_settings(self):
        """設定読込"""
        # 実装: YAMLファイルから設定を読込
        pass
    
    def run(self):
        """アプリケーション実行"""
        self.root.mainloop()

# 実行エントリーポイント
if __name__ == "__main__":
    """アプリケーション実行"""
    app = MainApplication()
    app.run()
