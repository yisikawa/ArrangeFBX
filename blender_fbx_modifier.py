import bpy
import sys
import os
import math
import json
import base64
import urllib.request
import urllib.error
import argparse

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

def upscale_image_with_gemini(image_path, factor, seamless):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set. Skipping upscale.")
        return None

    print(f"Upscaling texture: {os.path.basename(image_path)} (Factor: {factor}x, Seamless: {seamless})")
    
    # 画像をBase64エンコード
    try:
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        print(f"Error reading image {image_path}: {e}")
        return None

    # 画像のMIME形式を取得
    ext = os.path.splitext(image_path)[1].lower()
    mime_type = "image/jpeg" if ext in ['.jpg', '.jpeg'] else "image/png" if ext == '.png' else "image/png"

    # Gemini API エンドポイント (gemini-3.1-flash または適当なモデルを指定)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro-vision:generateContent?key={api_key}"
    
    # 最新の Gemini モデルは画像生成/編集(upscale) に対応していると仮定したリクエストボディ
    # ※ 注意: 現在の標準的な Gemini 1.5/2.0 Pro/Flash はテキスト/画像「入力」特化であり、
    # 画像「出力(生成・編集)」を行うには imagen-3.0-generate 等の別API（Vertex AI等）を使用するのが一般的です。
    # ここでは仕様に基づき、仮想的な Image Editing/Upscale API のリクエスト構造を定義しています。
    # 実際の Nano Banana / Image API の仕様に合わせて適宜調整してください。
    prompt_text = f"Upscale this texture by {factor}x. Maintain original aspect ratio and details."
    if seamless:
        prompt_text += " Ensure the resulting image is perfectly seamless/tileable for 3D PBR materials."

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt_text},
                    {
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": encoded_string
                        }
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.2 # 変換の場合は低め
        }
    }

    headers = {'Content-Type': 'application/json'}
    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')

    try:
        response = urllib.request.urlopen(req)
        response_data = json.loads(response.read().decode('utf-8'))
        
        # ※ ここはレスポンス仕様に依存します。画像がBase64文字列で `responseData.image` のように返ってくると仮定します。
        # Gemini API の標準的なレスポンスではテキストしか返らないため、
        # もしテキストで解説文が返ってきた場合はアップスケール失敗となります。
        result_text = response_data.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')
        print("API Response:", result_text[:100], "...")
        
        # 実際には画像を返すAPIエンドポイント（Imagen等）を使用する必要があります。
        # ここでは実装デモとして、元の画像をコピーして「_upscaled」として保存するダミー処理を行います。
        # （本来は取得したBase64文字列をデコードして保存します）
        
        # ---- ダミー実装（コピー） ----
        base_dir = os.path.dirname(image_path)
        base_name, ext = os.path.splitext(os.path.basename(image_path))
        new_image_name = f"{base_name}_upscaled{ext}"
        new_image_path = os.path.join(base_dir, new_image_name)
        
        # shutil は上部で import する必要があります。この関数内でのみ使用するためここでimport
        import shutil
        shutil.copy2(image_path, new_image_path)
        print(f"Saved upscaled texture to: {new_image_path} (Dummy implementation)")
        return new_image_path
        # -----------------------------
        
    except urllib.error.URLError as e:
        print(f"API Request Error: {e}")
        if hasattr(e, 'read'):
            print(e.read().decode('utf-8'))
        return None
    except Exception as e:
        print(f"Unexpected Error during upscale: {e}")
        return None

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
    
    # 引数のパース (blender自身の引数と分けるため、 '--' 以降を取得)
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = []

    parser = argparse.ArgumentParser(description="ArrangeFBX")
    parser.add_argument("--input", type=str, help="Input FBX file path")
    parser.add_argument("--output", type=str, help="Output FBX file path (Optional)")
    args, _ = parser.parse_known_args(argv)

    if args.input:
        INPUT_FBX = args.input
        if args.output:
            OUTPUT_FBX = args.output
        else:
            base_path, ext = os.path.splitext(INPUT_FBX)
            OUTPUT_FBX = f"{base_path}_ue{ext}"
        ANALYSIS_OUTPUT = os.path.join(os.path.dirname(INPUT_FBX), "bone_analysis.txt")
    else:
        # 引数がない場合は従来の動作（テスト用）
        INPUT_FBX = os.path.join(script_dir, "testFBX", "female.fbx")
        OUTPUT_FBX = os.path.join(script_dir, "testFBX", "female_ue.fbx")
        ANALYSIS_OUTPUT = os.path.join(script_dir, "testFBX", "bone_analysis.txt")

    CONFIG_FILE = os.path.join(script_dir, "config.json")

    # config.json の読み込み
    subdivision_level = 0
    apply_to_all_meshes = True
    merge_vertices = True
    merge_distance = 0.0001
    upscale_textures = False
    upscale_factor = 2
    upscale_seamless = True

    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                subdivision_level = config_data.get("subdivision_level", 0)
                apply_to_all_meshes = config_data.get("apply_subdivision_to_all_meshes", True)
                merge_vertices = config_data.get("merge_vertices", True)
                merge_distance = config_data.get("merge_distance", 0.0001)
                upscale_textures = config_data.get("upscale_textures", False)
                upscale_factor = config_data.get("upscale_factor", 2)
                upscale_seamless = config_data.get("upscale_seamless", True)
            print(f"Loaded config: sub_level={subdivision_level}, merge={merge_vertices}, upscale={upscale_textures}")
        except Exception as e:
            print(f"Warning: Failed to load config.json: {e}")

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

    # 重複頂点の結合 (マージ) - 細分化前処理
    if merge_vertices:
        print(f"Merging duplicate vertices (Distance: {merge_distance})...")
        bpy.ops.object.select_all(action='DESELECT')
        for obj in bpy.data.objects:
            if obj.type == 'MESH':
                bpy.context.view_layer.objects.active = obj
                obj.select_set(True)
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_all(action='SELECT')
                # 距離でマージ (Remove Doubles)
                bpy.ops.mesh.remove_doubles(threshold=merge_distance)
                bpy.ops.object.mode_set(mode='OBJECT')
                obj.select_set(False)

    # テクスチャのアップスケール処理
    if upscale_textures:
        print("Starting Texture Upscale Process...")
        # 処理済み画像の記録（重複実行を避けるため）
        processed_images = {}
        
        for mat in bpy.data.materials:
            if not mat.use_nodes:
                continue
                
            for node in mat.node_tree.nodes:
                # プリンシプルBSDFのBaseColorに繋がっているImage Textureなどを探す
                if node.type == 'TEX_IMAGE' and node.image:
                    # とりあえず全ての画像テクスチャを対象にするか、Base Colorのみに絞るか
                    # 这里では安全のため、ファイル名に 'norm', 'rough' 等が含まれないか簡易チェック
                    img_name = node.image.name.lower()
                    if 'norm' in img_name or 'rough' in img_name:
                        print(f"Skipping Normal/Roughness map: {node.image.name}")
                        continue
                        
                    img_path = bpy.path.abspath(node.image.filepath)
                    if not os.path.exists(img_path):
                        print(f"Image not found on disk: {img_path}")
                        continue
                        
                    if img_path in processed_images:
                        # 既に処理済みの場合はパスを差し替えるだけ
                        new_img_path = processed_images[img_path]
                        if new_img_path:
                            # Blender内に新しい画像をロードして差し替え
                            new_img = bpy.data.images.load(new_img_path)
                            node.image = new_img
                        continue

                    # APIでアップスケール実行
                    new_img_path = upscale_image_with_gemini(img_path, upscale_factor, upscale_seamless)
                    processed_images[img_path] = new_img_path
                    
                    if new_img_path:
                        # Blender内に新しい画像をロードして差し替え
                        new_img = bpy.data.images.load(new_img_path)
                        node.image = new_img
                        print(f"Applied upscaled texture to material: {mat.name}")

    # メッシュの細分化処理(Subdivision)
    if subdivision_level > 0:
        print(f"Applying Subdivision Surface (Level: {subdivision_level})...")
        for obj in bpy.data.objects:
            if obj.type == 'MESH':
                # モディファイアを追加
                subsurf = obj.modifiers.new(name="Subdivision", type='SUBSURF')
                subsurf.levels = subdivision_level
                subsurf.render_levels = subdivision_level

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
