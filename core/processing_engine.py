# core/processing_engine.py - 処理エンジン
import subprocess
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

from .video_extractor import VideoExtractor
from .quality_filter import QualityFilter
from .realityscan_interface import RealityScanInterface
from .output_generator import OutputGenerator

class ProcessingEngine:
    """メイン処理エンジン"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # 各処理モジュール初期化
        self.video_extractor = VideoExtractor(config)
        self.quality_filter = QualityFilter(config)
        self.realityscan = RealityScanInterface(config)
        self.output_generator = OutputGenerator(config)
        
        # 進捗管理
        self.progress_info = {
            'overall_progress': 0,
            'phase_progress': 0,
            'current_phase': 'Idle',
            'iteration_count': 0,
            'total_images': 0
        }
        
        self.stop_requested = False
    
    def execute_full_workflow(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """フルワークフロー実行"""
        try:
            self.logger.info("処理開始")
            self.progress_info['current_phase'] = '初期化中'
            
            # config にも output_dir を渡して VideoExtractor が参照できるようにする
            self.config['output_dir'] = params['output_dir']

            # 1. 初期フレーム抽出
            initial_frames = self._extract_initial_frames(params)
            
            # フレームが1枚も抽出されなかった場合のチェック
            if not initial_frames:
                self.logger.error("フレームが1枚も抽出されませんでした。処理を中断します。")
                raise RuntimeError("フレーム抽出に失敗しました。動画ファイルパスや形式を確認してください。")

            # 2. 適応的アライメント処理
            alignment_result = self._adaptive_alignment_process(initial_frames)
            # alignment_result には抽出したフレーム情報を含める
            alignment_result['images'] = initial_frames

            # 3. 最終出力生成
            output_result = self._generate_final_output(alignment_result, params)
            
            self.logger.info("処理完了")
            return output_result
            
        except Exception as e:
            self.logger.error(f"処理中にエラー: {str(e)}")
            raise
    
    def _extract_initial_frames(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """初期フレーム抽出"""
        self.progress_info['current_phase'] = '初期フレーム抽出中'
        
        all_frames = []
        target_per_video = params['target_images'] // len(params['videos'])
        
        # GUIからのフィルタリング設定を取得
        confidence = params.get('person_confidence', 0.5)
        area_threshold = params.get('area_threshold', 0.15)

        for i, video_path in enumerate(params['videos']):
            if self.stop_requested:
                break
                
            self.logger.info(f"動画{i+1}/{len(params['videos'])}を処理中: {Path(video_path).name}")
            
            frames = self.video_extractor.extract_adaptive_frames(
                video_path, 
                target_per_video,
                self.quality_filter,
                confidence,
                area_threshold
            )
            
            all_frames.extend(frames)
            
            # 進捗更新
            self.progress_info['phase_progress'] = (i + 1) / len(params['videos']) * 100
        
        self.progress_info['total_images'] = len(all_frames)
        self.logger.info(f"初期フレーム抽出完了: {len(all_frames)}枚")
        
        return all_frames
    
    def _adaptive_alignment_process(self, initial_frames: List[Dict[str, Any]]) -> Dict[str, Any]:
        """適応的アライメント処理"""
        self.progress_info['current_phase'] = 'アライメント処理中'
        
        current_images = initial_frames
        iteration_count = 0
        max_iterations = 10
        iteration_history = []
        
        while iteration_count < max_iterations:
            if self.stop_requested:
                break
                
            self.logger.info(f"=== アライメント反復 {iteration_count + 1} 開始 ===")
            self.progress_info['iteration_count'] = iteration_count + 1
            
            # RealityScanアライメント実行
            alignment_result = self.realityscan.run_alignment(current_images)
            
            # 結果評価
            quality_score = self._calculate_quality_score(alignment_result)
            iteration_history.append({
                'iteration': iteration_count,
                'image_count': len(current_images),
                'component_count': len(alignment_result['components']),
                'quality_score': quality_score
            })
            
            # 終了条件チェック
            should_stop, stop_reason = self._should_stop_iteration(
                alignment_result, iteration_history
            )
            
            if should_stop:
                self.logger.info(f"反復終了: {stop_reason}")
                break
            
            # 追加画像選定
            additional_images = self._select_additional_images(alignment_result, current_images)
            
            if not additional_images:
                self.logger.info("追加可能な画像がありません")
                break
            
            current_images.extend(additional_images)
            self.logger.info(f"画像追加: +{len(additional_images)} (総数: {len(current_images)})")
            
            iteration_count += 1
            
            # 進捗更新
            self.progress_info['overall_progress'] = min(70 + (iteration_count / max_iterations) * 20, 90)
        
        return alignment_result
    
    def _should_stop_iteration(self, alignment_result: Dict[str, Any], 
                              iteration_history: List[Dict[str, Any]]) -> tuple[bool, str]:
        """反復終了判定"""
        # 1. 単一コンポーネント達成チェック
        if len(alignment_result['components']) == 1:
            main_component = alignment_result['components'][0]
            if main_component['image_count'] / alignment_result['total_images'] >= 0.95:
                return True, "single_component_achieved"
        
        # 2. 品質閾値チェック
        if (alignment_result['mean_reprojection_error'] <= 2.0 and
            alignment_result['alignment_ratio'] >= 0.95):
            return True, "quality_threshold_met"
        
        # 3. 収束チェック
        if len(iteration_history) >= 3:
            recent_improvements = [
                iteration_history[-i]['quality_score'] - iteration_history[-i-1]['quality_score']
                for i in range(1, 4)
            ]
            if all(imp < 0.02 for imp in recent_improvements):
                return True, "convergence_detected"
        
        return False, "continue_iteration"
    
    def _calculate_quality_score(self, alignment_result: Dict[str, Any]) -> float:
        """品質スコア計算"""
        # 実装: アライメント品質の総合評価
        alignment_ratio = alignment_result['alignment_ratio']
        component_penalty = len(alignment_result['components']) * 0.1
        error_penalty = alignment_result['mean_reprojection_error'] / 10.0
        
        return alignment_ratio - component_penalty - error_penalty
    
    def _select_additional_images(self, alignment_result: Dict[str, Any], all_images: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """追加画像選定"""
        # 実装: コンポーネント分析に基づく追加画像選定
        problem_areas = self._analyze_alignment_problems(alignment_result, all_images)
        additional_images = self.video_extractor.extract_targeted_frames(problem_areas)
        
        return additional_images
    
    def _analyze_alignment_problems(self, alignment_result: Dict[str, Any], all_images: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """アライメントの問題領域を分析"""
        self.logger.info("アライメントの問題領域を分析中...")
        problems = []

        # 画像名とメタデータのマップを作成
        image_name_to_meta = {Path(img['image_path']).name: img for img in all_images}

        # 1. 未整列画像の分析
        unaligned_images_meta = []
        if 'unaligned_images' in alignment_result:
            for img_name in alignment_result['unaligned_images']:
                if img_name in image_name_to_meta:
                    unaligned_images_meta.append(image_name_to_meta[img_name])

        if unaligned_images_meta:
            # タイムスタンプでソートし、クラスタリングする（単純な時間差で）
            unaligned_images_meta.sort(key=lambda x: x['timestamp'])

            if unaligned_images_meta:
                cluster_start_meta = unaligned_images_meta[0]
                last_ts = cluster_start_meta['timestamp']

                for i in range(1, len(unaligned_images_meta)):
                    current_meta = unaligned_images_meta[i]
                    # タイムスタンプの差が5秒以上あれば別のクラスタとみなす
                    if current_meta['timestamp'] - last_ts > 5.0:
                        problems.append({
                            'type': 'unaligned_cluster',
                            'start_time': cluster_start_meta['timestamp'],
                            'end_time': last_ts,
                            'video_source': cluster_start_meta['video_source']
                        })
                        cluster_start_meta = current_meta
                    last_ts = current_meta['timestamp']

                # 最後のクラスタを追加
                problems.append({
                    'type': 'unaligned_cluster',
                    'start_time': cluster_start_meta['timestamp'],
                    'end_time': last_ts,
                    'video_source': cluster_start_meta['video_source']
                })
            self.logger.info(f"未整列画像のクラスタを{len(problems)}件検出")

        # 2. コンポーネント間のギャップ分析
        components = alignment_result.get('components', [])
        if len(components) > 1:
            self.logger.info(f"{len(components)}個のコンポーネントを検出。ギャップを分析します。")

            component_boundaries = []
            for comp in components:
                comp_images_meta = [image_name_to_meta[img['name']] for img in comp['images'] if img['name'] in image_name_to_meta]
                if not comp_images_meta:
                    continue

                min_ts = min(img['timestamp'] for img in comp_images_meta)
                max_ts = max(img['timestamp'] for img in comp_images_meta)
                video_source = comp_images_meta[0]['video_source'] # 仮定：コンポーネントは単一ビデオに由来
                component_boundaries.append({'min_ts': min_ts, 'max_ts': max_ts, 'video': video_source})

            # タイムスタンプでソート
            component_boundaries.sort(key=lambda x: x['min_ts'])

            for i in range(len(component_boundaries) - 1):
                gap_start = component_boundaries[i]['max_ts']
                gap_end = component_boundaries[i+1]['min_ts']

                # ギャップが大きい場合（例：1秒以上）
                if gap_end - gap_start > 1.0:
                    # ビデオソースが同じ場合にのみギャップを問題とする
                    if component_boundaries[i]['video'] == component_boundaries[i+1]['video']:
                        problem = {
                            'type': 'component_gap',
                            'start_time': gap_start,
                            'end_time': gap_end,
                            'video_source': component_boundaries[i]['video']
                        }
                        problems.append(problem)
                        self.logger.info(f"コンポーネント間のギャップを検出: {gap_start:.2f}s - {gap_end:.2f}s in {Path(problem['video_source']).name}")

        return problems
    
    def _generate_final_output(self, alignment_result: Dict[str, Any], 
                             params: Dict[str, Any]) -> Dict[str, Any]:
        """最終出力生成"""
        self.progress_info['current_phase'] = '最終出力生成中'
        
        output_result = self.output_generator.generate_3dgs_dataset(
            alignment_result, 
            params['output_dir']
        )
        
        self.progress_info['overall_progress'] = 100
        return output_result
    
    def get_progress_info(self) -> Dict[str, Any]:
        """進捗情報取得"""
        return self.progress_info.copy()
    
    def stop_processing(self):
        """処理停止要求"""
        self.stop_requested = True
        self.realityscan.abort_current_process()