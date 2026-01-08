@echo off
chcp 65001 > nul
echo ===================================
echo 画像からPDF作成
echo ===================================
echo.
echo dataフォルダ内の画像をPDFに変換します
echo.

python make_pdf.py

echo.
pause
