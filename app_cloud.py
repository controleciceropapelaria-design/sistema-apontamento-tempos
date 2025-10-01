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

def github_api_request(method, endpoint, data=None):
    """Faz requisição para GitHub API"""
    if not GITHUB_TOKEN:
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
        
        # Log da resposta para debug
        st.write(f"🔍 Debug API - {method} {endpoint}: Status {response.status_code}")
        
        if response.status_code in [200, 201]:
            return response.json()
        else:
            st.error(f"❌ GitHub API Error {response.status_code}: {response.text}")
            return None
    except Exception as e:
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
        st.info(f"🔄 Salvando OS no GitHub... (SHA: {sha[:8] if sha else 'novo'})")
        result = update_file_to_github("ordens_servico.csv", content, sha, commit_msg)
        if result:
            st.success("✅ OS salva no GitHub com sucesso!")
            st.json({"commit": result.get("commit", {}).get("sha", "N/A")[:8]})
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
        st.info(f"🔄 Salvando tempos no GitHub... (SHA: {sha[:8] if sha else 'novo'})")
        result = update_file_to_github("tempos_processos.csv", content, sha, commit_msg)
        if result:
            st.success("✅ Tempos salvos no GitHub!")
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

# Status do GitHub
if GITHUB_TOKEN:
    # Teste de conectividade
    test_response = github_api_request("GET", "")  # Info do repositório
    if test_response:
        st.success(f"🌐 Conectado ao GitHub: {test_response.get('full_name', 'N/A')}")
        st.info(f"📊 Último commit: {test_response.get('updated_at', 'N/A')}")
    else:
        st.error("❌ Token configurado mas erro de conexão")
else:
    st.warning("⚠️ Modo offline - Configure GITHUB_TOKEN nos secrets para sincronizar")

# Sidebar para navegação
st.sidebar.title("🧭 Navegação")
opcao = st.sidebar.selectbox("Escolha uma opção:", 
    ["🏠 Controle de Tempos", "📋 Gerenciar Ordens de Serviço", "📊 Relatórios"])

# Botão de teste de sincronização
st.sidebar.markdown("---")
st.sidebar.markdown("🔧 **Debug & Testes**")
if st.sidebar.button("🔄 Testar Sincronização"):
    if GITHUB_TOKEN:
        st.sidebar.info("Testando GitHub API...")
        
        # Testa leitura
        content, sha = get_file_from_github("ordens_servico.csv")
        if content:
            st.sidebar.success("✅ Leitura OK")
        else:
            st.sidebar.error("❌ Erro na leitura")
        
        # Testa escrita (arquivo de teste)
        test_content = f"teste,{datetime.now().isoformat()}\n"
        result = update_file_to_github("teste_sync.txt", test_content, None, "Teste de sincronização")
        if result:
            st.sidebar.success("✅ Escrita OK")
        else:
            st.sidebar.error("❌ Erro na escrita")
    else:
        st.sidebar.warning("⚠️ Token não configurado")

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
                        
                        st.session_state.df_os = pd.concat([st.session_state.df_os, pd.DataFrame([nova_os])], ignore_index=True)
                        
                        # Salva no GitHub
                        if salvar_os_github(st.session_state.df_os, st.session_state.sha_os):
                            # Recarrega dados para pegar novo SHA
                            st.session_state.df_os, st.session_state.sha_os = carregar_dados_os()
                        
                        st.success(f"✅ OS {numero_os} cadastrada com sucesso!")
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

# Rodapé
st.sidebar.markdown("---")
st.sidebar.markdown("🏭 **Sistema de Produção**")
st.sidebar.markdown("📅 Desenvolvido em 2025")