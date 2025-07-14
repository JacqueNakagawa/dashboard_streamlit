import streamlit as st
import pandas as pd
import requests
import plotly.express as px

st.set_page_config(layout = 'wide')

def formata_numero(valor, prefixo = ''):
    for unidade in ['', 'mil']:
        if valor <1000:
            return f'{prefixo} {valor:.2f} {unidade}'
        valor /= 1000
    return f'{prefixo} {valor:.2f} milhões'

st.title('DASHBOARD DE VENDAS :shopping_trolley:')

url = 'http://labdados.com/produtos'
regioes = ['Brasil', 'Centro-Oeste', 'Nordeste', 'Norte', 'Sudeste', 'Sul']

st.sidebar.title('Filtros')
região = st.sidebar.selectbox('Região', regioes)

if região == 'Brasil':
    região = ''

todos_anos = st.sidebar.checkbox('Dados de todo o período', value = True)

if todos_anos:
    ano = ''
else: 
    ano = st.sidebar.slider('Ano', 2020, 2023)

query_string = {'regiao': região.lower(), 'ano':ano}
response = requests.get(url, params = query_string)
dados = pd.DataFrame.from_dict(response.json())
dados['Data da Compra'] = pd.to_datetime(dados['Data da Compra'], format = '%d/%m/%Y')
df = pd.DataFrame(dados)

filtro_vendedores = st.sidebar.multiselect('Vendedores', dados['Vendedor'].unique())
if filtro_vendedores:
    dados = dados[dados['Vendedor'].isin(filtro_vendedores)]

## Tabelas
# Tabelas de Receita
receita_estados = dados.groupby('Local da compra')[['Preço']].sum()
receita_estados = dados.drop_duplicates(subset= 'Local da compra')[['Local da compra', 'lat', 'lon']].merge(receita_estados, left_on='Local da compra', right_index= True).sort_values('Preço', ascending= False)

receita_mensal = dados.set_index('Data da Compra').groupby(pd.Grouper(freq = 'M'))['Preço'].sum().reset_index()
receita_mensal['Ano'] = receita_mensal['Data da Compra'].dt.year
receita_mensal['Mes'] = receita_mensal['Data da Compra'].dt.month_name() 

receita_categorias = dados.groupby('Categoria do Produto')[['Preço']].sum().sort_values('Preço', ascending = False)


# Tabelas de quantidade de vendas
qtd_estados = dados.groupby('Local da compra')[['Preço']].count()
qtd_estados = dados.drop_duplicates(subset= 'Local da compra')[['Local da compra', 'lat', 'lon']].merge(qtd_estados, left_on='Local da compra', right_index= True).sort_values('Preço', ascending= False)


qtd_mensal = pd.DataFrame(dados.set_index('Data da Compra').groupby(pd.Grouper(freq = 'M'))['Preço'].count()).reset_index()
qtd_mensal['Ano'] = qtd_mensal['Data da Compra'].dt.year
qtd_mensal['Mes'] = qtd_mensal['Data da Compra'].dt.month_name()

qtd_categorias = pd.DataFrame(dados.groupby('Categoria do Produto')['Preço'].count().sort_values(ascending = False))

# Tabela vendedores
vendedores = pd.DataFrame(dados.groupby('Vendedor')['Preço'].agg(['sum', 'count']))

## Gráficos
fig_mapa_receita = px.scatter_geo(receita_estados,
                                  lat = 'lat',
                                  lon = 'lon',
                                  scope = 'south america',
                                  size = 'Preço',
                                  template = 'seaborn',
                                  hover_name = 'Local da compra',
                                  hover_data = {'lat' : False, 'lon' : False},
                                  title = 'Receita por Estado')

fig_receita_mensal = px.line(receita_mensal,
                             x = "Mes",
                             y = 'Preço',
                             markers = True,
                             range_y = (0, receita_mensal.max()),
                             color = 'Ano',
                             line_dash = 'Ano',
                             title = 'Receita Mensal')

fig_receita_mensal.update_layout(yaxis_title = 'Receita')

fig_receita_estados = px.bar(receita_estados.head(),
                             x = 'Local da compra',
                             y = 'Preço',
                             text_auto = True,
                             title = 'Top Estados (receita)')

