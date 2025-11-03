@echo off
echo ===========================================
echo    Ships Monitoring Dashboard - Startup
echo ===========================================
echo.

REM Verificar se o Python está instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERRO: Python não encontrado no sistema.
    echo Por favor, instale o Python primeiro: https://python.org
    pause
    exit /b 1
)

echo Python encontrado! Verificando dependências...

REM Instalar dependências se necessário
echo Instalando/Atualizando dependências...
pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo ERRO: Falha ao instalar dependências.
    pause
    exit /b 1
)

echo.
echo Dependências instaladas com sucesso!
echo.
echo ===========================================
echo    Iniciando Ships Monitoring Dashboard
echo ===========================================
echo.
echo A aplicação será aberta no seu navegador padrão.
echo Para parar a aplicação, pressione Ctrl+C neste terminal.
echo.

REM Executar a aplicação Streamlit
streamlit run main.py

echo.
echo Aplicação encerrada.
pause