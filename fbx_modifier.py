import sys
import os

try:
    import fbx
except ImportError:
    print("エラー: fbx モジュールが見つかりません。")
    print("Autodesk FBX SDK for Python がインストールされているか確認してください。")
    print("ダウンロード: https://aps.autodesk.com/developer/overview/fbx-sdk")
    sys.exit(1)

# テスト用ファイルのパス
INPUT_FBX = os.path.join(os.path.dirname(__file__), "testFBX", "female.fbx")
OUTPUT_FBX = os.path.join(os.path.dirname(__file__), "testFBX", "female_ue.fbx")
ANALYSIS_OUTPUT = os.path.join(os.path.dirname(__file__), "testFBX", "bone_analysis.txt")

# ==============================================================================
# ボーン名変換用の辞書定義
# 出力された bone_analysis.txt を確認し、ここの数字を書き換えてください。
# ==============================================================================
BONE_NAME_MAPPING = {
    # 例: "0": "root",
    # 例: "1": "pelvis",
}

def analyze_and_rename_nodes(node, depth, file_handle):
    if node is None:
        return

    current_name = node.GetName()
    node_type = node.GetTypeName()
    
    # ログファイルにノード情報を書き出し
    indent = "  " * depth
    file_handle.write(f"{indent}- [{node_type}] {current_name}\n")
    
    # ボーン名変換対象かチェック
    if current_name in BONE_NAME_MAPPING:
        new_name = BONE_NAME_MAPPING[current_name]
        print(f"  [変換] {current_name} -> {new_name}")
        node.SetName(new_name)

    # 子ノードを再帰的に処理
    for i in range(node.GetChildCount()):
        analyze_and_rename_nodes(node.GetChild(i), depth + 1, file_handle)

def main():
    if not os.path.exists(INPUT_FBX):
        print(f"エラー: 入力ファイルが見つかりません -> {INPUT_FBX}")
        return

    print(f"--- FBX処理ツール開始 ---")
    print(f"入力: {INPUT_FBX}")

    manager = fbx.FbxManager.Create()
    ios = fbx.FbxIOSettings.Create(manager, fbx.IOSROOT)
    manager.SetIOSettings(ios)

    importer = fbx.FbxImporter.Create(manager, "")
    if not importer.Initialize(INPUT_FBX, -1, manager.GetIOSettings()):
        print(f"インポート失敗: {importer.GetStatus().GetErrorString()}")
        return

    scene = fbx.FbxScene.Create(manager, "myScene")
    importer.Import(scene)
    importer.Destroy()

    # --- 1. スケールの分析と変換 (メートル -> センチメートル) ---
    system_unit = scene.GetGlobalSettings().GetSystemUnit()
    scale_factor = system_unit.GetScaleFactor()
    print(f"\n[スケール分析]")
    print(f"現在のスケールファクター: {scale_factor} (1.0=CM, 100.0=Meter 等)")
    
    # UE用 (センチメートル) に変換
    if scale_factor != 1.0:
        print("スケールを Unreal Engine 用 (センチメートル) に変換します...")
        fbx.FbxSystemUnit.cm.ConvertScene(scene)
        new_scale = scene.GetGlobalSettings().GetSystemUnit().GetScaleFactor()
        print(f"変換後のスケールファクター: {new_scale}")
    else:
        print("すでにセンチメートルスケールです。")

    # --- 2. ボーン階層の分析と名前の変換 ---
    print(f"\n[ノード階層分析とリネーム]")
    root_node = scene.GetRootNode()
    
    with open(ANALYSIS_OUTPUT, "w", encoding="utf-8") as f:
        f.write("FBX ノード階層分析結果\n")
        f.write("========================\n")
        if root_node:
            analyze_and_rename_nodes(root_node, 0, f)
            print(f"ノード階層を {ANALYSIS_OUTPUT} に出力しました。")
        else:
            print("ルートノードが見つかりません。")

    # --- 3. 出力 (UE向け調整済みFBX) ---
    print(f"\n[エクスポート]")
    exporter = fbx.FbxExporter.Create(manager, "")
    file_format = manager.GetIOPluginRegistry().GetNativeWriterFormat()
    
    if not exporter.Initialize(OUTPUT_FBX, file_format, manager.GetIOSettings()):
        print(f"エクスポート失敗: {exporter.GetStatus().GetErrorString()}")
        return

    exporter.Export(scene)
    exporter.Destroy()
    manager.Destroy()

    print(f"\n処理完了！")
    print(f"出力ファイル: {OUTPUT_FBX}")
    print(f"★ 次のステップ:")
    print(f"  1. {ANALYSIS_OUTPUT} を開いて、現在の数字のボーン名を確認してください。")
    print(f"  2. fbx_modifier.py 内の BONE_NAME_MAPPING に、数字と本来のボーン名（pelvis等）の対応を追記してください。")
    print(f"  3. スクリプトを再度実行すると、完璧なUE向けFBXが出力されます。")

if __name__ == "__main__":
    main()
