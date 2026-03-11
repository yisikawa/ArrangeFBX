import bpy
import sys
import os

def get_script_dir():
    for arg in sys.argv:
        if arg.endswith('.py'):
            return os.path.dirname(os.path.abspath(arg))
    return os.getcwd()

def setup_paths():
    """src/ をインポートパスに追加"""
    script_dir = get_script_dir()
    src_dir = os.path.join(script_dir, "src")
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)
    return script_dir

def patch_blender_compat():
    """Blender 4.1+の互換性パッチ"""
    for attr in ['create_normals_split', 'calc_normals_split', 'free_normals_split']:
        if not hasattr(bpy.types.Mesh, attr):
            setattr(bpy.types.Mesh, attr, lambda self: None)

def parse_cli_args() -> dict:
    """Blender実行時の -- 以降のCLI引数を解析"""
    result = {}
    argv = sys.argv
    if "--" in argv:
        custom_args = argv[argv.index("--") + 1:]
        i = 0
        while i < len(custom_args):
            if custom_args[i] in ("-i", "--input") and i + 1 < len(custom_args):
                result["input"] = custom_args[i + 1]
                i += 2
            elif custom_args[i] in ("-o", "--output") and i + 1 < len(custom_args):
                result["output"] = custom_args[i + 1]
                i += 2
            elif custom_args[i] == "--dry-run":
                result["dry_run"] = True
                i += 1
            else:
                i += 1
    return result

def main():
    script_dir = setup_paths()
    
    from config import Config
    from fbx_io import clear_scene, import_fbx, find_armature, export_fbx
    from bone_guesser import BoneGuesser
    from bone_mapper import load_preset, rename_bones, save_analysis
    from subdivision import merge_by_distance, apply_subdivision
    
    # 設定読み込み
    config_path = os.path.join(script_dir, "config.json")
    config = Config(config_path, base_dir=script_dir)
    
    # CLI引数の上書き処理
    args = parse_cli_args()
    if args.get("input"):
        config.override_input(args["input"])
    if args.get("output"):
        config.override_output(args["output"])
    
    patch_blender_compat()
    
    # バリデーション
    if not os.path.exists(config.input_path):
        print(f"ERROR: 入力ファイルが見つかりません -> {config.input_path}")
        return

    print("--- FBX Processing Started (Blender) ---")
    
    # 1. シーンクリア & インポート
    print(f"Importing: {config.input_path}")
    clear_scene()
    import_fbx(config.input_path, config.use_custom_normals)
    
    # 2. アーマチュア検索
    armature = find_armature()
    if armature is None:
        print("ERROR: アーマチュアが見つかりません")
        return
    
    # 3. ボーンマッピング（自動推測 + プリセット上書き）
    mapping = {}
    if config.auto_guess_enabled:
        print("Guessing bone mapping...")
        guesser = BoneGuesser(armature, config.side_threshold)
        mapping = guesser.guess()
    
    if config.preset_path and os.path.exists(config.preset_path):
        print(f"Loading preset: {config.preset_path}")
        preset = load_preset(config.preset_path)
        mapping.update(preset)  # プリセットで上書き
    
    # 4. ボーンリネーム & 解析出力
    print("Renaming bones...")
    log = rename_bones(armature, mapping)
    save_analysis(log, config.analysis_path)
    
    if args.get("dry_run"):
        print("Dry run finished. Exiting without export.")
        return
        
    # 5. 近傍点の統合（サブディビジョン前に実行）
    merge_threshold = config.merge_threshold
    if merge_threshold > 0:
        print(f"Merging vertices by distance (threshold={merge_threshold})...")
        merge_by_distance(merge_threshold)
    
    # 6. サブディビジョン
    print(f"Applying subdivision (level={config.subdivision_level})...")
    apply_subdivision(config.subdivision_level, config.apply_to_all_meshes)
    
    # 7. エクスポート
    print(f"Exporting to: {config.output_path}")
    
    # 出力先ディレクトリの作成
    if config.output_path:
        os.makedirs(os.path.dirname(config.output_path), exist_ok=True)
        
    export_fbx(config.output_path, config.export_settings)
    
    print("Finished successfully.")

if __name__ == "__main__":
    main()
