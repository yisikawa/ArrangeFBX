import bpy
import sys
import os
import math

# Blenderをバックグラウンドで実行し、FBXを再構築するスクリプト

# 手動マッピング（自動判定より優先されます）
BONE_NAME_MAPPING = {
    # 例: "Bone000": "root",
}

def get_script_dir():
    for arg in sys.argv:
        if arg.endswith('.py'):
            return os.path.dirname(os.path.abspath(arg))
    return os.getcwd()

def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    for col in [bpy.data.meshes, bpy.data.armatures, bpy.data.materials, bpy.data.images, bpy.data.actions]:
        for item in col:
            col.remove(item)

def guess_bone_mapping(armature_obj):
    """
    ボーンの階層構造と座標(左右)から、Unreal Engine標準ボーン名を推測してマッピングを生成する。
    """
    mapping = {}
    bones = armature_obj.data.bones
    
    # 1. ルートと骨盤の特定
    # 親がいないボーンをルートと仮定
    root_bones = [b for b in bones if b.parent is None]
    if not root_bones:
        return mapping
    
    root = root_bones[0]  # 通常は1つ
    if "root" not in root.name.lower():
        mapping[root.name] = "root"
    
    # ルートの最初の子を骨盤(pelvis)と仮定
    if len(root.children) > 0:
        pelvis = root.children[0]
        mapping[pelvis.name] = "pelvis"
        
        # 2. スパイン（背骨）の特定
        # 骨盤から上に伸びる直列のボーンを背骨とする
        current = pelvis
        spine_count = 1
        while len(current.children) > 0:
            # 最もZ軸(BlenderではYやZ)が上に向かっている、あるいは真ん中にある子を背骨とみなす
            # 簡易的に、子が複数ある場合はZが一番高いもの、またはXが0に近いものを選ぶなどのヒューリスティック
            center_children = [c for c in current.children if abs(c.head_local.x) < 0.05]
            if not center_children:
                 # 腕や脚の分岐に到達（胸/首回り）
                 break
                 
            # 最初のセンターボーンを次のスパインとする
            next_spine = center_children[0]
            
            # 首と頭の判定（背骨の先端付近）
            if len(next_spine.children) == 0:
                mapping[next_spine.name] = "head"
                # 一つ前を首に上書き
                if current.name in mapping and mapping[current.name].startswith("spine"):
                     mapping[current.name] = "neck_01"
                break
            elif len(next_spine.children) == 1 and abs(next_spine.children[0].head_local.x) < 0.05:
                 # まだ続く場合はスパイン
                 mapping[next_spine.name] = f"spine_{spine_count:02d}"
                 spine_count += 1
            else:
                 # 分岐がある場合は胸（clavicleの親）か首
                 mapping[next_spine.name] = "neck_01"
                 
            current = next_spine

        # 3. 腕と脚の特定（骨盤および胸からの分岐）
        for b in bones:
            # 既にマッピング済みはスキップ
            if b.name in mapping: continue
            
            # 親がマッピング済みか確認
            if not b.parent: continue
            
            # 脚の判定: 骨盤の子で、左右に分かれているもの
            if b.parent.name == pelvis.name and abs(b.head_local.x) > 0.01:
                side = "_l" if b.head_local.x > 0 else "_r" # BlenderのX軸は右がマイナスまたはプラス(要確認)
                # 一般的なX軸: 右が-X、左が+X (正面向きY-の時)
                side = "_l" if b.head_local.x > 0 else "_r"
                mapping[b.name] = f"thigh{side}"
                
                # 膝
                if len(b.children) > 0:
                    calf = b.children[0]
                    mapping[calf.name] = f"calf{side}"
                    # 足首
                    if len(calf.children) > 0:
                        foot = calf.children[0]
                        mapping[foot.name] = f"foot{side}"
                        
            # 腕の判定: 鎖骨周辺
            # 背骨の上のほう（neckの親など）から左右に伸びる
            parent_name_mapped = mapping.get(b.parent.name, "")
            if parent_name_mapped.startswith("spine") or parent_name_mapped.startswith("neck"):
                if abs(b.head_local.x) > 0.01:
                    side = "_l" if b.head_local.x > 0 else "_r"
                    mapping[b.name] = f"clavicle{side}"
                    
                    # 上腕
                    if len(b.children) > 0:
                        upperarm = b.children[0]
                        mapping[upperarm.name] = f"upperarm{side}"
                        # 前腕
                        if len(upperarm.children) > 0:
                            lowerarm = upperarm.children[0]
                            mapping[lowerarm.name] = f"lowerarm{side}"
                            # 手
                            if len(lowerarm.children) > 0:
                                hand = lowerarm.children[0]
                                mapping[hand.name] = f"hand{side}"

    return mapping

