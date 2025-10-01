import streamlit as st
import pandas as pd
import os
from datetime import datetime
import time

# Configuracao da pagina
st.set_page_config(
    page_title="Sistema de Apontamento de Tempos",
    layout="wide"
)

# Arquivos CSV
OS_FILE = "ordens_servico.csv"
TEMPOS_FILE = "tempos_processos.csv"

# Processos disponiveis
PROCESSOS = [
    "Aviamento de capa",
    "Aviamento de miolo", 
    "Encadernacao e Finalizacao",
    "Montagem de capa",
    "Montagem de Miolo",
    "Montagem do kit"
]

# Status das OS
STATUS_OS = {
    "ativa": "🟢 Ativa",
    "finalizada": "🔒 Finalizada"
}

def inicializar_csvs():
    """Inicializa os arquivos CSV se nao existirem"""
    # CSV das Ordens de Servico
    if not os.path.exists(OS_FILE):
        df_os = pd.DataFrame(columns=[
            'numero_os', 'produto', 'quantidade', 'data_criacao', 'status_os'
        ])
        df_os.to_csv(OS_FILE, index=False)
    
    # CSV dos Tempos
    if not os.path.exists(TEMPOS_FILE):
        df_tempos = pd.DataFrame(columns=[
            'numero_os', 'processo', 'tempo_total_segundos', 
            'status', 'inicio_atual', 'data_atualizacao'
        ])
        df_tempos.to_csv(TEMPOS_FILE, index=False)

def carregar_os():
    """Carrega as ordens de servico do CSV"""
    try:
        df = pd.read_csv(OS_FILE)
        # Adicionar coluna status_os se nao existir (compatibilidade)
        if 'status_os' not in df.columns:
            df['status_os'] = 'ativa'
            salvar_os(df)
        return df
    except:
        return pd.DataFrame(columns=['numero_os', 'produto', 'quantidade', 'data_criacao', 'status_os'])

def carregar_tempos():
    """Carrega os tempos dos processos do CSV"""
    try:
        return pd.read_csv(TEMPOS_FILE)
    except:
        return pd.DataFrame(columns=[
            'numero_os', 'processo', 'tempo_total_segundos', 
            'status', 'inicio_atual', 'data_atualizacao'
        ])

def salvar_os(df):
    """Salva as ordens de servico no CSV"""
    df.to_csv(OS_FILE, index=False)

def salvar_tempos(df):
    """Salva os tempos dos processos no CSV"""
    df.to_csv(TEMPOS_FILE, index=False)

def criar_os(numero_os, produto, quantidade):
    """Cria uma nova ordem de servico"""
    # Verificar se OS ja existe
    df_os = carregar_os()
    if numero_os in df_os['numero_os'].values:
        return False, "OS ja existe!"
    
    # Adicionar OS
    nova_os = pd.DataFrame({
        'numero_os': [numero_os],
        'produto': [produto],
        'quantidade': [quantidade],
        'data_criacao': [datetime.now().isoformat()],
        'status_os': ['ativa']
    })
    df_os = pd.concat([df_os, nova_os], ignore_index=True)
    salvar_os(df_os)
    
    # Criar processos para a OS
    df_tempos = carregar_tempos()
    for processo in PROCESSOS:
        novo_tempo = pd.DataFrame({
            'numero_os': [numero_os],
            'processo': [processo],
            'tempo_total_segundos': [0],
            'status': ['parado'],
            'inicio_atual': [''],
            'data_atualizacao': [datetime.now().isoformat()]
        })
        df_tempos = pd.concat([df_tempos, novo_tempo], ignore_index=True)
    
    salvar_tempos(df_tempos)
    return True, "OS cadastrada com sucesso!"

