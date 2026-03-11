import json
import os

class Config:
    """設定ファイルの読み込みと管理"""
    
    DEFAULT_CONFIG = {
        "input": {"fbx_path": "", "use_custom_normals": False},
        "output": {"fbx_path": "", "analysis_path": "", "format": "fbx_binary"},
        "bone_mapping": {"preset": "", "auto_guess_enabled": True, "side_detection_threshold": 0.05},
        "subdivision": {"level": 0, "apply_to_all_meshes": True, "merge_threshold": 0.0001},
        "export": {
            "global_scale": 1.0, "scale_options": "FBX_SCALE_ALL",
            "axis_forward": "-Z", "axis_up": "Y",
            "bake_anim": True, "add_leaf_bones": False, "mesh_smooth_type": "FACE"
        }
    }
    
    def __init__(self, config_path: str, base_dir: str = ""):
        self.base_dir = base_dir
        self._data = self.DEFAULT_CONFIG.copy()
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
                self._deep_update(self._data, user_config)
    
    def _deep_update(self, base: dict, update: dict):
        """ネストされた辞書を再帰的にマージ"""
        for key, val in update.items():
            if isinstance(val, dict) and key in base:
                self._deep_update(base[key], val)
            else:
                base[key] = val
    
    def override_input(self, fbx_path: str):
        self._data["input"]["fbx_path"] = fbx_path
        
    def override_output(self, fbx_path: str):
        self._data["output"]["fbx_path"] = fbx_path
    
    @property
    def input_path(self) -> str:
        return os.path.abspath(os.path.join(self.base_dir, self._data["input"]["fbx_path"])) if self._data["input"]["fbx_path"] else ""
    
    @property
    def use_custom_normals(self) -> bool:
        return self._data["input"]["use_custom_normals"]
        
    @property
    def output_path(self) -> str:
        return os.path.abspath(os.path.join(self.base_dir, self._data["output"]["fbx_path"])) if self._data["output"]["fbx_path"] else ""
        
    @property
    def analysis_path(self) -> str:
        return os.path.abspath(os.path.join(self.base_dir, self._data["output"]["analysis_path"])) if self._data["output"]["analysis_path"] else ""
        
    @property
    def preset_path(self) -> str:
        return os.path.abspath(os.path.join(self.base_dir, self._data["bone_mapping"]["preset"])) if self._data["bone_mapping"]["preset"] else ""
        
    @property
    def auto_guess_enabled(self) -> bool:
        return self._data["bone_mapping"]["auto_guess_enabled"]
        
    @property
    def side_threshold(self) -> float:
        return self._data["bone_mapping"]["side_detection_threshold"]
    
    @property
    def subdivision_level(self) -> int:
        return self._data["subdivision"]["level"]
        
    @property
    def apply_to_all_meshes(self) -> bool:
        return self._data["subdivision"]["apply_to_all_meshes"]
    
    @property
    def merge_threshold(self) -> float:
        return self._data["subdivision"]["merge_threshold"]
    
    @property
    def export_settings(self) -> dict:
        return self._data["export"]
