# ArrangeFBX (Blender Modifier Prototype)

提供されたFBXモデル（例: `testFBX/female.fbx`）をロードし、以下の自動調整を行ってUnreal Engine向けに出力するBlender用Pythonスクリプトです。

### 主な機能
1. **スケール変換**：Blenderのエクスポート機能を用いて、Unreal Engine標準のセンチメートル単位へのスケール適用を行います。
2. **ノード階層分析とボーン名の置換**：FBX内の全ボーン階層を解析します。自動推論システムにより、数字のみのボーン名などをUE標準のマネキンボーン名（pelvis, spine_01 等）に自動でマッピング・変換します。また、必要に応じて `presets/ue5_mannequin.json` 等で定義した手動マッピングで上書き可能です。解析結果は `testFBX/bone_analysis.txt` にリスト化されます。
3. **メッシュの細分化 (Subdivision)**: `config.json` の設定に基づき、エクスポート前にメッシュを自動で細分化し、より滑らかなモデルを生成できます。
4. **頂点結合**: サブディビジョン前に近傍頂点を統合することで、メッシュの縮退や穴あきを防止します。
5. **出力**：ボーンのリネームやメッシュの細分化を行った結果を指定されたFBXとして出力します。

### 実行準備 (Blenderのインストール)
※実行には **Blender 3.x または 4.x** がインストールされている必要があります。
Blenderの実行ファイル（`blender.exe`）にパスが通っているか、あるいはフルパスを指定して実行してください。

### ディレクトリ構成
```
ArrangeFBX/
├── blender_run.py           # Blender用実行スクリプト（メイン）
├── src/                     # Pythonモジュール（設定、ボーン処理、IO等）
├── config.json              # 基本設定ファイル
├── presets/                 # ボーンの手動マッピング辞書ファイル置き場
└── testFBX/                 # FBXデータ・解析結果
```

### 設定ファイル (`config.json`) の使い方
`config.json` を編集することで、入力・出力パスや各処理のパラメータを制御できます。
以下に全セクションの詳細を記載します。

#### `input` — 入力設定
| キー | 型 | デフォルト | 説明 |
|------|----|-----------|------|
| `fbx_path` | string | `""` | 入力FBXファイルのパス（スクリプトのディレクトリからの相対パス）。 |
| `use_custom_normals` | bool | `true` | `true` にすると、FBXに含まれるカスタム法線を保持します。メッシュの見た目を崩さないために `true` 推奨です。 |

#### `output` — 出力設定
| キー | 型 | デフォルト | 説明 |
|------|----|-----------|------|
| `fbx_path` | string | `""` | 出力FBXファイルのパス。 |
| `analysis_path` | string | `""` | ボーン解析結果テキストの出力先パス。 |
| `format` | string | `"fbx_binary"` | 出力フォーマット（現在は `fbx_binary` のみ対応）。 |

#### `bone_mapping` — ボーンマッピング設定
| キー | 型 | デフォルト | 説明 |
|------|----|-----------|------|
| `preset` | string | `""` | 手動マッピング用のJSONファイルパス（例: `presets/ue5_mannequin.json`）。自動推測結果を上書きします。 |
| `auto_guess_enabled` | bool | `true` | `true` でボーン名の自動推測を有効化。無効にすると手動プリセットのみ使用されます。 |
| `side_detection_threshold` | float | `0.05` | ボーンがセンターライン上にあるかを判定するX座標の閾値（メートル単位）。値を大きくすると、より広い範囲をセンターとみなします。 |

#### `subdivision` — メッシュ細分化設定
| キー | 型 | デフォルト | 説明 |
|------|----|-----------|------|
| `merge_threshold` | float | `0.0001` | 近傍頂点を統合する際の距離閾値。サブディビジョン時のメッシュ縮退を防ぐために重要です。 |
| `level` | int | `0` | サブディビジョンレベル。`0` = 細分化なし、`1` = 1段階（推奨）、`2`以上 = ファイルサイズが増えるため注意。 |
| `apply_to_all_meshes` | bool | `true` | `true` で全メッシュに適用。`false` で最初のメッシュのみに適用。 |

#### `texture` — テクスチャ関連設定（試験的な実装を含む）
| キー | 型 | デフォルト | 説明 |
|------|----|-----------|------|
| `scale_factor` | float | `4.0` | テクスチャのスケールファクター。 |
| `resize_interpolation` | string | `"bicubic"` | リサイズ時の補間方法。 |
| `use_bilateral_filter` | bool | `true` | バイラテラルフィルタ適用の有無。 |

#### `export` — FBXエクスポート設定
Blenderの `bpy.ops.export_scene.fbx` に渡されるパラメータです。

| キー | 型 | デフォルト | 説明 |
|------|----|-----------|------|
| `global_scale` | float | `1.0` | グローバルスケール倍率。 |
| `scale_options` | string | `"FBX_SCALE_ALL"` | スケール適用方法（UE推奨は `"FBX_SCALE_ALL"`）。 |
| `axis_forward` | string | `"-Z"` | 前方軸（UE標準は `"-Z"`）。 |
| `axis_up` | string | `"Y"` | 上方軸（UE標準は `"Y"`）。 |
| `bake_anim` | bool | `true` | アニメーションをベイクするかどうか。 |
| `add_leaf_bones` | bool | `false` | リーフボーンを付加するかどうか（UEは `false` 推奨）。 |
| `mesh_smooth_type` | string | `"FACE"` | スムージング情報の種類（UE推奨は `"FACE"`）。 |

---

### 実行手順

#### 方法A: バッチファイルを利用する（おすすめ）
同梱のバッチファイルを利用すると、ファイルのパスを意識せずにGUIから直感的に処理を実行できます。

1. **`run_arrange_fbx.bat`** をダブルクリックして実行します。
2. ファイル選択ダイアログが表示されるので、処理を行いたい `.fbx` ファイルを選択します。
3. 自動的にBlenderがバックグラウンドで起動し、処理が進行します。
4. 処理が完了すると、元のファイルと同じ場所に `_ue` がファイル名に付加された完成版FBXが出力されます。

#### 方法B: コマンドラインから実行する
1. コマンドプロンプトまたはPowerShellでこのフォルダに移動します。
2. Blenderを起動し、スクリプトを実行します（Blenderのパスはお使いの環境に合わせて調整してください）：

**基本実行:**
```powershell
& "C:\Program Files\Blender Foundation\Blender 4.3\blender.exe" --background --python blender_run.py
```

**CLI引数を用いた上書き実行:**
```powershell
# 入出力ファイルを指定
& "C:\Program Files\Blender Foundation\Blender 4.3\blender.exe" --background --python blender_run.py -- -i my_model.fbx -o my_model_ue.fbx

# 解析のみ（エクスポートなし）
& "C:\Program Files\Blender Foundation\Blender 4.3\blender.exe" --background --python blender_run.py -- --dry-run
```
