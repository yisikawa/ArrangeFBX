# ArrangeFBX (Blender Modifier Prototype)

提供されたFBXモデル（例: `testFBX/female.fbx`）をロードし、以下の自動調整を行ってUnreal Engine向けに出力するBlender用Pythonスクリプトです。

### 主な機能
1. **スケール変換**：Blenderのエクスポート機能を用いて、Unreal Engine標準のセンチメートル単位へのスケール適用を行います。
2. **ノード階層分析とボーン名の置換**：FBX内の全ボーン階層を解析します。自動推測や手動マッピング(`BONE_NAME_MAPPING`)を用いて、数字だけのボーン名をUE標準のマネキンボーン名（pelvis, spine_01 等）に変換可能です。解析結果は `testFBX/bone_analysis.txt` にリスト化されます。
3. **メッシュの細分化 (Subdivision)**: `config.json` の設定に基づき、エクスポート前にメッシュを自動で細分化し、より滑らかなモデルを生成できます。
4. **出力**：ボーンのリネームやメッシュの細分化を行った結果を `testFBX/female_ue.fbx` として出力します。

### 実行準備 (Blenderのインストール)
※実行には **Blender 3.x または 4.x** がインストールされている必要があります。
Blenderの実行ファイル（`blender.exe`）にパスが通っているか、あるいはフルパスを指定して実行してください。

### 設定ファイル (`config.json`) の使い方
スクリプト実行時、同じディレクトリにある `config.json` を読み込みます。
```json
{
    "subdivision_level": 1,
    "apply_subdivision_to_all_meshes": true
}
```
* **`subdivision_level`**: 何段階でメッシュを細分化（サブディビジョン）するかを指定します。
  * `0`: 細分化を行わず、元のメッシュのまま出力します。
  * `1`: 1度細分化します（ポリゴン数が増加し、滑らかなシルエットになります）。
  * `2`以上: さらに細分化しますが、ファイルサイズが急増するため注意してください。

### 実行手順

1. コマンドプロンプトまたはPowerShellでこのフォルダに移動します。
2. Blenderをバックグラウンドで起動し、スクリプトを実行します（お使いの環境に合わせてBlenderのパスを指定してください）：
   ```powershell
   # 例: Blender 4.3 がデフォルトの場所にインストールされている場合
   & "C:\Program Files\Blender Foundation\Blender 4.3\blender.exe" --background --python blender_fbx_modifier.py
   ```
3. スクリプトが完了すると、`testFBX/female_ue.fbx` が生成されます。また `testFBX/bone_analysis.txt` に元のボーンとリネーム結果の一覧が出力されます。
4. ボーン名の手動対応が必要な場合は、`blender_fbx_modifier.py` をエディタで開き、上部にある `BONE_NAME_MAPPING` 辞書に元の名前とUE用ボーン名の対応表を追記して、再度実行してください。
