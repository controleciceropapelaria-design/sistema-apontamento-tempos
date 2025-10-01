# Sistema de Apontamento de Tempos de Producao

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/seu-usuario/nome-do-repo/main/app_github.py)

## 🚀 Acesso Online

**Link da Aplicacao:** [Clique aqui para acessar](https://share.streamlit.io/seu-usuario/nome-do-repo/main/app_github.py)

## 📋 Sobre o Sistema

Sistema completo para apontamento de tempos de processos de producao desenvolvido em Streamlit com persistencia de dados em CSV.

### Funcionalidades

- ✅ **Cadastro de OS** - Criar ordens de servico com produto e quantidade
- ✅ **Apontamento de Tempos** - Cronometros independentes com Play/Pause/Stop
- ✅ **Relatorios** - Visualizacao de tempos totais por processo
- ✅ **Persistencia CSV** - Dados salvos automaticamente no GitHub
- ✅ **Interface Responsiva** - Atualiza em tempo real
- ✅ **Multi-OS** - Multiplas ordens simultaneas

### Processos Incluidos

1. **Aviamento de capa**
2. **Aviamento de miolo**
3. **Encadernacao e Finalizacao**
4. **Montagem de capa**
5. **Montagem de Miolo**
6. **Montagem do kit**

## 🛠️ Como Usar

### 1. Cadastrar OS
- Acesse "Cadastro de OS"
- Preencha numero, produto e quantidade
- Clique em "Criar OS"

### 2. Apontar Tempos
- Acesse "Apontamento"
- Selecione a OS
- Use os botoes para cada processo:
  - **Play** ▶️ - Inicia/retoma cronometro
  - **Pause** ⏸️ - Pausa mantendo tempo
  - **Stop** ⏹️ - Para e reseta status

### 3. Ver Relatorios
- Acesse "Relatorios"
- Selecione a OS
- Visualize tempos por processo e total

### 4. Exportar Dados
- Acesse "Dados"
- Visualize os CSVs
- Download dos arquivos

## 💾 Estrutura de Dados

### ordens_servico.csv
```csv
numero_os,produto,quantidade,data_criacao
OS-001,Livro,100,2025-10-01T10:00:00
```

### tempos_processos.csv
```csv
numero_os,processo,tempo_total_segundos,status,inicio_atual,data_atualizacao
OS-001,Aviamento de capa,3600,pausado,,2025-10-01T11:00:00
```

## 🚀 Deploy no Streamlit Cloud

### Passo 1: Preparar Repositorio
1. Suba este codigo para seu GitHub
2. Certifique-se que tem os arquivos:
   - `app_github.py`
   - `requirements.txt`
   - `README.md`

### Passo 2: Deploy
1. Acesse [share.streamlit.io](https://share.streamlit.io)
2. Conecte sua conta GitHub
3. Selecione o repositorio
4. Defina arquivo principal: `app_github.py`
5. Deploy automatico!

### Passo 3: Dados Persistentes
- Os CSVs serao criados automaticamente
- Dados ficam salvos no repositorio
- Cada alteracao gera commit automatico

## 🔧 Executar Localmente

```bash
# Clonar repositorio
git clone https://github.com/seu-usuario/nome-do-repo.git
cd nome-do-repo

# Instalar dependencias
pip install -r requirements.txt

# Executar aplicacao
streamlit run app_github.py
```

## 📊 Recursos Tecnicos

- **Framework:** Streamlit 1.28+
- **Dados:** Pandas + CSV
- **Deploy:** Streamlit Cloud
- **Versionamento:** Git/GitHub
- **Auto-refresh:** Tempo real para processos ativos
- **Responsivo:** Layout adaptavel

## 🤝 Contribuicoes

Contribuicoes sao bem-vindas! Por favor:

1. Fork o repositorio
2. Crie uma branch para sua feature
3. Commit suas mudancas
4. Push para a branch
5. Abra um Pull Request

## 📄 Licenca

Este projeto esta sob a licenca MIT. Veja o arquivo LICENSE para detalhes.

---

**Desenvolvido com ❤️ usando Streamlit**