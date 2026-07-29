@echo off
echo BulutIs Windows EXE Derleme Baslatiliyor...
pip install -r requirements.txt
pyinstaller --clean app.spec
echo.
echo Derleme Tamamlandi! dist/BulutIs.exe dosyasini calistirabilirsiniz.
pause
