@echo off
chcp 65001 > nul
echo =============================================
echo  ArrangeFBX - FBX自動処理とアップスケールツール
echo =============================================
echo.

:: 1. PowerShellでファイル選択ダイアログを起動
echo [1/2] 処理対象のFBXファイルを選択してください...
set "INPUT_FBX="
for /f "usebackq tokens=*" %%i in (`powershell -Command "Add-Type -AssemblyName System.Windows.Forms; $f = New-Object System.Windows.Forms.OpenFileDialog; $f.Filter = 'FBX Files (*.fbx)|*.fbx|All Files (*.*)|*.*'; $f.Title = '処理対象のFBXファイルを選択してください'; if ($f.ShowDialog() -eq 'OK') { Write-Output $f.FileName }"`) do set "INPUT_FBX=%%i"

:: キャンセル判定
if "%INPUT_FBX%"=="" (
    echo.
    echo [キャンセル] ファイルが選択されませんでした。処理を終了します。
    echo.
    pause
    exit /b
)

echo.
echo 選択されたファイル: "%INPUT_FBX%"
echo.

:: 2. 出力ファイル名の決定 (入力名の末尾に _ue を付加)
for %%F in ("%INPUT_FBX%") do (
    set "OUTPUT_FBX=%%~dpnF_ue.fbx"
)

:: 3. Blenderのパス設定
:: 環境に合わせてパスを調整してください
set "BLENDER_PATH=C:\Program Files\Blender Foundation\Blender 4.4\blender.exe"

:: 4. Blenderスクリプトを実行
echo [2/2] BlenderでFBXの構造変換を実行中...
echo 入力: "%INPUT_FBX%"
echo 出力: "%OUTPUT_FBX%"
echo.
"%BLENDER_PATH%" --background --python "%~dp0blender_run.py" -- -i "%INPUT_FBX%" -o "%OUTPUT_FBX%"

echo.
echo =============================================
echo 処理が完了しました！
echo =============================================
pause
