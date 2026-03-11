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
    
    for bone in armature_obj.data.edit_bones:
        if bone.name in mapping:
            old_name = bone.name
            new_name = mapping[old_name]
            bone.name = new_name
            log.append(f"{old_name} -> {new_name}")
        else:
            log.append(bone.name)
    
    bpy.ops.object.mode_set(mode='OBJECT')
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
