# -*- coding: utf-8 -*-
"""
Analisador de Escanteios - Interface Web (Streamlit)
Calcula valor esperado (EV) para apostas Over/Under em escanteios
Considera tempo total de 95 minutos (incluindo acréscimos)
"""
import streamlit as st
import math

# --- Configuração da Página ---
st.set_page_config(
    page_title="Analisador de Escanteios",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Estilos CSS ---
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stMetric {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
    }
    .recommendation-positive {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        padding: 1rem;
        border-radius: 0.5rem;
        color: #155724;
    }
    .recommendation-negative {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        padding: 1rem;
        border-radius: 0.5rem;
        color: #721c24;
    }
    .recommendation-neutral {
        background-color: #fff3cd;
        border: 1px solid #ffeeba;
        padding: 1rem;
        border-radius: 0.5rem;
        color: #856404;
    }
    </style>
""", unsafe_allow_html=True)

# --- Funções de Cálculo ---

def poisson_prob(k, lamb):
    """
    Calcula a probabilidade de Poisson para k ocorrências com uma média lamb.
    """
    if k < 0 or lamb < 0: 
        return 0.0
    try:
        return (lamb**k * math.exp(-lamb)) / math.factorial(k)
    except (OverflowError, ValueError):
        return 0.0

def calcular_ev_e_prob(minutos_jogados, escanteios_atuais, linha_over, odd_over, odd_under, media_campeonato):
    """
    Calcula as probabilidades e o valor esperado para apostas de escanteios.
    """
    TEMPO_TOTAL_COM_ACRESCIMOS = 95  # Tempo regulamentar + acréscimos médios
    
    if media_campeonato <= 0:
        return None

    taxa_escanteios_por_minuto = media_campeonato / TEMPO_TOTAL_COM_ACRESCIMOS
    minutos_restantes = max(0, TEMPO_TOTAL_COM_ACRESCIMOS - minutos_jogados)
    escanteios_projetados_restantes = taxa_escanteios_por_minuto * minutos_restantes
    escanteios_totais_projetados = escanteios_atuais + escanteios_projetados_restantes
    escanteios_necessarios_para_over = math.floor(linha_over) + 1 - escanteios_atuais

    if escanteios_necessarios_para_over <= 0:
        prob_over, prob_under = 1.0, 0.0
    elif minutos_restantes == 0:
        prob_over, prob_under = 0.0, 1.0
    else:
        prob_under = sum(poisson_prob(k, escanteios_projetados_restantes) 
                        for k in range(int(escanteios_necessarios_para_over)))
        prob_over = 1.0 - prob_under

    ev_over = (prob_over * (odd_over - 1)) - prob_under
    ev_under = (prob_under * (odd_under - 1)) - prob_over

    return {
        "tempo_total": TEMPO_TOTAL_COM_ACRESCIMOS,
        "minutos_restantes": minutos_restantes,
        "taxa_por_minuto": taxa_escanteios_por_minuto,
        "projecao_restante": escanteios_projetados_restantes,
        "projecao_final": escanteios_totais_projetados,
        "escanteios_necessarios": escanteios_necessarios_para_over,
        "prob_over": prob_over,
        "prob_under": prob_under,
        "ev_over": ev_over,
        "ev_under": ev_under,
    }

# --- Interface Principal ---

st.title("⚽ Analisador de Escanteios")
st.markdown("**Calcule o Valor Esperado (EV) para suas apostas em escanteios**")
st.markdown("---")

# --- Barra Lateral ---
with st.sidebar:
    st.header("📊 Configurações")
    
    st.subheader("Campeonato")
    media_campeonato = st.number_input(
        "Média de Escanteios do Campeonato",
        min_value=5.0,
        max_value=15.0,
        value=10.0,
        step=0.1,
        help="Média de escanteios por jogo do campeonato"
    )
    
    st.markdown("---")
    st.subheader("Referências de Ligas")
    st.markdown("""
    - **Premier League:** ~11.8
    - **Bundesliga:** ~11.2
    - **La Liga:** ~10.5
    - **Serie A:** ~10.0
    - **Brasileirão:** ~9.8
    - **Ligue 1:** ~9.2
    """)

# --- Área Principal ---

col1, col2 = st.columns(2)

with col1:
    st.subheader("📋 Dados da Partida")
    
    minutos_jogados = st.slider(
        "Minutos Jogados",
        min_value=0,
        max_value=95,
        value=45,
        step=1,
        help="Quantos minutos já foram jogados"
    )
    
    escanteios_atuais = st.number_input(
        "Escanteios Já Cobrados",
        min_value=0,
        max_value=30,
        value=5,
        step=1,
        help="Número de escanteios já cobrados na partida"
    )

with col2:
    st.subheader("💰 Aposta")
    
    linha_over = st.number_input(
        "Linha da Aposta",
        min_value=0.5,
        max_value=20.0,
        value=10.5,
        step=0.5,
        help="Linha Over/Under (ex: 10.5)"
    )
    
    col_odd1, col_odd2 = st.columns(2)
    with col_odd1:
        odd_over = st.number_input(
            "Odd do Over",
            min_value=1.01,
            max_value=10.0,
            value=1.90,
            step=0.01,
            help="Cotação para o Over"
        )
    
    with col_odd2:
        odd_under = st.number_input(
            "Odd do Under",
            min_value=1.01,
            max_value=10.0,
            value=1.90,
            step=0.01,
            help="Cotação para o Under"
        )

# --- Botão de Cálculo ---
st.markdown("---")

if st.button("🔍 Calcular Análise", use_container_width=True, type="primary"):
    
    # Validação
    if media_campeonato <= 0:
        st.error("❌ A média do campeonato deve ser maior que zero.")
    elif odd_over <= 1.0 or odd_under <= 1.0:
        st.error("❌ As odds devem ser maiores que 1.00.")
    else:
        # Cálculo
        resultados = calcular_ev_e_prob(
            minutos_jogados,
            escanteios_atuais,
            linha_over,
            odd_over,
            odd_under,
            media_campeonato
        )
        
        if resultados:
            st.markdown("---")
            st.subheader("📊 Resultados da Análise")
            
            # Métricas principais
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Projeção Final",
                f"{resultados['projecao_final']:.2f}", "escanteios"
                )
            
            with col2:
                st.metric(
                    "Minutos Restantes",
                    f"{resultados['minutos_restantes']}", "min"
                )
            
            with col3:
                st.metric(
                    "Taxa/Minuto",
                    f"{resultados['taxa_por_minuto']:.4f}", "esc/min"
                )
            
            with col4:
                st.metric(
                    "Necessários para Over",
             f"{resultados['escanteios_necessarios']}", "escanteios"
                )
            
            st.markdown("---")
            
            # Probabilidades
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric(
                   f"Probabilidade Over {linha_over}", f"{resultados['prob_over']*100:.2f}%"
                )
            
            with col2:
                st.metric(
               f"Probabilidade Under {linha_over}", f"{resultados['prob_under']*100:.2f}%"
                )
            
            st.markdown("---")
            
            # Valor Esperado
            col1, col2 = st.columns(2)
            
            with col1:
                ev_over_pct = resultados['ev_over'] * 100
                st.metric(
               f"EV Over {linha_over}", f"{resultados['ev_over']:.4f}", f"{ev_over_pct:+.2f}%"
                )
            
            with col2:
                ev_under_pct = resultados['ev_under'] * 100
                st.metric(
                f"EV Under {linha_over}", f"{resultados['ev_under']:.4f}", f"{ev_under_pct:+.2f}%"
                )
            
            st.markdown("---")
            
            # Recomendação
            st.subheader("🎯 Recomendação")
            
            if resultados['ev_over'] > 0.05:
                st.markdown(
                    f"""
                    <div class="recommendation-positive">
                    <h3>✓ APOSTE NO OVER {linha_over}</h3>
                    <p><strong>EV Positivo:</strong> {resultados['ev_over']:+.4f} ({resultados['ev_over']*100:+.2f}%)</p>
                    <p>A aposta no Over tem valor esperado positivo a longo prazo.</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            elif resultados['ev_under'] > 0.05:
                st.markdown(
                    f"""
                    <div class="recommendation-positive">
                    <h3>✓ APOSTE NO UNDER {linha_over}</h3>
                    <p><strong>EV Positivo:</strong> {resultados['ev_under']:+.4f} ({resultados['ev_under']*100:+.2f}%)</p>
                    <p>A aposta no Under tem valor esperado positivo a longo prazo.</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f"""
                    <div class="recommendation-neutral">
                    <h3>⚠ NÃO APOSTAR (EV INSUFICIENTE)</h3>
                    <p><strong>Melhor EV disponível:</strong> {max(resultados['ev_over'], resultados['ev_under']):+.4f}</p>
                    <p>Nenhuma das opções oferece um EV suficientemente positivo para uma aposta lucrativa.</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            
            st.markdown("---")
            
            # Detalhes Técnicos (em um expander)
            with st.expander("📈 Detalhes Técnicos"):
                st.markdown(f"""
                **Configurações de Cálculo:**
                - Tempo Total de Jogo: {resultados['tempo_total']} minutos
                - Taxa de Escanteios: {resultados['taxa_por_minuto']:.4f} escanteios/minuto
                - Escanteios Atuais: {escanteios_atuais}
                - Escanteios Projetados (Restantes): {resultados['projecao_restante']:.2f}
                - Escanteios Projetados (Total Final): {resultados['projecao_final']:.2f}
                
                **Modelo Estatístico:**
                - Distribuição: Poisson
                - Critério de Recomendação: EV > 0.05 (5%)
                """)

else:
    st.info("👆 Clique no botão acima para calcular a análise")

# --- Rodapé ---
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #888; font-size: 0.9rem;">
<p><strong>Analisador de Escanteios v5.0</strong> | Desenvolvido com Streamlit</p>
<p>⚠️ <strong>Aviso:</strong> Este é um simulador educacional. Apostas envolvem risco financeiro. Jogue com responsabilidade.</p>
</div>
""", unsafe_allow_html=True)
