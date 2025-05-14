import streamlit as st
import pandas as pd
import pyodbc
import time
from streamlit_autorefresh import st_autorefresh

# Configuração da conexão
server = r"VMSSQL01\INSTANCIA"
database = "INJET"
username = "consulta_injet"
password = "1nj&t_M0R"
driver = "{SQL Server}"

# Conectar ao banco
def conectar_sql():
    return pyodbc.connect(
        f"DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}"
    )

# Buscar máquinas com alerta com base no galpão
def buscar_alertas():
    conexao = conectar_sql()
    
    # A consulta base
    consulta = """
        SELECT DISTINCT cdmaquina, StParNaoInf, TmpUltParada, CdMolde, EfiCic, StMaquina, DsGalpao
        FROM ViewWMTR
        WHERE(
                (StParNaoInf = 1 AND TmpUltParada > 300)
                OR
                ((EfiCic > 150 OR EfiCic < 80) AND StMaquina = 1)
            )
    """
    
    
    consulta += " AND DsGalpao = ?"
    df = pd.read_sql(consulta, conexao, params=["INJET WEB"])
    
    conexao.close()
    return df

# Formatar tempo em segundos para hh:mm:ss
def formatar_segundos(segundos):
    if pd.isna(segundos):
        return ""
    segundos = int(segundos)
    horas = segundos // 3600
    minutos = (segundos % 3600) // 60
    segundos_restantes = segundos % 60
    return f"{horas:02}:{minutos:02}:{segundos_restantes:02}"

# Configuração da página
st.set_page_config(page_title="Alertas de Máquinas", layout="wide")
inicio = time.time()

# Cache de 40s com entrada do filtro
@st.cache_data(ttl=10)
def buscar_dados_filtrados():
    return buscar_alertas()

df = buscar_dados_filtrados()


# Traduz campos
df['StParNaoInf'] = df['StParNaoInf'].apply(lambda x: 'PARADA NÃO INFORMADA' if x == 1 else '')
df['StMaquina'] = df['StMaquina'].apply(lambda x: 'PRODUZINDO' if x == 1 else 'PARADO')
df['TmpUltParada'] = df['TmpUltParada'].apply(formatar_segundos)

# Verifique se os dados estão corretos
#st.write(df)

# Legenda
st.markdown(""" 
#### 🛑 ALERTAS INJET - INJET WEB
**Legenda:** 

- 🔴 **Vermelho**: Ciclo fora do padrão (Eficiência de Ciclo < 80 ou > 150)  
- 🟡 **Amarelo**: Parada não informada  
""")

# Separação em colunas
col1, col2 = st.columns(2)

# Exibir alertas de ciclo fora do padrão
with col1:
    st.subheader("🚨 Alertas de Ciclo Fora do Padrão")
    for _, row in df.iterrows():
        if (row['EfiCic'] > 150 or row['EfiCic'] < 80) and row['StMaquina'] == 'PRODUZINDO':
            st.error(f"Máquina {row['cdmaquina']} está com **ciclo fora do padrão** (Eficiência: {row['EfiCic'] / 100:.1%}).")

# Exibir alertas de parada não informada
with col2:
    st.subheader("⚠️ Alertas de Parada Não Informada")
    for _, row in df.iterrows():
        if row['StParNaoInf'] == 'PARADA NÃO INFORMADA' and int(row['TmpUltParada'].split(':')[0])*3600 + int(row['TmpUltParada'].split(':')[1])*60 + int(row['TmpUltParada'].split(':')[2]) > 300:
            st.warning(f"Máquina {row['cdmaquina']} está com **parada não informada** há {row['TmpUltParada']}.")


st_autorefresh(interval=10000, key="auto_refresh")



# Espera até completar o tempo mínimo de atualização
#tempo_decorrido = time.time() - inicio
#if tempo_decorrido < 5:
#    time.sleep(5 - tempo_decorrido)

# Atualiza a página
#st.rerun()
