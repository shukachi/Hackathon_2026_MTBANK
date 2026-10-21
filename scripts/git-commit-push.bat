@echo off
REM git-commit-push.bat — Windows-версия: stage, commit и push текущей ветки.
REM
REM Использование:
REM   scripts\git-commit-push.bat "сообщение коммита"
REM   scripts\git-commit-push.bat        (сообщение запросится интерактивно)

setlocal enabledelayedexpansion

REM Определяем корень репозитория (на уровень выше скрипта)
set "REPO_ROOT=%~dp0.."
cd /d "%REPO_ROOT%"

REM Текущая ветка
for /f "delims=" %%a in ('git rev-parse --abbrev-ref HEAD 2^>nul') do set "CURRENT_BRANCH=%%a"
if "%CURRENT_BRANCH%"=="" (
    echo Ошибка: не в git-репозитории.
    exit /b 1
)

if "%CURRENT_BRANCH%"=="main" (
    echo Внимание: вы находитесь на ветке main.
    set /p "REPLY=Продолжить коммит на main? (y/N) "
    if /i not "%REPLY%"=="y" if /i not "%REPLY%"=="Y" (
        echo Отменено. Создайте feature-ветку и повторите.
        exit /b 1
    )
)

echo === git status ===
git status --short

REM Сообщение коммита
set "COMMIT_MSG=%*"
if "%COMMIT_MSG%"=="" (
    set /p "COMMIT_MSG=Введите сообщение коммита: "
    if "%COMMIT_MSG%"=="" (
        echo Ошибка: пустое сообщение коммита.
        exit /b 1
    )
)

REM Добавляем стандартную атрибуцию
set "FULL_MSG=%COMMIT_MSG%

Co-Authored-By: Claude Code <noreply@anthropic.com>"

echo === git add -A ===
git add -A

echo === git commit ===
git commit -m "%FULL_MSG%"

echo === git push ===
git push origin %CURRENT_BRANCH%

echo Готово: закоммичено и запушено в ветку '%CURRENT_BRANCH%'.