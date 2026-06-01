import streamlit as st
import requests
import pandas as pd

# Configuração da página para usar todo o espaço (ótimo para telas ultrawide!)
st.set_page_config(page_title="Consulta DJEN", layout="wide", page_icon="⚖️")

st.title("⚖️ Painel de Comunicações - DJEN")
st.markdown("Consulta unificada de processos e editais do Diário de Justiça Eletrônico Nacional.")
st.divider()

# Menu lateral para os filtros
with st.sidebar:
    st.header("Filtros de Pesquisa")
    numero_processo = st.text_input("Número do Processo (com máscara)")
    sigla_tribunal = st.text_input("Sigla do Tribunal (ex: TRF4, TJRS)")
    nome_advogado = st.text_input("Nome do Advogado")
    
    buscar = st.button("Buscar Comunicações", type="primary")

# Área principal onde os resultados vão aparecer
if buscar:
    # A API exige pelo menos um parâmetro válido para busca
    if not numero_processo and not sigla_tribunal and not nome_advogado:
        st.warning("⚠️ Preencha pelo menos um campo para realizar a busca.")
    else:
        with st.spinner("Consultando a base do DJEN..."):
            # Endpoint público de comunicações
            url = "https://comunicaapi.pje.jus.br/api/v1/comunicacao"
            
            # Montando os parâmetros da requisição
            params = {
                "itensPorPagina": 10
            }
            if numero_processo: params["numeroProcesso"] = numero_processo
            if sigla_tribunal: params["siglaTribunal"] = sigla_tribunal
            if nome_advogado: params["nomeAdvogado"] = nome_advogado

            try:
                response = requests.get(url, params=params)
                
                if response.status_code == 200:
                    dados = response.json()
                    total_encontrado = dados.get("count", 0)
                    
                    if total_encontrado > 0:
                        st.success(f"✅ {total_encontrado} registro(s) encontrado(s)!")
                        
                        # Extraindo a lista de itens e transformando num DataFrame
                        itens = dados.get("items", [])
                        df = pd.DataFrame(itens)
                        
                        # Selecionando e renomeando as colunas para ficar bonito
                        colunas_desejadas = ["data_disponibilizacao", "siglaTribunal", "tipoComunicacao", "numero_processo", "meio"]
                        df_exibicao = df[[c for c in colunas_desejadas if c in df.columns]]
                        df_exibicao.columns = ["Data", "Tribunal", "Tipo", "Processo", "Meio"]
                        
                        # Exibindo a tabela estilizada
                        st.dataframe(df_exibicao, use_container_width=True, hide_index=True)
                        
                    else:
                        st.info("Nenhuma comunicação encontrada com os filtros informados.")
                        
                elif response.status_code == 429:
                    st.error("🚨 Limite de requisições atingido. O DJEN bloqueia acessos muito rápidos. Aguarde 1 minuto e tente novamente.")
                else:
                    st.error(f"❌ Erro na API do DJEN: Código {response.status_code}")
                    
            except Exception as e:
                st.error(f"Erro de conexão: {e}")
