import streamlit as st
import json
import os
from datetime import datetime, timedelta
import time

# Configuracao da pagina
st.set_page_config(
    page_title="Sistema de Apontamento de Tempos",
    page_icon=":stopwatch:",
    layout="wide"
)

# Arquivo para armazenar os dados
DATA_FILE = "dados_producao.json"

# Processos disponiveis
PROCESSOS = [
    "Aviamento de capa",
    "Aviamento de miolo", 
    "Encadernacao e Finalizacao",
    "Montagem de capa",
    "Montagem de Miolo",
    "Montagem do kit"
]

def carregar_dados():
    """Carrega os dados do arquivo JSON"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {"ordens_servico": {}}
    return {"ordens_servico": {}}

def salvar_dados(dados):
    """Salva os dados no arquivo JSON"""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)

def inicializar_os(numero_os, produto, quantidade):
    """Inicializa uma nova ordem de servico"""
    dados = carregar_dados()
    
    dados["ordens_servico"][numero_os] = {
        "produto": produto,
        "quantidade": quantidade,
        "data_criacao": datetime.now().isoformat(),
        "processos": {}
    }
    
    # Inicializa cada processo
    for processo in PROCESSOS:
        dados["ordens_servico"][numero_os]["processos"][processo] = {
            "tempo_total": 0,  # em segundos
            "status": "parado",  # parado, rodando, pausado
            "inicio_atual": None,
            "pausas": []
        }
    
    salvar_dados(dados)
    return dados

def atualizar_tempo_processo(numero_os, processo):
    """Atualiza o tempo de um processo baseado no status atual"""
    dados = carregar_dados()
    
    if numero_os not in dados["ordens_servico"]:
        return dados
    
    processo_data = dados["ordens_servico"][numero_os]["processos"][processo]
    
    if processo_data["status"] == "rodando" and processo_data["inicio_atual"]:
        # Calcula o tempo decorrido desde o ultimo inicio
        inicio = datetime.fromisoformat(processo_data["inicio_atual"])
        tempo_decorrido = (datetime.now() - inicio).total_seconds()
        processo_data["tempo_total"] += tempo_decorrido
        processo_data["inicio_atual"] = datetime.now().isoformat()
    
    salvar_dados(dados)
    return dados

def iniciar_processo(numero_os, processo):
    """Inicia ou retoma um processo"""
    dados = atualizar_tempo_processo(numero_os, processo)
    
    dados["ordens_servico"][numero_os]["processos"][processo]["status"] = "rodando"
    dados["ordens_servico"][numero_os]["processos"][processo]["inicio_atual"] = datetime.now().isoformat()
    
    salvar_dados(dados)

def pausar_processo(numero_os, processo):
    """Pausa um processo"""
    dados = atualizar_tempo_processo(numero_os, processo)
    
    dados["ordens_servico"][numero_os]["processos"][processo]["status"] = "pausado"
    dados["ordens_servico"][numero_os]["processos"][processo]["inicio_atual"] = None
    
    salvar_dados(dados)

def parar_processo(numero_os, processo):
    """Para um processo"""
    dados = atualizar_tempo_processo(numero_os, processo)
    
    dados["ordens_servico"][numero_os]["processos"][processo]["status"] = "parado"
    dados["ordens_servico"][numero_os]["processos"][processo]["inicio_atual"] = None
    
    salvar_dados(dados)

def formatar_tempo(segundos):
    """Formata o tempo em segundos para HH:MM:SS"""
    horas = int(segundos // 3600)
    minutos = int((segundos % 3600) // 60)
    segundos = int(segundos % 60)
    return f"{horas:02d}:{minutos:02d}:{segundos:02d}"

def calcular_tempo_atual(processo_data):
    """Calcula o tempo atual de um processo incluindo o tempo em execucao"""
    tempo_total = processo_data["tempo_total"]
    
    if processo_data["status"] == "rodando" and processo_data["inicio_atual"]:
        inicio = datetime.fromisoformat(processo_data["inicio_atual"])
        tempo_decorrido = (datetime.now() - inicio).total_seconds()
        tempo_total += tempo_decorrido
    
    return tempo_total

# Interface principal
st.title(":stopwatch: Sistema de Apontamento de Tempos de Producao")

# Sidebar para navegacao
st.sidebar.title("Navegacao")
pagina = st.sidebar.selectbox("Escolha uma pagina:", ["Cadastro de OS", "Apontamento de Tempos", "Relatorios"])

if pagina == "Cadastro de OS":
    st.header(":memo: Cadastro de Ordem de Servico")
    
    with st.form("cadastro_os"):
        col1, col2 = st.columns(2)
        
        with col1:
            numero_os = st.text_input("Numero da OS:", placeholder="Ex: OS-001")
            produto = st.text_input("Tipo de Produto:", placeholder="Ex: Livro, Revista, Catalogo")
        
        with col2:
            quantidade = st.number_input("Quantidade:", min_value=1, value=1)
        
        submitted = st.form_submit_button("Criar OS")
        
        if submitted:
            if numero_os and produto:
                dados = carregar_dados()
                if numero_os in dados["ordens_servico"]:
                    st.error(f"A OS {numero_os} ja existe!")
                else:
                    inicializar_os(numero_os, produto, quantidade)
                    st.success(f"OS {numero_os} criada com sucesso!")
            else:
                st.error("Preencha todos os campos obrigatorios!")

elif pagina == "Apontamento de Tempos":
    st.header(":clock2: Apontamento de Tempos")
    
    dados = carregar_dados()
    
    if not dados["ordens_servico"]:
        st.warning("Nenhuma OS cadastrada. Va para a pagina de Cadastro primeiro.")
    else:
        # Selecao da OS
        os_selecionada = st.selectbox(
            "Selecione a OS:",
            list(dados["ordens_servico"].keys())
        )
        
        if os_selecionada:
            os_data = dados["ordens_servico"][os_selecionada]
            
            # Informacoes da OS
            col1, col2, col3 = st.columns(3)
            with col1:
                st.info(f"**Produto:** {os_data['produto']}")
            with col2:
                st.info(f"**Quantidade:** {os_data['quantidade']}")
            with col3:
                st.info(f"**Criada em:** {datetime.fromisoformat(os_data['data_criacao']).strftime('%d/%m/%Y %H:%M')}")
            
            st.divider()
            
            # Container para auto-refresh
            placeholder = st.empty()
            
            with placeholder.container():
                # Processos
                for i, processo in enumerate(PROCESSOS):
                    processo_data = os_data["processos"][processo]
                    tempo_atual = calcular_tempo_atual(processo_data)
                    
                    # Layout do processo
                    col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
                    
                    with col1:
                        status_color = {
                            "parado": ":red_circle:",
                            "rodando": ":green_circle:", 
                            "pausado": ":yellow_circle:"
                        }
                        st.write(f"{status_color[processo_data['status']]} **{processo}**")
                        st.write(f"Tempo: {formatar_tempo(tempo_atual)}")
                    
                    with col2:
                        if st.button(":arrow_forward: Play", key=f"play_{i}", disabled=(processo_data['status'] == 'rodando')):
                            iniciar_processo(os_selecionada, processo)
                            st.rerun()
                    
                    with col3:
                        if st.button(":pause_button: Pause", key=f"pause_{i}", disabled=(processo_data['status'] != 'rodando')):
                            pausar_processo(os_selecionada, processo)
                            st.rerun()
                    
                    with col4:
                        if st.button(":stop_button: Stop", key=f"stop_{i}", disabled=(processo_data['status'] == 'parado')):
                            parar_processo(os_selecionada, processo)
                            st.rerun()
                    
                    with col5:
                        st.write(f"Status: {processo_data['status'].title()}")
                    
                    st.divider()
            
            # Auto-refresh a cada 1 segundo se houver processos rodando
            processos_rodando = any(p["status"] == "rodando" for p in os_data["processos"].values())
            if processos_rodando:
                time.sleep(1)
                st.rerun()

elif pagina == "Relatorios":
    st.header(":bar_chart: Relatorios")
    
    dados = carregar_dados()
    
    if not dados["ordens_servico"]:
        st.warning("Nenhuma OS cadastrada.")
    else:
        # Selecao da OS para relatorio
        os_selecionada = st.selectbox(
            "Selecione a OS para visualizar o relatorio:",
            list(dados["ordens_servico"].keys())
        )
        
        if os_selecionada:
            os_data = dados["ordens_servico"][os_selecionada]
            
            # Informacoes gerais
            st.subheader(f"Relatorio da OS: {os_selecionada}")
            
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Produto:** {os_data['produto']}")
                st.write(f"**Quantidade:** {os_data['quantidade']}")
            with col2:
                st.write(f"**Data de Criacao:** {datetime.fromisoformat(os_data['data_criacao']).strftime('%d/%m/%Y %H:%M')}")
            
            st.divider()
            
            # Tabela de tempos
            st.subheader("Tempos por Processo")
            
            tempo_total_os = 0
            for processo in PROCESSOS:
                processo_data = os_data["processos"][processo]
                tempo_atual = calcular_tempo_atual(processo_data)
                tempo_total_os += tempo_atual
                
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    st.write(f"**{processo}**")
                with col2:
                    st.write(f"{formatar_tempo(tempo_atual)}")
                with col3:
                    status_emoji = {
                        "parado": ":red_circle: Parado",
                        "rodando": ":green_circle: Rodando",
                        "pausado": ":yellow_circle: Pausado"
                    }
                    st.write(status_emoji[processo_data["status"]])
            
            st.divider()
            st.subheader(f"**Tempo Total da OS: {formatar_tempo(tempo_total_os)}**")
            
            # Botao para exportar dados
            if st.button(":inbox_tray: Exportar Relatorio JSON"):
                st.download_button(
                    label="Download JSON",
                    data=json.dumps(os_data, ensure_ascii=False, indent=2),
                    file_name=f"relatorio_os_{os_selecionada}.json",
                    mime="application/json"
                )

# Rodape
st.sidebar.markdown("---")
st.sidebar.markdown("**Sistema de Apontamento v1.0**")
st.sidebar.markdown("Desenvolvido com Streamlit")