def excluir_os(numero_os):
    """Exclui uma ordem de servico e todos seus tempos"""
    # Remover OS
    df_os = carregar_os()
    df_os = df_os[df_os['numero_os'] != numero_os]
    salvar_os(df_os)
    
    # Remover tempos da OS
    df_tempos = carregar_tempos()
    df_tempos = df_tempos[df_tempos['numero_os'] != numero_os]
    salvar_tempos(df_tempos)

def finalizar_os(numero_os):
    """Finaliza uma OS, impedindo alteracoes nos tempos"""
    df_os = carregar_os()
    mask = df_os['numero_os'] == numero_os
    if mask.any():
        idx = df_os[mask].index[0]
        df_os.loc[idx, 'status_os'] = 'finalizada'
        salvar_os(df_os)
        
        # Parar todos os processos em execucao
        df_tempos = carregar_tempos()
        os_mask = df_tempos['numero_os'] == numero_os
        for idx in df_tempos[os_mask].index:
            if df_tempos.loc[idx, 'status'] == 'rodando':
                # Atualizar tempo antes de parar
                if (df_tempos.loc[idx, 'inicio_atual'] and 
                    df_tempos.loc[idx, 'inicio_atual'] != ''):
                    inicio = datetime.fromisoformat(df_tempos.loc[idx, 'inicio_atual'])
                    tempo_decorrido = (datetime.now() - inicio).total_seconds()
                    df_tempos.loc[idx, 'tempo_total_segundos'] += tempo_decorrido
                
                df_tempos.loc[idx, 'status'] = 'finalizado'
                df_tempos.loc[idx, 'inicio_atual'] = ''
                df_tempos.loc[idx, 'data_atualizacao'] = datetime.now().isoformat()
        
        salvar_tempos(df_tempos)

def atualizar_tempo_processo(numero_os, processo):
    """Atualiza o tempo de um processo"""
    df_tempos = carregar_tempos()
    
    # Encontrar o processo
    mask = (df_tempos['numero_os'] == numero_os) & (df_tempos['processo'] == processo)
    
    if mask.any():
        idx = df_tempos[mask].index[0]
        
        if (df_tempos.loc[idx, 'status'] == 'rodando' and 
            df_tempos.loc[idx, 'inicio_atual'] and 
            df_tempos.loc[idx, 'inicio_atual'] != ''):
            
            # Calcular tempo decorrido
            inicio = datetime.fromisoformat(df_tempos.loc[idx, 'inicio_atual'])
            tempo_decorrido = (datetime.now() - inicio).total_seconds()
            df_tempos.loc[idx, 'tempo_total_segundos'] += tempo_decorrido
            df_tempos.loc[idx, 'inicio_atual'] = datetime.now().isoformat()
            df_tempos.loc[idx, 'data_atualizacao'] = datetime.now().isoformat()
            
            salvar_tempos(df_tempos)
    
    return df_tempos

def iniciar_processo(numero_os, processo):
    """Inicia um processo"""
    df_tempos = atualizar_tempo_processo(numero_os, processo)
    
    mask = (df_tempos['numero_os'] == numero_os) & (df_tempos['processo'] == processo)
    if mask.any():
        idx = df_tempos[mask].index[0]
        df_tempos.loc[idx, 'status'] = 'rodando'
        df_tempos.loc[idx, 'inicio_atual'] = datetime.now().isoformat()
        df_tempos.loc[idx, 'data_atualizacao'] = datetime.now().isoformat()
        salvar_tempos(df_tempos)

def pausar_processo(numero_os, processo):
    """Pausa um processo"""
    df_tempos = atualizar_tempo_processo(numero_os, processo)
    
    mask = (df_tempos['numero_os'] == numero_os) & (df_tempos['processo'] == processo)
    if mask.any():
        idx = df_tempos[mask].index[0]
        df_tempos.loc[idx, 'status'] = 'pausado'
        df_tempos.loc[idx, 'inicio_atual'] = ''
        df_tempos.loc[idx, 'data_atualizacao'] = datetime.now().isoformat()
        salvar_tempos(df_tempos)

