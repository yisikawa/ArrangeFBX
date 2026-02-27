# FBX Modifier Prototype (Unreal Engine向け)

提供された `testFBX/female.fbx` をロードし、以下の自動調整を行うPythonスクリプトです。

### 主な機能
1. **スケール変換**：メートル単位のモデルを、Unreal Engine標準のセンチメートル単位へ変換。
2. **ノード階層分析**：FBX内の全ボーン階層を解析し、`testFBX/bone_analysis.txt` にリスト化。
3. **ボーン名の置換**：数字だけのボーン名を、UE標準のマネキンボーン名（pelvis, spine_01 等）に変換可能。
4. **出力**：調整済みの結果を `testFBX/female_ue.fbx` として出力。

### 実行準備 (FBX SDKのインストール)
※Python環境にAutodeskのFBX SDKが必要です。
Windowsの場合は標準の `pip install fbx` ではインストールできないため、以下の公式ページからダウンロードしてインストールしてください。

1. [Autodesk FBX SDK for Python ダウンロードページ](https://aps.autodesk.com/developer/overview/fbx-sdk)
2. `FBX Python Bindings` をダウンロードして、環境にインストールしてください。

### 実行手順

1. コマンドプロンプトまたはPowerShellでこのフォルダに移動します。
2. スクリプトを実行します：
   ```bash
   python fbx_modifier.py
   ```
3. スクリプトが完了すると、`testFBX/bone_analysis.txt` が生成されます。
4. そのテキストファイルを開き、**「どの数字がどのボーン（頭、腕、足など）に対応するか」**を確認してください。
5. `fbx_modifier.py` をエディタで開き、上部にある `BONE_NAME_MAPPING` 辞書に数字と名前の対応表を書き込んで保存します。
6. もう一度 `python fbx_modifier.py` を実行すると、ボーン名が変換された完全な `female_ue.fbx` が生成されます！これをそのままUnreal Engineにインポートすることで、正しく動作します。
