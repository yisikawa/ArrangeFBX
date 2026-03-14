# FBXアニメーション複数出力対応の修正案

FBXエクスポート時に、モデルに含まれるすべてのアニメーション（アクション）が出力されるようにし、さらにボーンリネームに伴うアニメーションの破損を防止するための修正案です。

## 修正のポイント

1. **エクスポート設定の追加**: 
   BlenderのFBXエクスポート設定で `bake_anim_use_all_actions=True` を明示的に指定します。
2. **アニメーションデータのパス修正**: 
   ボーン名をリネームした際、すべてのアニメーション（Action）内のF-Curveパスを新しい名前に更新します。これを怠ると、リネーム後にアニメーションが動作しなくなります。
3. **設定値の反映**: 
   `src/config.py` および `config.json` にアニメーション関連の制御フラグを追加します。

## 実施手順（適用済み）

### 1. `src/fbx_io.py` の修正
エクスポートオプションに「全アクションの出力」を追加しました。

```python:src/fbx_io.py
def export_fbx(filepath: str, settings: dict):
    """FBXファイルをエクスポート"""
    bpy.ops.export_scene.fbx(
        filepath=filepath,
        use_selection=False,
        # ... 略 ...
        bake_anim=settings.get("bake_anim", True),
        bake_anim_use_all_bones=settings.get("bake_anim_use_all_bones", True),
        bake_anim_use_nla_strips=settings.get("bake_anim_use_nla_strips", True),    # 追加
        bake_anim_use_all_actions=settings.get("bake_anim_use_all_actions", True), # 追加: 全アクション出力
        # ... 略 ...
    )
```

### 2. `src/bone_mapper.py` の修正
ボーン名を変更した際、アクション内のF-Curveパス（`pose.bones["旧名"]...`）を「新名」に書き換える処理を追加しました。

```python:src/bone_mapper.py
def rename_bones(armature_obj, mapping: dict) -> list:
    """マッピング辞書に基づきボーンをリネームし、アニメーションパスも更新"""
    # ... ボーンリネーム処理 ...
    
    # アニメーション（Action）のF-Curveパスを更新
    if actual_mapping:
        print(f"Updating animation paths for {len(actual_mapping)} bones...")
        for action in bpy.data.actions:
            for fcurve in action.fcurves:
                data_path = fcurve.data_path
                if data_path.startswith("pose.bones["):
                    parts = data_path.split('"')
                    if len(parts) >= 3:
                        bone_name = parts[1]
                        if bone_name in actual_mapping:
                            new_bone_name = actual_mapping[bone_name]
                            fcurve.data_path = data_path.replace(f'"{bone_name}"', f'"{new_bone_name}"')
    return log
```

### 3. `src/config.py` の修正
デフォルト設定にアニメーション関連のフラグを追加しました。

```python:src/config.py
    DEFAULT_CONFIG = {
        # ... 略 ...
        "export": {
            "global_scale": 1.0, 
            # ... 略 ...
            "bake_anim": True, 
            "bake_anim_use_all_bones": True,
            "bake_anim_use_nla_strips": True,
            "bake_anim_use_all_actions": True,
            "add_leaf_bones": False, 
            "mesh_smooth_type": "FACE"
        }
    }
```

## 期待される効果
- インポートされたモデルに含まれる複数のアニメーションがすべて出力されるようになります。
- ボーン名を変更（例：数字からUE5マネキン名へ）しても、アニメーションが正しくターゲットボーンに適用された状態でエクスポートされます。