def parar_processo(numero_os, processo):
    """Para um processo"""
    df_tempos = atualizar_tempo_processo(numero_os, processo)
    
    mask = (df_tempos['numero_os'] == numero_os) & (df_tempos['processo'] == processo)
    if mask.any():
        idx = df_tempos[mask].index[0]
        df_tempos.loc[idx, 'status'] = 'parado'
        df_tempos.loc[idx, 'inicio_atual'] = ''
        df_tempos.loc[idx, 'data_atualizacao'] = datetime.now().isoformat()
        salvar_tempos(df_tempos)

def formatar_tempo(segundos):
    """Formata segundos em HH:MM:SS"""
    horas = int(segundos // 3600)
    minutos = int((segundos % 3600) // 60)
    segs = int(segundos % 60)
    return f"{horas:02d}:{minutos:02d}:{segs:02d}"

def calcular_tempo_atual(row):
    """Calcula tempo atual incluindo tempo em execucao"""
    tempo_total = float(row['tempo_total_segundos'])
    
    if (row['status'] == 'rodando' and 
        row['inicio_atual'] and 
        row['inicio_atual'] != ''):
        
        inicio = datetime.fromisoformat(row['inicio_atual'])
        tempo_decorrido = (datetime.now() - inicio).total_seconds()
        tempo_total += tempo_decorrido
    
    return tempo_total

# Inicializar CSVs
inicializar_csvs()

# Interface principal
st.title("Sistema de Apontamento de Tempos de Producao")
st.sidebar.title("Menu")

# Adicionar informacao sobre GitHub
st.sidebar.info("💾 Dados salvos em CSV para GitHub")

pagina = st.sidebar.selectbox("Escolha:", ["Cadastro de OS", "Apontamento", "Relatorios", "Dados"])

if pagina == "Cadastro de OS":
    st.header("Cadastro de Ordem de Servico")
    
    # Formulario de cadastro
    with st.form("cadastro"):
        col1, col2 = st.columns(2)
        
        with col1:
            numero_os = st.text_input("Numero da OS:")
            produto = st.text_input("Produto:")
        
        with col2:
            quantidade = st.number_input("Quantidade:", min_value=1, value=1)
        
        if st.form_submit_button("Criar OS"):
            if numero_os and produto:
                sucesso, mensagem = criar_os(numero_os, produto, quantidade)
                if sucesso:
                    st.success(mensagem)
                    st.rerun()
                else:
                    st.error(mensagem)
            else:
                st.error("Preencha todos os campos obrigatorios!")
    
    st.divider()
    
    # Lista de OS existentes com opcao de exclusao
    st.subheader("Ordens de Servico Cadastradas")
    df_os = carregar_os()
    
    if not df_os.empty:
        for _, os_row in df_os.iterrows():
            col1, col2, col3, col4, col5 = st.columns([2, 2, 1, 1, 1])
            
            with col1:
                st.write(f"**{os_row['numero_os']}**")
            with col2:
                st.write(f"{os_row['produto']} (Qtd: {os_row['quantidade']})")
            with col3:
                status_os = os_row.get('status_os', 'ativa')
                st.write(STATUS_OS.get(status_os, status_os))
            with col4:
                data_criacao = datetime.fromisoformat(os_row['data_criacao'])
                st.write(data_criacao.strftime('%d/%m/%Y'))
            with col5:
                if st.button("🗑️ Excluir", key=f"excluir_{os_row['numero_os']}", 
                           help="Excluir esta OS e todos os tempos"):
                    excluir_os(os_row['numero_os'])
                    st.success(f"OS {os_row['numero_os']} excluida!")
                    st.rerun()
    else:
        st.info("Nenhuma OS cadastrada ainda.")

elif pagina == "Apontamento":
    st.header("Apontamento de Tempos")
    
    df_os = carregar_os()
    df_tempos = carregar_tempos()
    
    if df_os.empty:
        st.warning("Nenhuma OS cadastrada.")
    else:
        # Filtrar apenas OS ativas para selecao
        os_ativas = df_os[df_os['status_os'] != 'finalizada']
        os_finalizadas = df_os[df_os['status_os'] == 'finalizada']
        
        # Selectbox com todas as OS (ativas primeiro)
        todas_os = list(os_ativas['numero_os'].values) + list(os_finalizadas['numero_os'].values)
        
        if not todas_os:
            st.warning("Nenhuma OS disponivel.")
        else:
            os_selecionada = st.selectbox("Selecione a OS:", todas_os)
            
            if os_selecionada:
                # Info da OS
                os_info = df_os[df_os['numero_os'] == os_selecionada].iloc[0]
                status_os_atual = os_info.get('status_os', 'ativa')
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.info(f"Produto: {os_info['produto']}")
                with col2:
                    st.info(f"Quantidade: {os_info['quantidade']}")
                with col3:
                    data_criacao = datetime.fromisoformat(os_info['data_criacao'])
                    st.info(f"Criada: {data_criacao.strftime('%d/%m/%Y')}")
                with col4:
                    if status_os_atual == 'finalizada':
                        st.error("🔒 OS Finalizada")
                    else:
                        st.success("🟢 OS Ativa")
                
                # Botao de finalizar OS (apenas se ativa)
                if status_os_atual != 'finalizada':
                    st.divider()
                    col_finalizar1, col_finalizar2, col_finalizar3 = st.columns([1, 2, 1])
                    with col_finalizar2:
                        if st.button("🔒 FINALIZAR OS", 
                                   help="Finaliza a OS e bloqueia alteracoes nos tempos",
                                   type="secondary"):
                            finalizar_os(os_selecionada)
                            st.success("OS finalizada com sucesso!")
                            st.rerun()
                
                st.divider()
                
                # Processos
                for i, processo in enumerate(PROCESSOS):
                    processo_mask = (df_tempos['numero_os'] == os_selecionada) & (df_tempos['processo'] == processo)
                    
                    if processo_mask.any():
                        processo_data = df_tempos[processo_mask].iloc[0]
                        tempo_atual = calcular_tempo_atual(processo_data)
                        
                        col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
                        
                        with col1:
                            if processo_data['status'] == 'finalizado':
                                status_icon = "🔒"
                                status_text = "Finalizado"
                            else:
                                status_icon = {"parado": "🔴", "rodando": "🟢", "pausado": "🟡"}[processo_data['status']]
                                status_text = processo_data['status']
                            
                            st.write(f"{status_icon} **{processo}**")
                            st.write(f"Tempo: {formatar_tempo(tempo_atual)}")
                        
                        # Botoes apenas se OS nao estiver finalizada
                        if status_os_atual != 'finalizada' and processo_data['status'] != 'finalizado':
                            with col2:
                                if st.button("▶️ Play", key=f"play_{i}", 
                                           disabled=(processo_data['status'] == 'rodando')):
                                    iniciar_processo(os_selecionada, processo)
                                    st.rerun()
                            
                            with col3:
                                if st.button("⏸️ Pause", key=f"pause_{i}", 
                                           disabled=(processo_data['status'] != 'rodando')):
                                    pausar_processo(os_selecionada, processo)
                                    st.rerun()
                            
                            with col4:
                                if st.button("⏹️ Stop", key=f"stop_{i}", 
                                           disabled=(processo_data['status'] == 'parado')):
                                    parar_processo(os_selecionada, processo)
                                    st.rerun()
                        else:
                            with col2:
                                st.write("🔒")
                            with col3:
                                st.write("🔒")
                            with col4:
                                st.write("🔒")
                        
                        with col5:
                            if processo_data['status'] == 'finalizado':
                                st.write("🔒 Finalizado")
                            else:
                                st.write(f"Status: {processo_data['status']}")
                        
                        st.divider()
                
                # Auto-refresh apenas para OS ativas
                if status_os_atual != 'finalizada':
                    os_tempos = df_tempos[df_tempos['numero_os'] == os_selecionada]
                    processos_rodando = any(os_tempos['status'] == 'rodando')
                    if processos_rodando:
                        time.sleep(1)
                        st.rerun()

elif pagina == "Relatorios":
    st.header("Relatorios")
    
    df_os = carregar_os()
    df_tempos = carregar_tempos()
    
    if df_os.empty:
        st.warning("Nenhuma OS cadastrada.")
    else:
        os_selecionada = st.selectbox("OS:", df_os['numero_os'].values)
        
        if os_selecionada:
            os_info = df_os[df_os['numero_os'] == os_selecionada].iloc[0]
            status_os_atual = os_info.get('status_os', 'ativa')
            
            st.subheader(f"Relatorio: {os_selecionada}")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"**Produto:** {os_info['produto']}")
                st.write(f"**Quantidade:** {os_info['quantidade']}")
            with col2:
                data_criacao = datetime.fromisoformat(os_info['data_criacao'])
                st.write(f"**Criada:** {data_criacao.strftime('%d/%m/%Y')}")
            with col3:
                st.write(f"**Status:** {STATUS_OS.get(status_os_atual, status_os_atual)}")
            
            st.divider()
            st.subheader("Tempos por Processo")
            
            tempo_total_os = 0
            os_tempos = df_tempos[df_tempos['numero_os'] == os_selecionada]
            
            for _, processo_data in os_tempos.iterrows():
                tempo_atual = calcular_tempo_atual(processo_data)
                tempo_total_os += tempo_atual
                
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    st.write(f"**{processo_data['processo']}**")
                with col2:
                    st.write(formatar_tempo(tempo_atual))
                with col3:
                    if processo_data['status'] == 'finalizado':
                        st.write("🔒 Finalizado")
                    else:
                        status_display = {
                            'parado': '🔴 Parado',
                            'rodando': '🟢 Rodando', 
                            'pausado': '🟡 Pausado'
                        }
                        st.write(status_display.get(processo_data['status'], processo_data['status']))
            
            st.divider()
            st.subheader(f"⏱️ **Tempo Total: {formatar_tempo(tempo_total_os)}**")
            
            # Resumo adicional para OS finalizadas
            if status_os_atual == 'finalizada':
                st.success("✅ Esta OS foi finalizada e seus tempos estao bloqueados para alteracao.")

elif pagina == "Dados":
    st.header("Visualizacao dos Dados CSV")
    
    tab1, tab2 = st.tabs(["Ordens de Servico", "Tempos dos Processos"])
    
    with tab1:
        st.subheader("ordens_servico.csv")
        df_os = carregar_os()
        if not df_os.empty:
            st.dataframe(df_os, use_container_width=True)
            
            # Download CSV
            csv_os = df_os.to_csv(index=False)
            st.download_button(
                label="Download CSV Ordens",
                data=csv_os,
                file_name="ordens_servico.csv",
                mime="text/csv"
            )
        else:
            st.info("Nenhuma ordem de servico cadastrada")
    
    with tab2:
        st.subheader("tempos_processos.csv")
        df_tempos = carregar_tempos()
        if not df_tempos.empty:
            st.dataframe(df_tempos, use_container_width=True)
            
            # Download CSV
            csv_tempos = df_tempos.to_csv(index=False)
            st.download_button(
                label="Download CSV Tempos",
                data=csv_tempos,
                file_name="tempos_processos.csv",
                mime="text/csv"
            )
        else:
            st.info("Nenhum tempo registrado")

st.sidebar.markdown("---")
st.sidebar.markdown("**Sistema v2.0 - GitHub Ready**")
st.sidebar.markdown("Desenvolvido com Streamlit + CSV")