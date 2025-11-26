@echo off
title Educational Platform
color 0A

echo =======================================
echo   Educational Platform
echo   منصة تعليمية احترافية
echo =======================================
echo.

REM Check if venv exists
if not exist "venv" (
    echo [!] البيئة الافتراضية غير موجودة
    echo [*] جاري إنشائها...
    python -m venv venv
    echo [+] تم الإنشاء!
    echo.
)

REM Activate venv
call venv\Scripts\activate.bat

REM Check if .env exists
if not exist ".env" (
    echo [!] ملف .env غير موجود
    echo [*] جاري نسخه من .env.example...
    copy .env.example .env
    echo [+] تم النسخ!
    echo.
    echo [!] يرجى تعديل ملف .env وإضافة:
    echo     - TELEGRAM_BOT_TOKEN
    echo     - MONGODB_URL
    echo     - ADMIN_PASSWORD
    echo.
    notepad .env
    pause
)

REM Install requirements
echo [*] التحقق من المكتبات...
pip install -q -r requirements.txt --upgrade

echo.
echo =======================================
echo   اختر ما تريد تشغيله:
echo =======================================
echo   1. Telegram Bot فقط
echo   2. Admin Dashboard فقط
echo   3. كلاهما (Bot + Dashboard)
echo =======================================
echo.

set /p choice="اختيارك (1/2/3): "

if "%choice%"=="1" (
    echo.
    echo [*] تشغيل Telegram Bot...
    python bot/main.py
) else if "%choice%"=="2" (
    echo.
    echo [*] تشغيل Admin Dashboard...
    echo [+] Dashboard: http://localhost:8000
    python admin_dashboard/app.py
) else if "%choice%"=="3" (
    echo.
    echo [*] تشغيل كلاهما...
    echo [+] Bot: يعمل في الخلفية
    echo [+] Dashboard: http://localhost:8000
    echo.
    start /B python bot/main.py
    python admin_dashboard/app.py
) else (
    echo [!] اختيار غير صحيح
    pause
)

pause