def main():
    script_dir = get_script_dir()
    INPUT_FBX = os.path.join(script_dir, "testFBX", "female.fbx")
    OUTPUT_FBX = os.path.join(script_dir, "testFBX", "female_ue.fbx")
    ANALYSIS_OUTPUT = os.path.join(script_dir, "testFBX", "bone_analysis.txt")

    if not os.path.exists(INPUT_FBX):
        print(f"ERROR: File not found {INPUT_FBX}")
        return

    print("--- FBX Processing Started (Blender) ---")
    
    # シーンクリア
    clear_scene()

    # FBXのインポート
    # Blenderは標準でメートル/センチメートルの解釈を適切に行います
    bpy.ops.import_scene.fbx(filepath=INPUT_FBX)

    # アーマチュア（ボーンの集合体）を探す
    armature_obj = None
    for obj in bpy.data.objects:
        if obj.type == 'ARMATURE':
            armature_obj = obj
            break

    if armature_obj is None:
        print("ERROR: No armature (bones) found in the FBX file.")
        return

    # 自動判定マッピングの生成
    guessed_mapping = guess_bone_mapping(armature_obj)
    
    # 手動マッピングで上書き（手動設定を優先）
    final_mapping = guessed_mapping.copy()
    final_mapping.update(BONE_NAME_MAPPING)

    # ボーンの解析とリネーム
    print("Analyzing and renaming bones...")
    bone_list = []
    
    # 編集のためにアームチュアを選択
    bpy.context.view_layer.objects.active = armature_obj
    bpy.ops.object.mode_set(mode='EDIT')
    
    for bone in armature_obj.data.edit_bones:
        current_name = bone.name
        
        # マッピング辞書に基づいてリネーム
        if current_name in final_mapping:
            new_name = final_mapping[current_name]
            bone.name = new_name
            bone_list.append(f"{current_name} -> {new_name}")
            print(f"Renamed: {current_name} -> {new_name}")
        else:
            bone_list.append(current_name)

    bpy.ops.object.mode_set(mode='OBJECT')

    # 解析結果の出力
    with open(ANALYSIS_OUTPUT, "w", encoding="utf-8") as f:
        f.write("FBX Bone Analysis Result\n")
        f.write("========================\n")
        for b_name in sorted(bone_list):
            f.write(f"- {b_name}\n")
    print(f"Analysis saved to {ANALYSIS_OUTPUT}")

    # FBXエクスポート (Unreal Engine用に最適化された設定)
    print("Exporting to Unreal Engine format...")
    bpy.ops.export_scene.fbx(
        filepath=OUTPUT_FBX,
        use_selection=False,
        global_scale=1.0,
        apply_scale_options='FBX_SCALE_ALL', # UE用のスケール適用
        axis_forward='-Z',
        axis_up='Y',
        bake_anim=True,
        bake_anim_use_all_bones=True,
        add_leaf_bones=False,
        mesh_smooth_type='FACE'
    )
    
    print(f"Finished! Saved to {OUTPUT_FBX}")

if __name__ == "__main__":
    main()
