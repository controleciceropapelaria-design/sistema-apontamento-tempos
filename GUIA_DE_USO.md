# SISTEMA DE APONTAMENTO DE TEMPOS DE PRODUCAO

## Como Executar

### Opcao 1: Executar pelo arquivo BAT
1. Clique duas vezes no arquivo `iniciar.bat`
2. Aguarde o sistema carregar
3. O navegador abrira automaticamente

### Opcao 2: Executar pelo terminal
1. Abra o PowerShell ou CMD
2. Navegue ate a pasta do projeto
3. Execute: `python -m streamlit run app_simples.py`

## Como Usar o Sistema

### 1. Cadastrar uma OS (Ordem de Servico)
- Acesse a aba "Cadastro de OS" no menu lateral
- Preencha: Numero da OS, Produto e Quantidade
- Clique em "Criar OS"

### 2. Apontar Tempos
- Acesse a aba "Apontamento" no menu lateral  
- Selecione a OS desejada
- Para cada processo use os botoes:
  - **Play**: Inicia/retoma o cronometro
  - **Pause**: Pausa mantendo o tempo
  - **Stop**: Para e volta ao estado inicial

### 3. Visualizar Relatorios
- Acesse a aba "Relatorios" no menu lateral
- Selecione a OS para ver tempos totais por processo

## Processos Incluidos

Cada OS criada contem automaticamente estes processos:
1. Aviamento de capa
2. Aviamento de miolo  
3. Encadernacao e Finalizacao
4. Montagem de capa
5. Montagem de Miolo
6. Montagem do kit

## Recursos

- ✅ Cronometros independentes para cada processo
- ✅ Pause/retomada mantendo tempo acumulado
- ✅ Interface em tempo real (auto-refresh)
- ✅ Dados salvos automaticamente
- ✅ Multiplas OS ativas simultaneamente
- ✅ Relatorios de tempo por OS

## Arquivos do Sistema

- `app_simples.py` - Aplicacao principal
- `dados_producao.json` - Base de dados (criado automaticamente)
- `iniciar.bat` - Script de inicializacao
- `README.md` - Este arquivo de ajuda

## Solucao de Problemas

**Erro "Streamlit nao encontrado":**
- Execute: `pip install streamlit`

**Navegador nao abre automaticamente:**
- Abra manualmente: http://localhost:8501

**Dados nao salvam:**
- Verifique permissoes da pasta
- Execute como administrador se necessario

## Suporte Tecnico

Sistema desenvolvido com Python + Streamlit
Versao: 1.0
Data: Outubro 2025