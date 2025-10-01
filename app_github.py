import streamlit as st
import pandas as pd
import json
from datetime import datetime, timedelta
import time
import requests
import base64

# Configuração da página
st.set_page_config(
    page_title="Sistema de Apontamento de Tempos",
    page_icon="⏱️",
    layout="wide"
)

# Configuração GitHub API
GITHUB_TOKEN = st.secrets.get("GITHUB_TOKEN", "")  # Token será configurado nos secrets
GITHUB_REPO = "controleciceropapelaria-design/sistema-apontamento-tempos"
GITHUB_API_BASE = f"https://api.github.com/repos/{GITHUB_REPO}"

def github_api_request(method, endpoint, data=None, debug=False):
    """Faz requisição para GitHub API"""
    if not GITHUB_TOKEN:
        if debug:
            st.error("⚠️ Token do GitHub não configurado. Usando modo offline.")
        return None
    
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    url = f"{GITHUB_API_BASE}/{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "PUT":
            response = requests.put(url, headers=headers, json=data)
        
        # Log da resposta só no debug
        if debug:
            st.write(f"🔍 API {method} {endpoint}: Status {response.status_code}")
        
        if response.status_code in [200, 201]:
            return response.json()
        else:
            if debug:
                st.error(f"❌ GitHub API Error {response.status_code}")
                st.code(response.text)
            return None
    except Exception as e:
        if debug:
            st.error(f"❌ Erro de conexão GitHub: {str(e)}")
        return None

def get_file_from_github(filename):
    """Baixa arquivo do GitHub"""
    response = github_api_request("GET", f"contents/{filename}")
    if response:
        content = base64.b64decode(response["content"]).decode("utf-8")
        return content, response["sha"]
    return None, None

def update_file_to_github(filename, content, sha, commit_message):
    """Atualiza arquivo no GitHub"""
    encoded_content = base64.b64encode(content.encode("utf-8")).decode("utf-8")
    
    data = {
        "message": commit_message,
        "content": encoded_content
    }
    
    # Só adiciona SHA se existir (para arquivos existentes)
    if sha:
        data["sha"] = sha
    
    return github_api_request("PUT", f"contents/{filename}", data)

def carregar_dados_os():
    """Carrega ordens de serviço do GitHub ou local"""
    # Primeiro tenta GitHub
    content, sha = get_file_from_github("ordens_servico.csv")
    if content:
        try:
            df = pd.read_csv(pd.StringIO(content))
            return df, sha
        except:
            pass
    
    # Fallback para arquivo local
    try:
        df = pd.read_csv("ordens_servico.csv")
        return df, None
    except:
        df = pd.DataFrame(columns=['numero_os', 'produto', 'quantidade', 'data_criacao', 'status_os'])
        return df, None

def carregar_dados_tempos():
    """Carrega tempos de processo do GitHub ou local"""
    # Primeiro tenta GitHub
    content, sha = get_file_from_github("tempos_processos.csv")
    if content:
        try:
            df = pd.read_csv(pd.StringIO(content))
            return df, sha
        except:
            pass
    
    # Fallback para arquivo local
    try:
        df = pd.read_csv("tempos_processos.csv")
        return df, None
    except:
        df = pd.DataFrame(columns=['numero_os', 'processo', 'tempo_total_segundos', 'status', 'inicio_atual', 'data_atualizacao'])
        return df, None

def salvar_os_github(df, sha):
    """Salva OS no GitHub"""
    content = df.to_csv(index=False)
    commit_msg = f"OS atualizada - {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    
    # Sempre salva local primeiro como backup
    df.to_csv("ordens_servico.csv", index=False)
    
    if GITHUB_TOKEN:
        with st.spinner('🔄 Sincronizando com GitHub...'):
            # Primeiro, busca o SHA mais atual
            current_content, current_sha = get_file_from_github("ordens_servico.csv")
            if current_sha:
                sha = current_sha  # Usa o SHA mais atual
            
            result = update_file_to_github("ordens_servico.csv", content, sha, commit_msg)
            if result:
                st.success("✅ OS salva no GitHub com sucesso!")
                # Atualiza o SHA no session state
                st.session_state.sha_os = result.get("content", {}).get("sha")
                # Força recarregamento dos dados
                st.session_state.df_os, st.session_state.sha_os = carregar_dados_os()
                return True
            else:
                st.error("❌ Erro ao salvar no GitHub - mantido backup local")
    else:
        st.warning("⚠️ GitHub Token não configurado - salvo apenas localmente")
    
    return False

