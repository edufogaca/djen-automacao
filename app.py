import streamlit as st
import requests
import pandas as pd
import re
import html

# Configuração para telas largas
st.set_page_config(page_title="Consulta DJEN", layout="wide", page_icon="⚖️")

st.title("⚖️ Painel de Comunicações - DJEN")
st.markdown("Consulta avançada de processos e editais.")
st.divider()

# --- FUNÇÃO PARA LIMPAR O HTML DO TEXTO ---
def limpar_texto_juridico(texto_bruto):
    if not isinstance(texto_bruto, str):
        return ""
    # Substitui as tags HTML por um espaço em branco
    texto_limpo = re.sub(r'<.*?>', ' ', texto_bruto)
    # Converte códigos especiais (como &nbsp;) para texto normal
    texto_limpo = html.unescape(texto_limpo)
    # Remove espaços duplos e quebras de linha excessivas
    texto_limpo = re.sub(r'\s+', ' ', texto_limpo).strip()
    return texto_limpo

# --- BARRA LATERAL: TODOS OS FILTROS ---
with st.sidebar:
    st.header("Filtros de Pesquisa")
    
    st.subheader("Dados do Processo")
    numero_processo = st.text_input("Número do Processo (com máscara)")
    sigla_tribunal = st.text_input("Sigla do Tribunal (ex: TJRS, TRT4)")
    nome_parte = st.text_input("Nome da Parte")
    
    st.subheader("Dados do Advogado")
    nome_advogado = st.text_input("Nome do Advogado")
    col1, col2 = st.columns(2)
    with col1:
        numero_oab = st.text_input("Número OAB")
    with col2:
        uf_oab = st.text_input("UF da OAB (ex: RS)")
        
    st.subheader("Data de Disponibilização")
    col3, col4 = st.columns(2)
    with col3:
        data_inicio = st.date_input("Data Início", value=None)
    with col4:
        data_fim = st.date_input("Data Fim", value=None)
        
    st.subheader("Filtros Específicos")
    numero_comunicacao = st.number_input("Número da Comunicação", value=0, step=1, help="Deixe 0 para ignorar")
    orgao_id = st.number_input("ID do Órgão", value=0, step=1, help="Deixe 0 para ignorar")
    
    meio_opcoes = {"Ambos": None, "Edital (E)": "E", "Diário Eletrônico (D)": "D"}
    meio_selecionado = st.selectbox("Meio de Comunicação", options=list(meio_opcoes.keys()))
    
    st.subheader("Paginação")
    pagina = st.number_input("Página", value=1, min_value=1, step=1)
    itens_pagina = st.number_input("Itens por página (5 a 100)", value=10, min_value=5, max_value=100, step=1)

    buscar = st.button("Buscar Comunicações", type="primary", use_container_width=True)

# --- ÁREA PRINCIPAL: PROCESSAMENTO E RESULTADOS ---
if buscar:
    parametros_textuais = [sigla_tribunal, nome_parte, nome_advogado, numero_oab, numero_processo]
    
    if not any(parametros_textuais) and itens_pagina > 5:
        st.warning("⚠️ A API exige que você preencha pelo menos um campo textual OU limite a busca a no máximo 5 itens por página.")
    else:
        with st.spinner("Consultando a base do DJEN..."):
            url = "https://comunicaapi.pje.jus.br/api/v1/comunicacao"
            
            params = {
                "itensPorPagina": itens_pagina,
                "pagina": pagina
            }
            
            if numero_processo: params["numeroProcesso"] = numero_processo
            if sigla_tribunal: params["siglaTribunal"] = sigla_tribunal
            if nome_parte: params["nomeParte"] = nome_parte
            if nome_advogado: params["nomeAdvogado"] = nome_advogado
            if numero_oab: params["numeroOab"] = numero_oab
            if uf_oab: params["ufOab"] = uf_oab
            if data_inicio: params["dataDisponibilizacaoInicio"] = data_inicio.strftime("%Y-%m-%d")
            if data_fim: params["dataDisponibilizacaoFim"] = data_fim.strftime("%Y-%m-%d")
            if numero_comunicacao > 0: params["numeroComunicacao"] = numero_comunicacao
            if orgao_id > 0: params["orgaoId"] = orgao_id
            
            meio_valor = meio_opcoes[meio_selecionado]
            if meio_valor: params["meio"] = meio_valor

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }

            try:
                response = requests.get(url, params=params, headers=headers)
                
                if response.status_code == 200:
                    dados = response.json()
                    total_encontrado = dados.get("count", 0)
                    
                    if total_encontrado > 0:
                        st.success(f"✅ {total_encontrado} registro(s) encontrado(s)!")
                        
                        itens = dados.get("items", [])
                        df = pd.DataFrame(itens)
                        
                        # Aplica a limpeza na coluna texto
                        if 'texto' in df.columns:
                            df['texto'] = df['texto'].apply(limpar_texto_juridico)
                        
                        # Define os nomes bonitos para as colunas
                        colunas_desejadas = {
                            'data_disponibilizacao': 'Data',
                            'siglaTribunal': 'Tribunal',
                            'numero_processo': 'Processo',
                            'tipoComunicacao': 'Tipo',
                            'nomeOrgao': 'Órgão',
                            'texto': 'Conteúdo da Intimação'
                        }
                        
                        # Filtra e renomeia apenas as colunas que vieram na resposta
                        colunas_presentes = [c for c in colunas_desejadas.keys() if c in df.columns]
                        df_exibicao = df[colunas_presentes].rename(columns=colunas_desejadas)
                        
                        # Exibe a tabela com configurações avançadas
                        st.dataframe(
                            df_exibicao, 
                            use_container_width=True, 
                            hide_index=True,
                            column_config={
                                "Conteúdo da Intimação": st.column_config.TextColumn(
                                    "Conteúdo da Intimação",
                                    width="large" # Dá mais espaço para a coluna de texto
                                )
                            }
                        )
                        
                    else:
                        st.info("Nenhuma comunicação encontrada com os filtros informados.")
                        
                elif response.status_code == 429:
                    st.error("🚨 Limite de requisições atingido. O DJEN bloqueia acessos muito rápidos. Aguarde 1 minuto e tente novamente.")
                elif response.status_code == 403:
                    st.error("🚨 Erro 403: Acesso Negado.")
                else:
                    st.error(f"❌ Erro na API do DJEN: Código {response.status_code}")
                    
            except Exception as e:
                st.error(f"Erro de comunicação de rede: {e}")
