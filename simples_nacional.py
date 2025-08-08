import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from typing import Dict, Tuple, List

# Configuração da página
st.set_page_config(
    page_title="Apurador Simples Nacional Completo – PAC",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Tabelas do Simples Nacional 2025 (baseadas nas fontes: Contabilizei, Cora, eSimples)
# Anexo I - Comércio
ANEXO_I = {
    "faixas": [
        {"inicio": 0, "fim": 180000, "aliquota": 4.00, "deducao": 0},
        {"inicio": 180000.01, "fim": 360000, "aliquota": 7.30, "deducao": 5940},
        {"inicio": 360000.01, "fim": 720000, "aliquota": 9.50, "deducao": 13860},
        {"inicio": 720000.01, "fim": 1800000, "aliquota": 10.70, "deducao": 22500},
        {"inicio": 1800000.01, "fim": 3600000, "aliquota": 14.30, "deducao": 87300},
        {"inicio": 3600000.01, "fim": 4800000, "aliquota": 19.00, "deducao": 378000}
    ]
}

# Anexo II - Indústria
ANEXO_II = {
    "faixas": [
        {"inicio": 0, "fim": 180000, "aliquota": 4.50, "deducao": 0},
        {"inicio": 180000.01, "fim": 360000, "aliquota": 7.80, "deducao": 5940},
        {"inicio": 360000.01, "fim": 720000, "aliquota": 10.00, "deducao": 13860},
        {"inicio": 720000.01, "fim": 1800000, "aliquota": 11.20, "deducao": 22500},
        {"inicio": 1800000.01, "fim": 3600000, "aliquota": 14.70, "deducao": 87300},
        {"inicio": 3600000.01, "fim": 4800000, "aliquota": 30.00, "deducao": 720000}
    ]
}

# Anexo III - Serviços com Fator R
ANEXO_III = {
    "faixas": [
        {"inicio": 0, "fim": 180000, "aliquota": 6.00, "deducao": 0},
        {"inicio": 180000.01, "fim": 360000, "aliquota": 11.20, "deducao": 9360},
        {"inicio": 360000.01, "fim": 720000, "aliquota": 13.20, "deducao": 17640},
        {"inicio": 720000.01, "fim": 1800000, "aliquota": 16.00, "deducao": 35640},
        {"inicio": 1800000.01, "fim": 3600000, "aliquota": 21.00, "deducao": 125640},
        {"inicio": 3600000.01, "fim": 4800000, "aliquota": 33.00, "deducao": 648000}
    ]
}

# Anexo IV - Serviços Especializados
ANEXO_IV = {
    "faixas": [
        {"inicio": 0, "fim": 180000, "aliquota": 4.50, "deducao": 0},
        {"inicio": 180000.01, "fim": 360000, "aliquota": 9.00, "deducao": 8100},
        {"inicio": 360000.01, "fim": 720000, "aliquota": 10.20, "deducao": 12420},
        {"inicio": 720000.01, "fim": 1800000, "aliquota": 11.40, "deducao": 21600},
        {"inicio": 1800000.01, "fim": 3600000, "aliquota": 14.70, "deducao": 85500},
        {"inicio": 3600000.01, "fim": 4800000, "aliquota": 18.00, "deducao": 720000}
    ]
}

# Anexo V - Outros Serviços
ANEXO_V = {
    "faixas": [
        {"inicio": 0, "fim": 180000, "aliquota": 15.50, "deducao": 0},
        {"inicio": 180000.01, "fim": 360000, "aliquota": 18.00, "deducao": 4500},
        {"inicio": 360000.01, "fim": 720000, "aliquota": 19.50, "deducao": 9900},
        {"inicio": 720000.01, "fim": 1800000, "aliquota": 20.50, "deducao": 17100},
        {"inicio": 1800000.01, "fim": 3600000, "aliquota": 23.00, "deducao": 62100},
        {"inicio": 3600000.01, "fim": 4800000, "aliquota": 30.50, "deducao": 540000}
    ]
}

def calcular_fator_r(folha_pagamento: float, receita_bruta: float) -> float:
    """
    Calcula o Fator R conforme Resolução CGSN nº 140/2018
    
    Args:
        folha_pagamento: Total da folha de pagamento dos últimos 12 meses
        receita_bruta: Total da receita bruta dos últimos 12 meses
    
    Returns:
        float: Valor do Fator R (entre 0 e 1)
    """
    if receita_bruta == 0 and folha_pagamento > 0:
        return 0.28  # 28%
    elif receita_bruta > 0 and folha_pagamento == 0:
        return 0.01  # 1%
    elif receita_bruta == 0:
        return 0.0
    else:
        return folha_pagamento / receita_bruta

def enquadrar_anexo(tipo_atividade: str, tipo_servico: str, fator_r: float = None) -> str:
    """
    Determina qual anexo aplicar baseado no tipo de atividade e Fator R
    
    Args:
        tipo_atividade: 'Comércio', 'Indústria' ou 'Serviços'
        tipo_servico: 'Serviço com fator R', 'Serviço especializado' ou 'Outro serviço'
        fator_r: Valor do Fator R (apenas para serviços com fator R)
    
    Returns:
        str: 'I', 'II', 'III', 'IV' ou 'V'
    """
    if tipo_atividade == "Comércio":
        return "I"
    elif tipo_atividade == "Indústria":
        return "II"
    elif tipo_atividade == "Serviços":
        if tipo_servico == "Serviço especializado":
            return "IV"
        elif tipo_servico == "Serviço com fator R":
            return "III" if fator_r and fator_r >= 0.28 else "V"
        else:  # Outro serviço
            return "V"
    else:
        return "V"  # Default

def buscar_faixa_e_calcular_aliquota(receita_bruta: float, anexo: str) -> Tuple[float, float, Dict]:
    """
    Busca a faixa e calcula a alíquota efetiva baseado na receita bruta
    
    Args:
        receita_bruta: Receita bruta acumulada dos últimos 12 meses
        anexo: 'I', 'II', 'III', 'IV' ou 'V'
    
    Returns:
        Tuple[float, float, Dict]: (aliquota_efetiva, parcela_deduzir, faixa_encontrada)
    """
    tabelas = {
        "I": ANEXO_I,
        "II": ANEXO_II,
        "III": ANEXO_III,
        "IV": ANEXO_IV,
        "V": ANEXO_V
    }
    
    tabela = tabelas.get(anexo, ANEXO_V)
    
    for faixa in tabela["faixas"]:
        if faixa["inicio"] <= receita_bruta <= faixa["fim"]:
            aliquota_nominal = faixa["aliquota"]
            parcela_deduzir = faixa["deducao"]
            aliquota_efetiva = calcular_aliquota_efetiva(receita_bruta, aliquota_nominal, parcela_deduzir)
            return aliquota_efetiva, parcela_deduzir, faixa
    
    # Se não encontrar, retorna a última faixa
    ultima_faixa = tabela["faixas"][-1]
    aliquota_nominal = ultima_faixa["aliquota"]
    parcela_deduzir = ultima_faixa["deducao"]
    aliquota_efetiva = calcular_aliquota_efetiva(receita_bruta, aliquota_nominal, parcela_deduzir)
    return aliquota_efetiva, parcela_deduzir, ultima_faixa

def calcular_aliquota_efetiva(receita_bruta: float, aliquota_nominal: float, parcela_deduzir: float) -> float:
    """
    Calcula a alíquota efetiva
    
    Args:
        receita_bruta: Receita bruta acumulada dos últimos 12 meses
        aliquota_nominal: Alíquota nominal da faixa
        parcela_deduzir: Parcela a deduzir da faixa
    
    Returns:
        float: Alíquota efetiva em percentual
    """
    if receita_bruta == 0:
        return 0.0
    
    aliquota_efetiva = ((receita_bruta * aliquota_nominal / 100) - parcela_deduzir) / receita_bruta * 100
    return max(0, aliquota_efetiva)

def calcular_das(receita_mes: float, aliquota_efetiva: float) -> float:
    """
    Calcula o valor do DAS
    
    Args:
        receita_mes: Receita do mês atual
        aliquota_efetiva: Alíquota efetiva em percentual
    
    Returns:
        float: Valor do DAS
    """
    return receita_mes * aliquota_efetiva / 100

def calcular_comparativo(receita_bruta: float, receita_mes: float, anexo_atual: str) -> Dict:
    """
    Calcula o comparativo com outros anexos
    
    Args:
        receita_bruta: Receita bruta acumulada
        receita_mes: Receita do mês atual
        anexo_atual: Anexo atual
    
    Returns:
        Dict: Dados do comparativo
    """
    comparativos = {}
    
    # Lista de anexos para comparar
    anexos_para_comparar = ["I", "II", "III", "IV", "V"]
    
    for anexo in anexos_para_comparar:
        if anexo != anexo_atual:
            aliquota_efetiva_alt, _, _ = buscar_faixa_e_calcular_aliquota(receita_bruta, anexo)
            das_alternativo = calcular_das(receita_mes, aliquota_efetiva_alt)
            
            comparativos[anexo] = {
                "aliquota_efetiva": aliquota_efetiva_alt,
                "das": das_alternativo
            }
    
    return comparativos

def criar_grafico_pizza(aliquota_efetiva: float, receita_mes: float) -> go.Figure:
    """
    Cria gráfico de pizza mostrando a distribuição da alíquota
    
    Args:
        aliquota_efetiva: Alíquota efetiva em percentual
        receita_mes: Receita do mês atual
    
    Returns:
        go.Figure: Gráfico de pizza
    """
    valor_tributo = receita_mes * aliquota_efetiva / 100
    valor_liquido = receita_mes - valor_tributo
    
    fig = go.Figure(data=[go.Pie(
        labels=['Tributos (DAS)', 'Receita Líquida'],
        values=[valor_tributo, valor_liquido],
        hole=0.4,
        marker_colors=['#FF6B6B', '#4ECDC4'],
        textinfo='label+percent',
        textposition='inside'
    )])
    
    fig.update_layout(
        title="Distribuição da Receita",
        showlegend=True,
        height=400
    )
    
    return fig

def criar_grafico_barras_comparativo(anexo_atual: str, comparativos: Dict) -> go.Figure:
    """
    Cria gráfico de barras comparando alíquotas efetivas
    
    Args:
        anexo_atual: Anexo atual
        comparativos: Dados dos comparativos
    
    Returns:
        go.Figure: Gráfico de barras
    """
    anexos = list(comparativos.keys()) + [anexo_atual]
    aliquota_atual, _, _ = buscar_faixa_e_calcular_aliquota(1000000, anexo_atual)  # Exemplo
    
    aliquotas = []
    for anexo in anexos:
        if anexo == anexo_atual:
            aliquotas.append(aliquota_atual)
        else:
            aliquotas.append(comparativos[anexo]["aliquota_efetiva"])
    
    fig = go.Figure(data=[
        go.Bar(
            x=[f"Anexo {anexo}" for anexo in anexos],
            y=aliquotas,
            marker_color=['#FF6B6B' if anexo == anexo_atual else '#4ECDC4' for anexo in anexos],
            text=[f"{aliquota:.2f}%" for aliquota in aliquotas],
            textposition='auto'
        )
    ])
    
    fig.update_layout(
        title="Comparativo de Alíquotas Efetivas por Anexo",
        xaxis_title="Anexos",
        yaxis_title="Alíquota Efetiva (%)",
        height=400
    )
    
    return fig

def main():
    """Função principal da aplicação"""
    
    # Título principal
    st.title("🏢 Apurador Simples Nacional Completo – PAC")
    st.markdown("---")
    
    # Sidebar com informações
    with st.sidebar:
        st.header("ℹ️ Informações")
        st.info("""
        **Regras de Enquadramento:**
        - **Comércio** → Anexo I
        - **Indústria** → Anexo II
        - **Serviços com fator R** → Anexo III (≥28%) ou V (<28%)
        - **Serviços especializados** → Anexo IV
        - **Outros serviços** → Anexo V
        
        **Base Legal:** Simples Nacional 2025
        """)
    
    # Layout em colunas
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📋 Dados da Empresa")
        
        # Entradas do usuário
        nome_empresa = st.text_input("Nome da Empresa", placeholder="Digite o nome da empresa")
        
        tipo_atividade = st.selectbox(
            "Tipo de Atividade",
            ["Comércio", "Indústria", "Serviços"],
            help="Selecione o tipo de atividade principal"
        )
        
        # Campo específico para serviços
        tipo_servico = None
        if tipo_atividade == "Serviços":
            tipo_servico = st.selectbox(
                "Tipo de Serviço",
                ["Serviço com fator R (Anexo III/V)", "Serviço especializado (Anexo IV)", "Outro serviço (Anexo V)"],
                help="Selecione o tipo específico de serviço"
            )
        
        st.subheader("💰 Dados Financeiros")
        
        receita_bruta = st.number_input(
            "Receita Bruta Acumulada (últimos 12 meses)",
            min_value=0.0,
            value=0.0,
            step=1000.0,
            format="%.2f",
            help="Total da receita bruta dos últimos 12 meses"
        )
        
        folha_pagamento = st.number_input(
            "Folha de Pagamento (últimos 12 meses)",
            min_value=0.0,
            value=0.0,
            step=1000.0,
            format="%.2f",
            help="Total da folha de pagamento dos últimos 12 meses (apenas para serviços)"
        )
        
        receita_mes = st.number_input(
            "Receita do Mês Atual",
            min_value=0.0,
            value=0.0,
            step=1000.0,
            format="%.2f",
            help="Receita bruta do mês atual"
        )
    
    with col2:
        st.subheader("📊 Resultados")
        
        if st.button("🔄 Calcular Simples Nacional", type="primary"):
            if receita_bruta == 0 and folha_pagamento == 0:
                st.error("⚠️ Por favor, informe pelo menos a receita bruta ou folha de pagamento.")
            else:
                # Cálculos
                fator_r = None
                if tipo_atividade == "Serviços" and "fator R" in tipo_servico:
                    fator_r = calcular_fator_r(folha_pagamento, receita_bruta)
                
                anexo = enquadrar_anexo(tipo_atividade, tipo_servico, fator_r)
                aliquota_efetiva, parcela_deduzir, faixa_encontrada = buscar_faixa_e_calcular_aliquota(receita_bruta, anexo)
                das = calcular_das(receita_mes, aliquota_efetiva)
                
                # Comparativo
                comparativos = calcular_comparativo(receita_bruta, receita_mes, anexo)
                
                # Exibição dos resultados
                if nome_empresa:
                    st.success(f"🏢 **{nome_empresa}**")
                
                # Métricas principais
                col_metric1, col_metric2 = st.columns(2)
                
                with col_metric1:
                    if fator_r is not None:
                        st.metric(
                            "Fator R",
                            f"{fator_r:.2%}",
                            help="Folha de pagamento / Receita bruta"
                        )
                    
                    st.metric(
                        "Anexo Aplicado",
                        f"Anexo {anexo}",
                        help="I=Comércio, II=Indústria, III/V=Serviços"
                    )
                
                with col_metric2:
                    st.metric(
                        "Alíquota Efetiva",
                        f"{aliquota_efetiva:.2f}%",
                        help="Alíquota efetiva do Simples Nacional"
                    )
                    
                    st.metric(
                        "DAS",
                        f"R$ {das:,.2f}",
                        help="Valor do DAS a pagar"
                    )
                
                # Detalhes técnicos
                with st.expander("🔍 Detalhes Técnicos"):
                    st.write(f"**Faixa de Receita:** R$ {faixa_encontrada['inicio']:,.2f} a R$ {faixa_encontrada['fim']:,.2f}")
                    st.write(f"**Alíquota Nominal:** {faixa_encontrada['aliquota']:.2f}%")
                    st.write(f"**Parcela a Deduzir:** R$ {parcela_deduzir:,.2f}")
                    st.write(f"**Receita Bruta:** R$ {receita_bruta:,.2f}")
                    st.write(f"**Receita do Mês:** R$ {receita_mes:,.2f}")
                
                # Comparativo
                st.subheader("📈 Comparativo com Outros Anexos")
                
                # Criar DataFrame para exibição
                dados_comparativo = []
                for anexo_comp, dados in comparativos.items():
                    dados_comparativo.append({
                        "Anexo": f"Anexo {anexo_comp}",
                        "Alíquota Efetiva": f"{dados['aliquota_efetiva']:.2f}%",
                        "DAS": f"R$ {dados['das']:,.2f}",
                        "Diferença": f"R$ {dados['das'] - das:,.2f}"
                    })
                
                df_comparativo = pd.DataFrame(dados_comparativo)
                st.dataframe(df_comparativo, use_container_width=True)
                
                # Gráficos
                if receita_mes > 0:
                    col_graf1, col_graf2 = st.columns(2)
                    
                    with col_graf1:
                        st.subheader("📊 Distribuição da Receita")
                        fig_pizza = criar_grafico_pizza(aliquota_efetiva, receita_mes)
                        st.plotly_chart(fig_pizza, use_container_width=True)
                    
                    with col_graf2:
                        st.subheader("📊 Comparativo de Alíquotas")
                        fig_barras = criar_grafico_barras_comparativo(anexo, comparativos)
                        st.plotly_chart(fig_barras, use_container_width=True)
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666; font-size: 0.8em;'>
        📊 Sistema desenvolvido para fins educacionais e de simulação<br>
        ⚖️ Baseado no Simples Nacional 2025 - Todos os 5 Anexos
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main() 