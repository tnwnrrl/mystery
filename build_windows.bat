@echo off
REM Windows용 실행파일 빌드 스크립트

echo ====================================================
echo Canon 100D 사진 처리 프로그램 빌드 시작 (Windows)
echo ====================================================
echo.

REM 가상환경 활성화
call venv\Scripts\activate.bat

REM 기존 빌드 정리
echo 기존 빌드 파일 정리...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM PyInstaller로 빌드
echo.
echo 실행파일 생성 중...
pyinstaller build_windows.spec --clean

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ====================================================
    echo ✅ 빌드 성공!
    echo ====================================================
    echo 📂 실행 파일 위치: dist\Canon100D.exe
    echo.
    echo 사용 방법:
    echo 1. dist\Canon100D.exe를 원하는 위치로 복사
    echo 2. Canon100D.exe를 더블클릭하여 실행
    echo.
    echo ⚠️  필수 사항:
    echo    - libgphoto2 Windows 버전 설치 필요
    echo    - 카메라 드라이버 설치 필요
    echo.
) else (
    echo.
    echo ❌ 빌드 실패
    echo 오류 로그를 확인하세요
    exit /b 1
)

pause
