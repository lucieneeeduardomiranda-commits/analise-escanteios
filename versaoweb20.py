# -*- coding: utf-8 -*-
"""
Analisador de Apostas em Escanteios - Interface Web (Streamlit)
Modelo de Poisson com Média Ponderada (Força de Ataque/Defesa)
Tempo Total de Jogo: 95 minutos (com acréscimos)
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

# --- Funções de Cálculo ---

def poisson_prob(k, lamb):
    """Calcula a probabilidade de Poisson P(X=k) dado o lambda (média)."""
    if k < 0:
        return 0.0
    try:
        return (lamb**k * math.exp(-lamb)) / math.factorial(k)
    except (OverflowError, ValueError):
        return 0.0

def calcular_ev_e_prob(minutos_jogados, escanteios_atuais, linha_over, odd_over, odd_under, media_escanteios_por_jogo):
    """
    Calcula as probabilidades e o Valor Esperado (EV) para a aposta em escanteios.
    """
    
    # Constantes
    TEMPO_TOTAL_REGULAMENTAR = 95  # 95 MINUTOS (CONSIDERANDO ACRÉSCIMOS)
    
    MEDIA_ESCANTEIOS_POR_JOGO = media_escanteios_por_jogo
    TAXA_ESCANTEIOS_POR_MINUTO = MEDIA_ESCANTEIOS_POR_JOGO / TEMPO_TOTAL_REGULAMENTAR

    # 1. Cálculo da Projeção
    minutos_restantes = TEMPO_TOTAL_REGULAMENTAR - minutos_jogados
    
    if minutos_restantes <= 0:
        minutos_restantes = 0
        escanteios_projetados_restantes = 0.0
    else:
        escanteios_projetados_restantes = TAXA_ESCANTEIOS_POR_MINUTO * minutos_restantes

    # 2. Determinação do Tipo de Linha
    is_half_line = (linha_over * 10) % 10 != 0
    
    # 3. Cálculo das Probabilidades
    
    # Número de escanteios que faltam para o Over
    target_over = math.floor(linha_over) + 1 - escanteios_atuais
    
    if is_half_line:
        # Linha de Meio Ponto (ex: 8.5) - Não há push
        # Over ganha se X >= target_over
        
        if target_over <= 0:
            prob_over = 1.0
            prob_under = 0.0
        elif minutos_restantes == 0:
            prob_over = 0.0
            prob_under = 1.0
        else:
            prob_under_target = 0.0
            for k in range(target_over):
                prob_under_target += poisson_prob(k, escanteios_projetados_restantes)

            prob_under = prob_under_target
            prob_over = 1.0 - prob_under_target
            
        prob_push = 0.0
        
    else:
        # Linha Asiática (Inteira, ex: 8.0) - Possibilidade de Push
        # target_push é o número de escanteios restantes para o push
        target_push = target_over 
        
        if minutos_restantes == 0:
            prob_over = 0.0
            prob_push = 0.0
            prob_under = 1.0
        else:
            # P(Push) = P(X = target_push)
            prob_push = poisson_prob(target_push, escanteios_projetados_restantes)
            
            # P(Under) = P(X < target_push) = P(X <= target_push - 1)
            prob_under_target = 0.0
            for k in range(target_push):
                prob_under_target += poisson_prob(k, escanteios_projetados_restantes)
            prob_under = prob_under_target
            
            # P(Over) = 1 - P(Push) - P(Under)
            prob_over = 1.0 - prob_push - prob_under
            
            # Ajuste para casos onde o total atual já é maior ou igual à linha
            if escanteios_atuais > linha_over:
                prob_over = 1.0
                prob_push = 0.0
                prob_under = 0.0
            elif escanteios_atuais == linha_over:
                prob_over = 0.0
                prob_push = 1.0
                prob_under = 0.0

    # 4. Cálculo do Valor Esperado (Expected Value - EV)
    
    # EV = (Prob Ganhar * Lucro) - (Prob Perder * Perda)
    ev_over = (prob_over * (odd_over - 1)) - (prob_under * 1)
    ev_under = (prob_under * (odd_under - 1)) - (prob_over * 1)

    # 5. Retornar os resultados
    return {
        "minutos_restantes": minutos_restantes,
        "escanteios_projetados_restantes": escanteios_projetados_restantes,
        "taxa_escanteios_por_minuto": TAXA_ESCANTEIOS_POR_MINUTO,
        "is_half_line": is_half_line,
        "prob_over": prob_over,
        "prob_push": prob_push,
        "prob_under": prob_under,
        "ev_over": ev_over,
        "ev_under": ev_under,
        "media_escanteios": MEDIA_ESCANTEIOS_POR_JOGO,
    }

# --- Interface Principal ---

st.title("⚽ Analisador de Apostas em Escanteios")
st.markdown("**Modelo de Poisson com Média Ponderada (Força de Ataque/Defesa)**")
st.markdown("**Tempo Total de Jogo: 95 minutos (com acréscimos)**")
st.markdown("---")

# --- Barra Lateral ---
with st.sidebar:
    st.header("📊 Configurações")
    
    st.subheader("Dados da Partida")
    minutos_jogados = st.slider(
        "Minutos Jogados",
        min_value=0,
        max_value=95,
        value=45,
        step=1,
        help="Quantos minutos já foram jogados"
    )
    
    escanteios_atuais = st.number_input(
        "Escanteios Atuais",
        min_value=0,
        max_value=30,
        value=5,
        step=1,
        help="Número de escanteios já cobrados na partida"
    )
    
    st.markdown("---")
    st.subheader("Dados da Aposta")
    
    linha_over = st.number_input(
        "Linha de Aposta",
        min_value=0.5,
        max_value=20.0,
        value=10.5,
        step=0.5,
        help="Linha Over/Under (ex: 10.5 ou 8.0)"
    )
    
    col_odd1, col_odd2 = st.columns(2)
    with col_odd1:
        odd_over = st.number_input(
            "Odd Over",
            min_value=1.01,
            max_value=10.0,
            value=1.90,
            step=0.01,
            help="Cotação para o Over"
        )
    
    with col_odd2:
        odd_under = st.number_input(
            "Odd Under",
            min_value=1.01,
            max_value=10.0,
            value=1.90,
            step=0.01,
            help="Cotação para o Under"
        )

# --- Área Principal ---

st.subheader("📋 Dados dos Times (Média Ponderada)")

col1, col2, col3, col4 = st.columns(4)

with col1:
    media_casa_favor = st.number_input(
        "Time Casa - A Favor",
        min_value=0.0,
        max_value=15.0,
        value=5.89,
        step=0.1,
        help="Média de escanteios cobrados pelo Time da Casa"
    )

with col2:
    media_casa_contra = st.number_input(
        "Time Casa - Contra",
        min_value=0.0,
        max_value=15.0,
        value=2.95,
        step=0.1,
        help="Média de escanteios cedidos pelo Time da Casa"
    )

with col3:
    media_visitante_favor = st.number_input(
        "Time Visitante - A Favor",
        min_value=0.0,
        max_value=15.0,
        value=4.00,
        step=0.1,
        help="Média de escanteios cobrados pelo Time Visitante"
    )

with col4:
    media_visitante_contra = st.number_input(
        "Time Visitante - Contra",
        min_value=0.0,
        max_value=15.0,
        value=4.68,
        step=0.1,
        help="Média de escanteios cedidos pelo Time Visitante"
    )

# --- Cálculo da Média Ponderada ---

media_a_favor = media_casa_favor + media_visitante_favor
media_sofridos = media_casa_contra + media_visitante_contra
media_ponderada_jogo = (media_a_favor + media_sofridos) / 2

st.markdown("---")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Média A Favor", f"{media_a_favor:.2f}")

with col2:
    st.metric("Média Sofridos", f"{media_sofridos:.2f}")

with col3:
    st.metric("Média Ponderada", f"{media_ponderada_jogo:.2f}")

st.markdown("---")

# --- Botão de Cálculo ---

if st.button("🔍 Calcular Análise", use_container_width=True, type="primary"):
    
    # Validação
    if minutos_jogados < 0 or minutos_jogados > 95:
        st.error("❌ Os minutos jogados devem estar entre 0 e 95.")
    elif escanteios_atuais < 0:
        st.error("❌ Os escanteios atuais não podem ser negativos.")
    elif linha_over <= 0:
        st.error("❌ A linha de aposta deve ser maior que zero.")
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
            media_ponderada_jogo
        )
        
        st.markdown("---")
        st.subheader("📊 Resultados da Análise")
        
        # Métricas principais
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Minutos Restantes",
                f"{resultados['minutos_restantes']}",
                "min"
            )
        
        with col2:
            st.metric(
                "Taxa/Minuto",
                f"{resultados['taxa_escanteios_por_minuto']:.4f}",
                "esc/min"
            )
        
        with col3:
            st.metric(
                "Escanteios Projetados",
                f"{resultados['escanteios_projetados_restantes']:.2f}",
                "restantes"
            )
        
        with col4:
            tipo_linha = "Meio Ponto" if resultados['is_half_line'] else "Asiática"
            st.metric(
                "Tipo de Linha",
                tipo_linha
            )
        
        st.markdown("---")
        
        # Probabilidades
        st.subheader("📈 Probabilidades")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                f"Probabilidade Over {linha_over}",
                f"{resultados['prob_over']*100:.2f}%"
            )
        
        with col2:
            if not resultados['is_half_line']:
                st.metric(
                    f"Probabilidade Push",
                    f"{resultados['prob_push']*100:.2f}%"
                )
            else:
                st.metric(
                    "Push",
                    "N/A",
                    "(Meio Ponto)"
                )
        
        with col3:
            st.metric(
                f"Probabilidade Under {linha_over}",
                f"{resultados['prob_under']*100:.2f}%"
            )
        
        st.markdown("---")
        
        # Valor Esperado
        st.subheader("💰 Valor Esperado (EV)")
        
        col1, col2 = st.columns(2)
        
        with col1:
            ev_over_pct = resultados['ev_over'] * 100
            st.metric(
                f"EV Over {linha_over}",
                f"{resultados['ev_over']:.4f}",
                f"{ev_over_pct:+.2f}%"
            )
        
        with col2:
            ev_under_pct = resultados['ev_under'] * 100
            st.metric(
                f"EV Under {linha_over}",
                f"{resultados['ev_under']:.4f}",
                f"{ev_under_pct:+.2f}%"
            )
        
        st.markdown("---")
        
        # Recomendação
        st.subheader("🎯 Recomendação")
        
        if resultados['ev_over'] > 0.05 and resultados['ev_over'] > resultados['ev_under']:
            st.success(f"""
            ✓ **APOSTE NO OVER {linha_over}**
            
            **EV Positivo:** {resultados['ev_over']:+.4f} ({resultados['ev_over']*100:+.2f}%)
            
            A aposta no Over tem valor esperado positivo a longo prazo.
            """)
        elif resultados['ev_under'] > 0.05 and resultados['ev_under'] > resultados['ev_over']:
            st.success(f"""
            ✓ **APOSTE NO UNDER {linha_over}**
            
            **EV Positivo:** {resultados['ev_under']:+.4f} ({resultados['ev_under']*100:+.2f}%)
            
            A aposta no Under tem valor esperado positivo a longo prazo.
            """)
        else:
            st.warning(f"""
            ⚠️ **EVITAR A APOSTA**
            
            **Melhor EV disponível:** {max(resultados['ev_over'], resultados['ev_under']):+.4f}
            
            Nenhuma das opções oferece um EV suficientemente positivo para uma aposta lucrativa.
            """)
        
        st.markdown("---")
        
        # Detalhes Técnicos
        with st.expander("📋 Detalhes Técnicos"):
            st.markdown(f"""
            **Configurações de Cálculo:**
            - Tempo Total de Jogo: 95 minutos
            - Média de Escanteios (Ponderada): {resultados['media_escanteios']:.3f}
            - Taxa de Escanteios: {resultados['taxa_escanteios_por_minuto']:.4f} escanteios/minuto
            
            **Dados da Partida:**
            - Minutos Jogados: {minutos_jogados}
            - Escanteios Atuais: {escanteios_atuais}
            - Linha de Aposta: {linha_over} ({'Meio Ponto' if resultados['is_half_line'] else 'Asiática'})
            - Odds: Over {odd_over} / Under {odd_under}
            
            **Projeções:**
            - Minutos Restantes: {resultados['minutos_restantes']}
            - Escanteios Projetados (Restantes): {resultados['escanteios_projetados_restantes']:.2f}
            
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
<p><strong>Analisador de Apostas em Escanteios</strong> | Modelo de Poisson com Média Ponderada</p>
<p>⚠️ <strong>Aviso:</strong> Este é um simulador educacional. Apostas envolvem risco financeiro. Jogue com responsabilidade.</p>
</div>
""", unsafe_allow_html=True)
