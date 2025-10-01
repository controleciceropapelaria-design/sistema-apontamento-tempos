import streamlit as st
import json
import os
from datetime import datetime
import time

# Configuracao da pagina
st.set_page_config(
    page_title="Sistema de Apontamento de Tempos",
    layout="wide"
)

# Arquivo para dados
DATA_FILE = "dados_producao.json"

# Processos
PROCESSOS = [
    "Aviamento de capa",
    "Aviamento de miolo", 
    "Encadernacao e Finalizacao",
    "Montagem de capa",
    "Montagem de Miolo",
    "Montagem do kit"
]

def carregar_dados():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except:
            return {"ordens_servico": {}}
    return {"ordens_servico": {}}

def salvar_dados(dados):
    with open(DATA_FILE, 'w') as f:
        json.dump(dados, f, indent=2)

def inicializar_os(numero_os, produto, quantidade):
    dados = carregar_dados()
    dados["ordens_servico"][numero_os] = {
        "produto": produto,
        "quantidade": quantidade,
        "data_criacao": datetime.now().isoformat(),
        "processos": {}
    }
    
    for processo in PROCESSOS:
        dados["ordens_servico"][numero_os]["processos"][processo] = {
            "tempo_total": 0,
            "status": "parado",
            "inicio_atual": None
        }
    
    salvar_dados(dados)
    return dados

def atualizar_tempo_processo(numero_os, processo):
    dados = carregar_dados()
    if numero_os not in dados["ordens_servico"]:
        return dados
    
    processo_data = dados["ordens_servico"][numero_os]["processos"][processo]
    
    if processo_data["status"] == "rodando" and processo_data["inicio_atual"]:
        inicio = datetime.fromisoformat(processo_data["inicio_atual"])
        tempo_decorrido = (datetime.now() - inicio).total_seconds()
        processo_data["tempo_total"] += tempo_decorrido
        processo_data["inicio_atual"] = datetime.now().isoformat()
    
    salvar_dados(dados)
    return dados

def iniciar_processo(numero_os, processo):
    dados = atualizar_tempo_processo(numero_os, processo)
    dados["ordens_servico"][numero_os]["processos"][processo]["status"] = "rodando"
    dados["ordens_servico"][numero_os]["processos"][processo]["inicio_atual"] = datetime.now().isoformat()
    salvar_dados(dados)

def pausar_processo(numero_os, processo):
    dados = atualizar_tempo_processo(numero_os, processo)
    dados["ordens_servico"][numero_os]["processos"][processo]["status"] = "pausado"
    dados["ordens_servico"][numero_os]["processos"][processo]["inicio_atual"] = None
    salvar_dados(dados)

def parar_processo(numero_os, processo):
    dados = atualizar_tempo_processo(numero_os, processo)
    dados["ordens_servico"][numero_os]["processos"][processo]["status"] = "parado"
    dados["ordens_servico"][numero_os]["processos"][processo]["inicio_atual"] = None
    salvar_dados(dados)

def formatar_tempo(segundos):
    horas = int(segundos // 3600)
    minutos = int((segundos % 3600) // 60)
    segs = int(segundos % 60)
    return f"{horas:02d}:{minutos:02d}:{segs:02d}"

def calcular_tempo_atual(processo_data):
    tempo_total = processo_data["tempo_total"]
    
    if processo_data["status"] == "rodando" and processo_data["inicio_atual"]:
        inicio = datetime.fromisoformat(processo_data["inicio_atual"])
        tempo_decorrido = (datetime.now() - inicio).total_seconds()
        tempo_total += tempo_decorrido
    
    return tempo_total

# Interface principal
st.title("Sistema de Apontamento de Tempos de Producao")

# Sidebar
st.sidebar.title("Menu")
pagina = st.sidebar.selectbox("Escolha:", ["Cadastro de OS", "Apontamento", "Relatorios"])

if pagina == "Cadastro de OS":
    st.header("Cadastro de Ordem de Servico")
    
    with st.form("cadastro"):
        col1, col2 = st.columns(2)
        
        with col1:
            numero_os = st.text_input("Numero da OS:")
            produto = st.text_input("Produto:")
        
        with col2:
            quantidade = st.number_input("Quantidade:", min_value=1, value=1)
        
        if st.form_submit_button("Criar OS"):
            if numero_os and produto:
                dados = carregar_dados()
                if numero_os in dados["ordens_servico"]:
                    st.error("OS ja existe!")
                else:
                    inicializar_os(numero_os, produto, quantidade)
                    st.success("OS criada!")
            else:
                st.error("Preencha todos os campos!")

elif pagina == "Apontamento":
    st.header("Apontamento de Tempos")
    
    dados = carregar_dados()
    
    if not dados["ordens_servico"]:
        st.warning("Nenhuma OS cadastrada.")
    else:
        os_selecionada = st.selectbox("Selecione a OS:", list(dados["ordens_servico"].keys()))
        
        if os_selecionada:
            os_data = dados["ordens_servico"][os_selecionada]
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.info(f"Produto: {os_data['produto']}")
            with col2:
                st.info(f"Quantidade: {os_data['quantidade']}")
            with col3:
                st.info(f"Criada: {datetime.fromisoformat(os_data['data_criacao']).strftime('%d/%m/%Y')}")
            
            st.divider()
            
            for i, processo in enumerate(PROCESSOS):
                processo_data = os_data["processos"][processo]
                tempo_atual = calcular_tempo_atual(processo_data)
                
                col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
                
                with col1:
                    status_icon = {"parado": "🔴", "rodando": "🟢", "pausado": "🟡"}
                    st.write(f"{status_icon[processo_data['status']]} **{processo}**")
                    st.write(f"Tempo: {formatar_tempo(tempo_atual)}")
                
                with col2:
                    if st.button("Play", key=f"play_{i}", disabled=(processo_data['status'] == 'rodando')):
                        iniciar_processo(os_selecionada, processo)
                        st.rerun()
                
                with col3:
                    if st.button("Pause", key=f"pause_{i}", disabled=(processo_data['status'] != 'rodando')):
                        pausar_processo(os_selecionada, processo)
                        st.rerun()
                
                with col4:
                    if st.button("Stop", key=f"stop_{i}", disabled=(processo_data['status'] == 'parado')):
                        parar_processo(os_selecionada, processo)
                        st.rerun()
                
                with col5:
                    st.write(f"Status: {processo_data['status']}")
                
                st.divider()
            
            # Auto-refresh
            processos_rodando = any(p["status"] == "rodando" for p in os_data["processos"].values())
            if processos_rodando:
                time.sleep(1)
                st.rerun()

elif pagina == "Relatorios":
    st.header("Relatorios")
    
    dados = carregar_dados()
    
    if not dados["ordens_servico"]:
        st.warning("Nenhuma OS cadastrada.")
    else:
        os_selecionada = st.selectbox("OS:", list(dados["ordens_servico"].keys()))
        
        if os_selecionada:
            os_data = dados["ordens_servico"][os_selecionada]
            
            st.subheader(f"Relatorio: {os_selecionada}")
            
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"Produto: {os_data['produto']}")
                st.write(f"Quantidade: {os_data['quantidade']}")
            with col2:
                st.write(f"Criada: {datetime.fromisoformat(os_data['data_criacao']).strftime('%d/%m/%Y')}")
            
            st.divider()
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
                    st.write(formatar_tempo(tempo_atual))
                with col3:
                    st.write(processo_data["status"])
            
            st.divider()
            st.subheader(f"Tempo Total: {formatar_tempo(tempo_total_os)}")

st.sidebar.markdown("---")
st.sidebar.markdown("**Sistema v1.0**")