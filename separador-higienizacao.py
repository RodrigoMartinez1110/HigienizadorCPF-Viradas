import pandas as pd
import streamlit as st

# Configurações iniciais
st.set_page_config(page_title="Processador de Arquivos", layout="wide")

# Função para carregar arquivos
@st.cache_data
def carregar_arquivos(arquivos):
    lista = []
    for arquivo in arquivos:
        base = pd.read_csv(arquivo, sep=',', low_memory=False)
        lista.append(base)
    base_final = pd.concat(lista, ignore_index=True)
    return base_final

# Função para gerar os arquivos
def gerar_arquivos_filtrados(base, tipo_planilha):
    colunas_iguais = base['MG_Emprestimo_Disponivel'].equals(base['MG_Emprestimo_Total'])
    cpfs_classificados = set()

    if colunas_iguais:
        negativos = base[base['MG_Emprestimo_Disponivel'] < 0]
        cpfs_classificados.update(negativos['CPF'].tolist())
        
        menores_50 = base[
            (base['MG_Emprestimo_Disponivel'] < 50) & 
            ~base['CPF'].isin(cpfs_classificados)
        ]
        cpfs_classificados.update(menores_50['CPF'].tolist())
        
        menores_300 = base[
            (base['MG_Emprestimo_Disponivel'] < 300) & 
            (base['MG_Emprestimo_Disponivel'] >= 50) & 
            ~base['CPF'].isin(cpfs_classificados)
        ]
        cpfs_classificados.update(menores_300['CPF'].tolist())
        
        menores_500 = base[
            (base['MG_Emprestimo_Disponivel'] < 500) & 
            (base['MG_Emprestimo_Disponivel'] >= 300) & 
            ~base['CPF'].isin(cpfs_classificados)
        ]
        cpfs_classificados.update(menores_500['CPF'].tolist())
        
        restante = base[
            (base['MG_Emprestimo_Disponivel'] >= 500) & 
            ~base['CPF'].isin(cpfs_classificados)
        ]

    else:
        negativos = base[base['MG_Emprestimo_Disponivel'] < 0]
        cpfs_classificados.update(negativos['CPF'].tolist())

        menores_50 = base[
            (base['MG_Emprestimo_Disponivel'] < 50) & 
            ~base['CPF'].isin(cpfs_classificados)
        ]
        cpfs_classificados.update(menores_50['CPF'].tolist())

        super_tomador = base[
            (base['MG_Emprestimo_Disponivel'] / base['MG_Emprestimo_Total'] < 0.35) & 
            (base['MG_Emprestimo_Disponivel'] >= 50) & 
            ~base['CPF'].isin(cpfs_classificados)
        ]
        cpfs_classificados.update(super_tomador['CPF'].tolist())
        
        tomador = base[
            (base['MG_Emprestimo_Disponivel'] != base['MG_Emprestimo_Total']) & 
            ~base['CPF'].isin(cpfs_classificados)
        ]

        restante = base[
            ~base['CPF'].isin(cpfs_classificados)
        ]

    # Ajustar as colunas conforme o tipo de planilha
    arquivos = {
        "negativos": negativos,
        "menores_50": menores_50,
        "super_tomador": super_tomador if not colunas_iguais else None,
        "menores_300": menores_300 if colunas_iguais else None,
        "menores_500": menores_500 if colunas_iguais else None,
        "tomador": tomador if not colunas_iguais else None,
        "restante": restante
    }
    
    for key, dataframe in arquivos.items():
        if dataframe is not None:
            if tipo_planilha == "Molde CPF":
                arquivos[key] = dataframe[['CPF']].rename(columns={'CPF': 'cpf'})
            elif tipo_planilha == "Molde CPF e Matrícula":
                arquivos[key] = dataframe[['CPF', 'Matricula']].rename(columns={'CPF': 'cpf', 'Matricula': 'matricula'})
                arquivos[key]['senha'] = ''
                arquivos[key]['nome'] = ''
                # Reordenar colunas
                arquivos[key] = arquivos[key][['cpf', 'senha', 'matricula', 'nome']]
    
    return arquivos

# Interface do Streamlit
st.title("Processador de Arquivos CSV")

# Upload dos arquivos
st.sidebar.title("Configurações")
arquivos = st.sidebar.file_uploader("Arraste e solte seus arquivos CSV aqui", accept_multiple_files=True, type=['csv'])
st.sidebar.write("---")

# Tipo de planilha
tipo_planilha = st.sidebar.radio("Selecione o tipo de planilha que deseja retornar:", ["Molde CPF", "Molde CPF e Matrícula"])

if arquivos:
    # Carregar os dados
    base = carregar_arquivos(arquivos)
    st.write("---")
    st.write("### Pré-visualização dos dados carregados")
    st.dataframe(base.head())
    st.write(base.shape)
    st.write("---")

    base = base.sort_values(by='MG_Emprestimo_Disponivel', ascending=True)
    base = base.drop_duplicates(subset='CPF')
    base = base.reset_index(drop=True)

    # Gerar os arquivos filtrados
    arquivos_filtrados = gerar_arquivos_filtrados(base, tipo_planilha)
    convenio = base.loc[1, 'Convenio']

    st.write(f"### Arquivos Gerados para Download - {convenio.upper()}")
    
    
    for nome, dataframe in arquivos_filtrados.items():
        if dataframe is not None:
            csv = dataframe.to_csv(index=False, sep=',')
            st.download_button(
                label=f"Baixar {nome}.csv",
                data=csv,
                file_name=f"{convenio} - {nome}.csv",
                mime="text/csv"
            )