def salvar_tempos_github(df, sha):
    """Salva tempos no GitHub"""
    content = df.to_csv(index=False)
    commit_msg = f"Tempos atualizados - {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    
    # Sempre salva local primeiro como backup
    df.to_csv("tempos_processos.csv", index=False)
    
    if GITHUB_TOKEN:
        with st.spinner('🔄 Sincronizando tempos com GitHub...'):
            # Primeiro, busca o SHA mais atual
            current_content, current_sha = get_file_from_github("tempos_processos.csv")
            if current_sha:
                sha = current_sha  # Usa o SHA mais atual
            
            result = update_file_to_github("tempos_processos.csv", content, sha, commit_msg)
            if result:
                st.success("✅ Tempos salvos no GitHub!")
                # Atualiza o SHA no session state
                st.session_state.sha_tempos = result.get("content", {}).get("sha")
                # Força recarregamento dos dados
                st.session_state.df_tempos, st.session_state.sha_tempos = carregar_dados_tempos()
                return True
            else:
                st.error("❌ Erro ao salvar tempos no GitHub - mantido backup local")
    else:
        st.warning("⚠️ GitHub Token não configurado - salvo apenas localmente")
    
    return False

# Inicialização dos dados
if 'df_os' not in st.session_state or 'sha_os' not in st.session_state:
    st.session_state.df_os, st.session_state.sha_os = carregar_dados_os()

if 'df_tempos' not in st.session_state or 'sha_tempos' not in st.session_state:
    st.session_state.df_tempos, st.session_state.sha_tempos = carregar_dados_tempos()

# Lista de processos
PROCESSOS = [
    "Aviamento de capa",
    "Aviamento de miolo", 
    "Encadernação e Finalização",
    "Montagem de capa",
    "Montagem de Miolo",
    "Montagem do kit"
]

