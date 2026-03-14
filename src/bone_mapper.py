import bpy
import json
import os

def load_preset(preset_path: str) -> dict:
    """プリセットファイルからボーンマッピング辞書を読み込み"""
    if not preset_path or not os.path.exists(preset_path):
        return {}
    with open(preset_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def rename_bones(armature_obj, mapping: dict) -> list:
    """マッピング辞書に基づきボーンをリネーム。変更ログのリストを返す"""
    log = []
    
    bpy.context.view_layer.objects.active = armature_obj
    bpy.ops.object.mode_set(mode='EDIT')
    
    actual_mapping = {}
    for bone in armature_obj.data.edit_bones:
        if bone.name in mapping:
            old_name = bone.name
            new_name = mapping[old_name]
            bone.name = new_name
            actual_mapping[old_name] = new_name
            log.append(f"{old_name} -> {new_name}")
        else:
            log.append(bone.name)
    
    bpy.ops.object.mode_set(mode='OBJECT')

    # アニメーション（Action）のF-Curveパスを更新
    if actual_mapping:
        print(f"Updating animation paths for {len(actual_mapping)} bones...")
        for action in bpy.data.actions:
            for fcurve in action.fcurves:
                data_path = fcurve.data_path
                if data_path.startswith("pose.bones["):
                    # pose.bones["BoneName"].location -> ["pose.bones[", "BoneName", "].location"]
                    parts = data_path.split('"')
                    if len(parts) >= 3:
                        bone_name = parts[1]
                        if bone_name in actual_mapping:
                            new_bone_name = actual_mapping[bone_name]
                            fcurve.data_path = data_path.replace(f'"{bone_name}"', f'"{new_bone_name}"')

    return log

def save_analysis(log: list, output_path: str):
    """ボーン解析結果をファイルに出力"""
    if not output_path:
        return
        
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("FBX Bone Analysis Result\n")
        f.write("========================\n")
        for entry in sorted(log):
            f.write(f"- {entry}\n")