fig_receita_estados.update_layout(yaxis_title = 'Receita')

fig_receita_categorias = px.bar(receita_categorias,
                                text_auto = True,
                                title = 'Receita por Categoria')

fig_receita_categorias.update_layout(yaxis_title = 'Receita')

# Gráficos quantidade vendida
fig_mapa_qtd = px.scatter_geo(qtd_estados,
                                  lat = 'lat',
                                  lon = 'lon',
                                  scope = 'south america',
                                  size = 'Preço',
                                  template = 'seaborn',
                                  hover_name = 'Local da compra',
                                  hover_data = {'lat' : False, 'lon' : False},
                                  title = 'Quantidade por Estado')

fig_qtd_mensal = px.line(qtd_mensal,
                             x = "Mes",
                             y = 'Preço',
                             markers = True,
                             range_y = (0, qtd_mensal.max()),
                             color = 'Ano',
                             line_dash = 'Ano',
                             title = 'Quantidade Mensal')

fig_qtd_mensal.update_layout(yaxis_title = 'Quantidade')

fig_qtd_estados = px.bar(qtd_estados.head(),
                             x ='Local da compra',
                             y = 'Preço',
                             text_auto = True,
                             title = 'Top 5 estados'
)

fig_qtd_estados.update_layout(yaxis_title='Quantidade de vendas')

fig_qtd_categorias = px.bar(qtd_categorias, 
                                text_auto = True,
                                title = 'Quantidade por categoria')
fig_qtd_categorias.update_layout(showlegend=False, yaxis_title='Quantidade de vendas')


## Visualização no Streamlit

aba1, aba2, aba3 = st.tabs(['Receita', 'Quantidade de Vendas', 'Vendedores'])

with aba1:
    coluna1, coluna2 = st.columns(2)
    with coluna1: 
        st.metric('Receita', formata_numero(dados['Preço'].sum(), 'R$'))
        st.plotly_chart(fig_mapa_receita, use_container_width = True)
        st.plotly_chart(fig_receita_estados, use_container_width = True)
    with coluna2:
        st.metric('Quantidade de vendas', formata_numero(dados.shape[0]))
        st.plotly_chart(fig_receita_mensal, use_container_width = True)
        st.plotly_chart(fig_receita_categorias, use_container_width = True)

with aba2:
    coluna1, coluna2 = st.columns(2)
    with coluna1:         
        st.metric('Receita', formata_numero(dados['Preço'].sum(), 'R$'))
        st.plotly_chart(fig_mapa_qtd, use_container_width = True)
        st.plotly_chart(fig_qtd_estados, use_container_width = True)

    with coluna2:
        st.metric('Quantidade de vendas', formata_numero(dados.shape[0]))
        st.plotly_chart(fig_qtd_mensal, use_container_width = True)
        st.plotly_chart(fig_qtd_categorias, use_container_width = True)

with aba3:
    qtd_vendedores = st.number_input('Quantidade de vendedores', 2, 10, 5)
    coluna1, coluna2 = st.columns(2)
    with coluna1: 
        st.metric('Receita', formata_numero(dados['Preço'].sum(), 'R$'))
        fig_receita_vendedores = px.bar(vendedores[['sum']].sort_values('sum', ascending = False).head(qtd_vendedores),
                                        x = 'sum',
                                        y = vendedores[['sum']].sort_values('sum', ascending = False).head(qtd_vendedores).index,
                                        text_auto = True,
                                        title = f'Top {qtd_vendedores} vendedores (receita)')
        st.plotly_chart(fig_receita_vendedores)

    with coluna2:
        st.metric('Quantidade de vendas', formata_numero(dados.shape[0]))
        fig_vendas_vendedores = px.bar(vendedores[['count']].sort_values('count', ascending = False).head(qtd_vendedores),
                                        x = 'count',
                                        y = vendedores[['count']].sort_values('count', ascending = False).head(qtd_vendedores).index,
                                        text_auto = True,
                                        title = f'Top {qtd_vendedores} vendedores (Qtd vendas)')
        st.plotly_chart(fig_vendas_vendedores)


st.dataframe(dados)