def formatar_tempo(segundos):
    """Formata tempo em HH:MM:SS"""
    if pd.isna(segundos) or segundos == 0:
        return "00:00:00"
    
    horas = int(segundos // 3600)
    minutos = int((segundos % 3600) // 60)
    segundos = int(segundos % 60)
    return f"{horas:02d}:{minutos:02d}:{segundos:02d}"

def iniciar_processo(numero_os, processo):
    """Inicia cronômetro do processo"""
    agora = datetime.now()
    
    # Verifica se já existe registro
    mask = (st.session_state.df_tempos['numero_os'] == numero_os) & (st.session_state.df_tempos['processo'] == processo)
    
    if mask.any():
        # Atualiza registro existente
        st.session_state.df_tempos.loc[mask, 'status'] = 'em_andamento'
        st.session_state.df_tempos.loc[mask, 'inicio_atual'] = agora.isoformat()
        st.session_state.df_tempos.loc[mask, 'data_atualizacao'] = agora.isoformat()
    else:
        # Cria novo registro
        novo_registro = {
            'numero_os': numero_os,
            'processo': processo,
            'tempo_total_segundos': 0,
            'status': 'em_andamento',
            'inicio_atual': agora.isoformat(),
            'data_atualizacao': agora.isoformat()
        }
        st.session_state.df_tempos = pd.concat([st.session_state.df_tempos, pd.DataFrame([novo_registro])], ignore_index=True)
    
    # Salva no GitHub
    salvar_tempos_github(st.session_state.df_tempos, st.session_state.sha_tempos)

def pausar_processo(numero_os, processo):
    """Pausa cronômetro do processo"""
    mask = (st.session_state.df_tempos['numero_os'] == numero_os) & (st.session_state.df_tempos['processo'] == processo)
    
    if mask.any():
        agora = datetime.now()
        inicio_str = st.session_state.df_tempos.loc[mask, 'inicio_atual'].iloc[0]
        
        if pd.notna(inicio_str) and inicio_str:
            inicio = datetime.fromisoformat(inicio_str)
            tempo_decorrido = (agora - inicio).total_seconds()
            
            # Atualiza tempo total
            tempo_atual = st.session_state.df_tempos.loc[mask, 'tempo_total_segundos'].iloc[0]
            if pd.isna(tempo_atual):
                tempo_atual = 0
            
            st.session_state.df_tempos.loc[mask, 'tempo_total_segundos'] = tempo_atual + tempo_decorrido
            st.session_state.df_tempos.loc[mask, 'status'] = 'pausado'
            st.session_state.df_tempos.loc[mask, 'inicio_atual'] = None
            st.session_state.df_tempos.loc[mask, 'data_atualizacao'] = agora.isoformat()
            
            # Salva no GitHub
            salvar_tempos_github(st.session_state.df_tempos, st.session_state.sha_tempos)

def parar_processo(numero_os, processo):
    """Para cronômetro do processo"""
    pausar_processo(numero_os, processo)
    
    mask = (st.session_state.df_tempos['numero_os'] == numero_os) & (st.session_state.df_tempos['processo'] == processo)
    if mask.any():
        st.session_state.df_tempos.loc[mask, 'status'] = 'finalizado'
        st.session_state.df_tempos.loc[mask, 'data_atualizacao'] = datetime.now().isoformat()
        
        # Salva no GitHub
        salvar_tempos_github(st.session_state.df_tempos, st.session_state.sha_tempos)

def get_tempo_atual_processo(numero_os, processo):
    """Calcula tempo atual do processo"""
    mask = (st.session_state.df_tempos['numero_os'] == numero_os) & (st.session_state.df_tempos['processo'] == processo)
    
    if not mask.any():
        return 0, 'não_iniciado'
    
    row = st.session_state.df_tempos.loc[mask].iloc[0]
    tempo_total = row['tempo_total_segundos'] if pd.notna(row['tempo_total_segundos']) else 0
    status = row['status'] if pd.notna(row['status']) else 'não_iniciado'
    
    # Se está em andamento, adiciona tempo desde o último início
    if status == 'em_andamento' and pd.notna(row['inicio_atual']) and row['inicio_atual']:
        inicio = datetime.fromisoformat(row['inicio_atual'])
        tempo_decorrido = (datetime.now() - inicio).total_seconds()
        tempo_total += tempo_decorrido
    
    return tempo_total, status

# Interface principal
st.title("⏱️ Sistema de Apontamento de Tempos de Produção")

# Status do GitHub com comparação
col_status1, col_status2 = st.columns(2)

with col_status1:
    if GITHUB_TOKEN:
        # Teste de conectividade
        test_response = github_api_request("GET", "")  # Info do repositório
        if test_response:
            st.success(f"🌐 Conectado: {test_response.get('full_name', 'N/A')}")
        else:
            st.error("❌ Token configurado mas erro de conexão")
    else:
        st.warning("⚠️ Modo offline")

with col_status2:
    if GITHUB_TOKEN:
        # Compara dados locais vs GitHub
        github_os, _ = get_file_from_github("ordens_servico.csv")
        if github_os:
            try:
                df_github = pd.read_csv(pd.StringIO(github_os))
                if len(st.session_state.df_os) != len(df_github):
                    st.warning(f"⚠️ Dessincronizado: Local({len(st.session_state.df_os)}) vs GitHub({len(df_github)})")
                else:
                    st.success(f"✅ Sincronizado: {len(st.session_state.df_os)} OS")
            except:
                st.info("📄 GitHub vazio ou erro na leitura")
        else:
            st.info("📄 Arquivo não encontrado no GitHub")

# Sidebar para navegação
st.sidebar.title("🧭 Navegação")
opcao = st.sidebar.selectbox("Escolha uma opção:", 
    ["🏠 Controle de Tempos", "📋 Gerenciar Ordens de Serviço", "📊 Relatórios", "🔧 Debug GitHub"])

# Seção de debug na sidebar
st.sidebar.markdown("---")
st.sidebar.markdown("🔧 **Debug & Diagnóstico**")

# Mostrar status do token
if GITHUB_TOKEN:
    st.sidebar.success(f"✅ Token: ...{GITHUB_TOKEN[-4:]}")
else:
    st.sidebar.error("❌ Token não encontrado")

# Botão de teste manual
if st.sidebar.button("🔄 Teste Completo GitHub"):
    with st.sidebar:
        st.write("### 🔍 Testando GitHub API")
        
        if not GITHUB_TOKEN:
            st.error("❌ Token não configurado!")
        else:
            st.info("1️⃣ Testando acesso ao repositório...")
            
            # Teste 1: Acesso ao repo
            repo_info = github_api_request("GET", "", debug=True)
            if repo_info:
                st.success(f"✅ Repo OK: {repo_info.get('name', 'N/A')}")
            else:
                st.error("❌ Erro no acesso ao repositório")
                
            st.info("2️⃣ Testando leitura de arquivo...")
            
            # Teste 2: Leitura
            content, sha = get_file_from_github("ordens_servico.csv")
            if content is not None:
                st.success(f"✅ Leitura OK (SHA: {sha[:8] if sha else 'N/A'})")
                st.text(f"Conteúdo: {len(content)} chars")
            else:
                st.error("❌ Erro na leitura do arquivo")
                
            st.info("3️⃣ Testando escrita...")
            
            # Teste 3: Escrita
            test_content = f"teste_debug,{datetime.now().isoformat()}\n"
            with st.expander("🔍 Detalhes da Escrita"):
                result = github_api_request("PUT", "contents/debug_test.txt", {
                    "message": "Debug test", 
                    "content": base64.b64encode(test_content.encode()).decode()
                }, debug=True)
                
            if result:
                st.success("✅ Escrita funcionando!")
                st.json({"commit_sha": result.get("commit", {}).get("sha", "N/A")[:8]})
            else:
                st.error("❌ Erro na escrita")

# Status detalhado dos dados
st.sidebar.markdown("### 📊 Status dos Dados")
st.sidebar.write(f"📋 OS Locais: {len(st.session_state.df_os)}")
st.sidebar.write(f"⏱️ Tempos Locais: {len(st.session_state.df_tempos)}")

# Botão de sincronização forçada
if st.sidebar.button("🔄 Forçar Sincronização"):
    with st.sidebar:
        with st.spinner("Sincronizando..."):
            # Recarrega dados do GitHub
            st.session_state.df_os, st.session_state.sha_os = carregar_dados_os()
            st.session_state.df_tempos, st.session_state.sha_tempos = carregar_dados_tempos()
            st.success("✅ Dados sincronizados!")
            st.rerun()

if opcao == "📋 Gerenciar Ordens de Serviço":
    st.header("📋 Gerenciar Ordens de Serviço")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("➕ Cadastrar Nova OS")
        
        with st.form("cadastrar_os"):
            numero_os = st.number_input("Número da OS:", min_value=1, step=1)
            produto = st.text_input("Produto:")
            quantidade = st.number_input("Quantidade:", min_value=1, step=1, value=1)
            
            if st.form_submit_button("Cadastrar OS"):
                if numero_os and produto:
                    # Verifica se OS já existe
                    if numero_os in st.session_state.df_os['numero_os'].values:
                        st.error("❌ OS já existe!")
                    else:
                        nova_os = {
                            'numero_os': numero_os,
                            'produto': produto,
                            'quantidade': quantidade,
                            'data_criacao': datetime.now().isoformat(),
                            'status_os': 'ativa'
                        }
                        
                        # Adiciona a OS ao DataFrame local
                        st.session_state.df_os = pd.concat([st.session_state.df_os, pd.DataFrame([nova_os])], ignore_index=True)
                        
                        # Mostra progresso
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        status_text.text("💾 Salvando localmente...")
                        progress_bar.progress(25)
                        
                        # Salva no GitHub
                        status_text.text("🌐 Enviando para GitHub...")
                        progress_bar.progress(50)
                        
                        sucesso_github = salvar_os_github(st.session_state.df_os, st.session_state.sha_os)
                        progress_bar.progress(100)
                        
                        if sucesso_github:
                            status_text.text("✅ Sincronizado com GitHub!")
                        else:
                            status_text.text("⚠️ Salvo localmente, problema no GitHub")
                        
                        st.success(f"✅ OS {numero_os} cadastrada com sucesso!")
                        time.sleep(1)  # Pausa para mostrar o feedback
                        st.rerun()
                else:
                    st.error("❌ Preencha todos os campos!")
    
    with col2:
        st.subheader("📋 Ordens de Serviço Ativas")
        
        if not st.session_state.df_os.empty:
            os_ativas = st.session_state.df_os[st.session_state.df_os['status_os'] == 'ativa']
            
            for _, os_row in os_ativas.iterrows():
                with st.container():
                    st.markdown(f"**OS {int(os_row['numero_os'])}** - {os_row['produto']}")
                    col_btn1, col_btn2 = st.columns(2)
                    
                    with col_btn1:
                        if st.button(f"🗑️ Excluir", key=f"del_{os_row['numero_os']}"):
                            # Remove OS e seus tempos
                            st.session_state.df_os = st.session_state.df_os[st.session_state.df_os['numero_os'] != os_row['numero_os']]
                            st.session_state.df_tempos = st.session_state.df_tempos[st.session_state.df_tempos['numero_os'] != os_row['numero_os']]
                            
                            # Salva no GitHub
                            salvar_os_github(st.session_state.df_os, st.session_state.sha_os)
                            salvar_tempos_github(st.session_state.df_tempos, st.session_state.sha_tempos)
                            
                            st.success(f"✅ OS {int(os_row['numero_os'])} excluída!")
                            st.rerun()
                    
                    with col_btn2:
                        if st.button(f"✅ Finalizar", key=f"fin_{os_row['numero_os']}"):
                            # Finaliza OS
                            mask_os = st.session_state.df_os['numero_os'] == os_row['numero_os']
                            st.session_state.df_os.loc[mask_os, 'status_os'] = 'finalizada'
                            
                            # Finaliza todos os processos da OS
                            mask_tempos = st.session_state.df_tempos['numero_os'] == os_row['numero_os']
                            st.session_state.df_tempos.loc[mask_tempos, 'status'] = 'finalizado'
                            
                            # Salva no GitHub
                            salvar_os_github(st.session_state.df_os, st.session_state.sha_os)
                            salvar_tempos_github(st.session_state.df_tempos, st.session_state.sha_tempos)
                            
                            st.success(f"✅ OS {int(os_row['numero_os'])} finalizada!")
                            st.rerun()
                    
                    st.divider()
        else:
            st.info("📝 Nenhuma OS cadastrada ainda.")

elif opcao == "🏠 Controle de Tempos":
    st.header("⏱️ Controle de Tempos por Processo")
    
    # Seleção da OS
    if not st.session_state.df_os.empty:
        os_ativas = st.session_state.df_os[st.session_state.df_os['status_os'] == 'ativa']
        
        if not os_ativas.empty:
            os_opcoes = {f"OS {int(row['numero_os'])} - {row['produto']}": int(row['numero_os']) 
                        for _, row in os_ativas.iterrows()}
            
            os_selecionada_str = st.selectbox("🎯 Selecione a OS:", list(os_opcoes.keys()))
            os_selecionada = os_opcoes[os_selecionada_str]
            
            st.subheader(f"📋 Processos da {os_selecionada_str}")
            
            # Auto-refresh a cada 1 segundo
            placeholder = st.empty()
            
            with placeholder.container():
                # Criar grid de processos
                for i in range(0, len(PROCESSOS), 2):
                    col1, col2 = st.columns(2)
                    
                    # Processo 1
                    with col1:
                        if i < len(PROCESSOS):
                            processo = PROCESSOS[i]
                            tempo_atual, status = get_tempo_atual_processo(os_selecionada, processo)
                            
                            # Card do processo
                            with st.container():
                                st.markdown(f"### {processo}")
                                st.markdown(f"**⏰ Tempo:** `{formatar_tempo(tempo_atual)}`")
                                st.markdown(f"**📊 Status:** {status.replace('_', ' ').title()}")
                                
                                col_play, col_pause, col_stop = st.columns(3)
                                
                                with col_play:
                                    if st.button("▶️ Play", key=f"play_{processo}_{os_selecionada}", 
                                               disabled=(status == 'em_andamento')):
                                        iniciar_processo(os_selecionada, processo)
                                        st.rerun()
                                
                                with col_pause:
                                    if st.button("⏸️ Pause", key=f"pause_{processo}_{os_selecionada}",
                                               disabled=(status != 'em_andamento')):
                                        pausar_processo(os_selecionada, processo)
                                        st.rerun()
                                
                                with col_stop:
                                    if st.button("⏹️ Stop", key=f"stop_{processo}_{os_selecionada}",
                                               disabled=(status == 'não_iniciado')):
                                        parar_processo(os_selecionada, processo)
                                        st.rerun()
                    
                    # Processo 2
                    with col2:
                        if i + 1 < len(PROCESSOS):
                            processo = PROCESSOS[i + 1]
                            tempo_atual, status = get_tempo_atual_processo(os_selecionada, processo)
                            
                            # Card do processo
                            with st.container():
                                st.markdown(f"### {processo}")
                                st.markdown(f"**⏰ Tempo:** `{formatar_tempo(tempo_atual)}`")
                                st.markdown(f"**📊 Status:** {status.replace('_', ' ').title()}")
                                
                                col_play, col_pause, col_stop = st.columns(3)
                                
                                with col_play:
                                    if st.button("▶️ Play", key=f"play_{processo}_{os_selecionada}",
                                               disabled=(status == 'em_andamento')):
                                        iniciar_processo(os_selecionada, processo)
                                        st.rerun()
                                
                                with col_pause:
                                    if st.button("⏸️ Pause", key=f"pause_{processo}_{os_selecionada}",
                                               disabled=(status != 'em_andamento')):
                                        pausar_processo(os_selecionada, processo)
                                        st.rerun()
                                
                                with col_stop:
                                    if st.button("⏹️ Stop", key=f"stop_{processo}_{os_selecionada}",
                                               disabled=(status == 'não_iniciado')):
                                        parar_processo(os_selecionada, processo)
                                        st.rerun()
            
            # Auto-refresh
            time.sleep(1)
            st.rerun()
        
        else:
            st.warning("📝 Nenhuma OS ativa encontrada. Cadastre uma OS primeiro.")
    
    else:
        st.warning("📝 Nenhuma OS cadastrada. Vá para 'Gerenciar Ordens de Serviço' para criar uma.")

elif opcao == "📊 Relatórios":
    st.header("📊 Relatórios de Tempos")
    
    if not st.session_state.df_tempos.empty:
        # Resumo por OS
        st.subheader("📋 Resumo por Ordem de Serviço")
        
        resumo_os = []
        for numero_os in st.session_state.df_tempos['numero_os'].unique():
            tempos_os = st.session_state.df_tempos[st.session_state.df_tempos['numero_os'] == numero_os]
            tempo_total = tempos_os['tempo_total_segundos'].sum()
            
            # Buscar info da OS
            os_info = st.session_state.df_os[st.session_state.df_os['numero_os'] == numero_os]
            produto = os_info['produto'].iloc[0] if not os_info.empty else "N/A"
            
            resumo_os.append({
                'OS': numero_os,
                'Produto': produto,
                'Tempo Total': formatar_tempo(tempo_total),
                'Processos': len(tempos_os)
            })
        
        df_resumo = pd.DataFrame(resumo_os)
        st.dataframe(df_resumo, use_container_width=True)
        
        # Detalhes por processo
        st.subheader("🔍 Detalhes por Processo")
        
        os_selecionada_rel = st.selectbox(
            "Selecione uma OS para ver detalhes:",
            st.session_state.df_tempos['numero_os'].unique()
        )
        
        if os_selecionada_rel:
            detalhes = st.session_state.df_tempos[
                st.session_state.df_tempos['numero_os'] == os_selecionada_rel
            ].copy()
            
            if not detalhes.empty:
                # Formatar tempo para exibição
                detalhes['Tempo Formatado'] = detalhes['tempo_total_segundos'].apply(formatar_tempo)
                
                # Selecionar colunas para exibição
                colunas_exibir = ['processo', 'Tempo Formatado', 'status', 'data_atualizacao']
                detalhes_exibir = detalhes[colunas_exibir].copy()
                detalhes_exibir.columns = ['Processo', 'Tempo Total', 'Status', 'Última Atualização']
                
                st.dataframe(detalhes_exibir, use_container_width=True)
            else:
                st.info("📝 Nenhum tempo registrado para esta OS ainda.")
    else:
        st.info("📝 Nenhum tempo registrado ainda.")

elif opcao == "🔧 Debug GitHub":
    st.header("🔧 Diagnóstico GitHub API")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Status Atual")
        
        if GITHUB_TOKEN:
            st.success(f"✅ Token configurado: ...{GITHUB_TOKEN[-6:]}")
            st.info(f"📍 Repositório: {GITHUB_REPO}")
        else:
            st.error("❌ Token não configurado")
            st.markdown("""
            **Para configurar:**
            1. Vá em Settings → Secrets
            2. Adicione: `GITHUB_TOKEN = "seu_token_aqui"`
            """)
        
        st.markdown(f"**Dados locais:**")
        st.write(f"📋 OS: {len(st.session_state.df_os)} registros")
        st.write(f"⏱️ Tempos: {len(st.session_state.df_tempos)} registros")
    
    with col2:
        st.subheader("🧪 Teste Completo")
        
        if st.button("🚀 Executar Diagnóstico Completo", key="debug_main"):
            if not GITHUB_TOKEN:
                st.error("❌ Configure o token primeiro!")
            else:
                with st.container():
                    # Teste 1: Repositório
                    st.write("**1️⃣ Testando acesso ao repositório...**")
                    repo_info = github_api_request("GET", "", debug=False)
                    if repo_info:
                        st.success(f"✅ Conectado: {repo_info.get('full_name')}")
                        st.info(f"📅 Último update: {repo_info.get('updated_at')}")
                    else:
                        st.error("❌ Erro no acesso ao repositório")
                        st.stop()
                    
                    # Teste 2: Leitura
                    st.write("**2️⃣ Testando leitura de arquivos...**")
                    content_os, sha_os = get_file_from_github("ordens_servico.csv")
                    content_tempos, sha_tempos = get_file_from_github("tempos_processos.csv")
                    
                    if content_os is not None:
                        st.success(f"✅ ordens_servico.csv: {len(content_os)} chars (SHA: {sha_os[:8] if sha_os else 'N/A'})")
                    else:
                        st.warning("⚠️ ordens_servico.csv não encontrado")
                    
                    if content_tempos is not None:
                        st.success(f"✅ tempos_processos.csv: {len(content_tempos)} chars (SHA: {sha_tempos[:8] if sha_tempos else 'N/A'})")
                    else:
                        st.warning("⚠️ tempos_processos.csv não encontrado")
                    
                    # Teste 3: Escrita
                    st.write("**3️⃣ Testando escrita...**")
                    test_content = f"debug_test,{datetime.now().isoformat()},OK\n"
                    
                    encoded_content = base64.b64encode(test_content.encode()).decode()
                    test_data = {
                        "message": f"Debug test - {datetime.now().strftime('%H:%M:%S')}",
                        "content": encoded_content
                    }
                    
                    result = github_api_request("PUT", "contents/debug_sync_test.csv", test_data, debug=False)
                    if result:
                        st.success("✅ Escrita funcionando perfeitamente!")
                        commit_sha = result.get("commit", {}).get("sha", "N/A")
                        st.info(f"📝 Commit criado: {commit_sha[:8]}")
                    else:
                        st.error("❌ Erro na escrita - verifique permissões do token")
                    
                    # Teste 4: Simulação de OS
                    st.write("**4️⃣ Testando fluxo completo de OS...**")
                    
                    test_os = pd.DataFrame([{
                        'numero_os': 9999,
                        'produto': 'TESTE DEBUG',
                        'quantidade': 1,
                        'data_criacao': datetime.now().isoformat(),
                        'status_os': 'ativa'
                    }])
                    
                    csv_content = test_os.to_csv(index=False)
                    encoded_csv = base64.b64encode(csv_content.encode()).decode()
                    
                    os_data = {
                        "message": f"Teste OS completo - {datetime.now().strftime('%H:%M:%S')}",
                        "content": encoded_csv
                    }
                    
                    os_result = github_api_request("PUT", "contents/teste_os_debug.csv", os_data, debug=False)
                    if os_result:
                        st.success("✅ Simulação de OS funcionando!")
                        st.balloons()
                    else:
                        st.error("❌ Problema no fluxo de OS")
    
    # Logs em tempo real
    st.subheader("📋 Arquivos no GitHub")
    if st.button("🔍 Listar Arquivos"):
        files_info = github_api_request("GET", "contents/")
        if files_info:
            for file in files_info:
                if file['name'].endswith('.csv'):
                    st.write(f"📄 {file['name']} - {file['size']} bytes")

# Rodapé
st.sidebar.markdown("---")
st.sidebar.markdown("🏭 **Sistema de Produção**")
st.sidebar.markdown("📅 Desenvolvido em 2025")