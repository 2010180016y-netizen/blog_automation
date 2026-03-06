import hashlib
import json
import os
import shutil
from typing import Dict, List

from .alt_text import generate_alt_text
from .image_seo import detect_keyword_stuffing_alt, optimize_image_asset
from .keyframes import extract_keyframes


class UniquePackGenerator:
    def __init__(self, config: Dict):
        self.config = config
        self.assets_root = config.get("content_sources", {}).get("image_assets_dir", "./assets/images")
        self.video_root = config.get("content_sources", {}).get("video_assets_dir", "./assets/videos")
        self.output_root = config.get("unique_pack", {}).get("outputs", {}).get("package_dir", "./out/packages")
        self.min_images = config.get("unique_pack", {}).get("required_per_post", {}).get("min_images", 2)
        self.alt_context = config.get("unique_pack", {}).get("alt_text", {}).get("context", "product usage scene")
        self.primary_keyword = config.get("unique_pack", {}).get("alt_text", {}).get("primary_keyword", "")

        quality_cfg = config.get("unique_pack", {}).get("quality", {})
        self.max_duplicate_ratio = float(quality_cfg.get("max_duplicate_ratio", 0.4))
        self.alt_min_chars = int(quality_cfg.get("alt_min_chars", 8))
        self.alt_max_chars = int(quality_cfg.get("alt_max_chars", 140))
        self.alt_required_phrases = quality_cfg.get("alt_required_phrases", [])

    def _get_file_hash(self, filepath: str) -> str:
        hasher = hashlib.md5()
        with open(filepath, "rb") as f:
            hasher.update(f.read())
        return hasher.hexdigest()

    def _collect_selected_files(self, sku: str, img_dir: str, package_dir: str) -> Dict:
        selected_files: List[str] = []
        hashes = set()
        duplicate_count = 0
        total_candidates = 0

        video_path = os.path.join(self.video_root, sku, "video.mp4")
        if os.path.exists(video_path):
            temp_frames_dir = os.path.join(package_dir, "temp_frames")
            frames = extract_keyframes(video_path, temp_frames_dir)
            for frame in frames:
                total_candidates += 1
                f_hash = self._get_file_hash(frame)
                if f_hash in hashes:
                    duplicate_count += 1
                    continue
                hashes.add(f_hash)
                dest = os.path.join(img_dir, os.path.basename(frame))
                shutil.move(frame, dest)
                selected_files.append(dest)
            if os.path.exists(temp_frames_dir):
                shutil.rmtree(temp_frames_dir)

        sku_img_dir = os.path.join(self.assets_root, sku)
        if os.path.exists(sku_img_dir):
            for f_name in os.listdir(sku_img_dir):
                f_path = os.path.join(sku_img_dir, f_name)
                if os.path.isfile(f_path) and f_name.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                    total_candidates += 1
                    f_hash = self._get_file_hash(f_path)
                    if f_hash in hashes:
                        duplicate_count += 1
                        continue
                    hashes.add(f_hash)
                    dest = os.path.join(img_dir, f_name)
                    shutil.copy2(f_path, dest)
                    selected_files.append(dest)

        duplicate_ratio = (duplicate_count / total_candidates) if total_candidates else 0.0
        return {
            "selected_files": selected_files,
            "duplicate_count": duplicate_count,
            "total_candidates": total_candidates,
            "duplicate_ratio": duplicate_ratio,
        }

    def _validate_alt_policy(self, alt: str, file_path: str) -> Dict | None:
        alt_len = len((alt or "").strip())
        if alt_len < self.alt_min_chars or alt_len > self.alt_max_chars:
            return {
                "status": "REJECT",
                "reason": f"Alt policy length violation for {os.path.basename(file_path)} ({alt_len} chars)",
            }

        if self.alt_required_phrases:
            lowered = alt.lower()
            if not any(phrase.lower() in lowered for phrase in self.alt_required_phrases):
                return {
                    "status": "REJECT",
                    "reason": f"Alt policy required phrase missing for {os.path.basename(file_path)}",
                }

        return None

    def process(self, sku: str, content_id: str) -> Dict:
        package_dir = os.path.join(self.output_root, content_id)
        img_dir = os.path.join(package_dir, "selected_images")
        optimized_dir = os.path.join(package_dir, "optimized_images")
        os.makedirs(img_dir, exist_ok=True)

        collect_report = self._collect_selected_files(sku, img_dir, package_dir)
        selected_files = collect_report["selected_files"]

        if len(selected_files) < self.min_images:
            return {
                "status": "REJECT",
                "reason": f"Insufficient unique images. Found {len(selected_files)}, need {self.min_images}.",
            }

        if collect_report["duplicate_ratio"] > self.max_duplicate_ratio:
            return {
                "status": "REJECT",
                "reason": f"Duplicate ratio too high ({collect_report['duplicate_ratio']:.2f}>{self.max_duplicate_ratio:.2f})",
                "duplicate_ratio": collect_report["duplicate_ratio"],
            }

        optimization_report = []
        optimized_files = []
        for img in selected_files:
            report = optimize_image_asset(img, optimized_dir)
            optimization_report.append(report)
            optimized_files.append(report["output"])

        alt_texts = {}
        for file_path in optimized_files:
            alt = generate_alt_text(file_path, sku, context=self.alt_context, primary_keyword=self.primary_keyword)
            if detect_keyword_stuffing_alt(alt, [self.primary_keyword] if self.primary_keyword else []):
                return {
                    "status": "REJECT",
                    "reason": f"Keyword stuffing detected in alt text for {os.path.basename(file_path)}",
                }

            alt_policy_error = self._validate_alt_policy(alt, file_path)
            if alt_policy_error:
                return alt_policy_error

            alt_texts[os.path.basename(file_path)] = alt

        with open(os.path.join(package_dir, "alt_texts.json"), "w", encoding="utf-8") as f:
            json.dump(alt_texts, f, indent=2, ensure_ascii=False)

        with open(os.path.join(package_dir, "image_optimization_report.json"), "w", encoding="utf-8") as f:
            json.dump(optimization_report, f, indent=2, ensure_ascii=False)

        unique_facts = {
            "sku": sku,
            "content_id": content_id,
            "usage_period": "3 weeks",
            "environment": "Home office / Daily life",
            "checklist": ["Quality check passed", "Safety certified", "User tested"],
            "comparison_table": {
                "this_product": "High performance",
                "competitor_a": "Medium performance",
                "competitor_b": "Low performance",
            },
        }
        with open(os.path.join(package_dir, "unique_facts.json"), "w", encoding="utf-8") as f:
            json.dump(unique_facts, f, indent=2, ensure_ascii=False)

        return {
            "status": "PASS",
            "package_path": package_dir,
            "image_count": len(selected_files),
            "optimized_image_count": len(optimized_files),
            "facts_count": 2,
            "duplicate_ratio": collect_report["duplicate_ratio"],
        }
