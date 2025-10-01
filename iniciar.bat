@echo off
title Sistema de Apontamento de Tempos
echo ========================================
echo   SISTEMA DE APONTAMENTO DE TEMPOS     
echo ========================================
echo.
echo Verificando dependencias...

rem Instalar streamlit se necessario
pip install streamlit 2>nul >nul

echo Iniciando sistema...
echo.
echo O sistema sera aberto no seu navegador padrao.
echo Pressione Ctrl+C para parar o sistema.
echo.

rem Executar streamlit
python -m streamlit run app_simples.py --server.headless false --browser.gatherUsageStats false

pause