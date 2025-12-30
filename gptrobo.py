# -*- coding: utf-8 -*-
import streamlit as st
import math
from scipy.stats import nbinom

# ======================================================
# CONFIGURAÇÃO
# ======================================================
st.set_page_config(
    page_title="Scanner Pro v9.0 - Live Realista",
    page_icon="⚽",
    layout="wide"
)

st.markdown("""
<style>
[data-testid="stMetricValue"] { font-size: 26px; font-weight: bold; color: #00ffcc; }
.stButton>button { width: 100%; height: 3em; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ======================================================
# FUNÇÕES AUXILIARES
# ======================================================

def fator_ritmo_manual(ritmo):
    return {
        "🔴 Muito lento": 0.65,
        "🟡 Normal": 1.00,
        "🟢 Alto": 1.20,
        "🔥 Muito alto": 1.40
    }[ritmo]

def fator_fluidez_fixo():
    # Fixado em Neutro conforme solicitado
    return 1.00

def peso_lambda_observado(minuto):
    if minuto < 30:
        return 0.35
    elif minuto < 55:
        return 0.55
    elif minuto < 70:
        return 0.70
    else:
        return 0.85

def neg_binomial_prob(k, mu, k_disp=3.0):
    if k < 0 or mu <= 0:
        return 0.0
    p = k_disp / (k_disp + mu)
    return float(nbinom.pmf(k, k_disp, p))

def calcular_probabilidades(lambda_r, atuais, linha):
    alvo = math.floor(linha) + 1 - atuais
    is_half = (linha * 10) % 10 != 0

    if alvo <= 0:
        return 1.0, 0.0, 0.0

    if is_half:
        p_under = sum(neg_binomial_prob(k, lambda_r) for k in range(alvo))
        p_over = 1 - p_under
        p_push = 0.0
    else:
        p_push = neg_binomial_prob(alvo, lambda_r)
        p_under = sum(neg_binomial_prob(k, lambda_r) for k in range(alvo))
        p_over = 1 - p_under - p_push

    return p_over, p_under, p_push

def calcular_ev(p_win, p_lose, odd):
    return (p_win * (odd - 1)) - p_lose

def calcular_kelly(p_win, p_lose, odd, fator=0.5):
    if odd <= 1:
        return 0.0
    b = odd - 1
    f = (p_win * b - p_lose) / b
    return max(0, f * fator)

# ======================================================
# SIDEBAR — INPUTS RÁPIDOS (LIVE)
# ======================================================

with st.sidebar:
    st.header("🎮 Dados da Live")

    minuto = st.slider("⏱️ Minuto", 0, 95, 60)
    escanteios = st.number_input("🚩 Escanteios atuais", 0, 30, 4)

    st.divider()

    linha = st.number_input("🎯 Linha (Over)", 0.5, 20.0, 8.5, 0.5)
    odd_o = st.number_input("Odd Over", 1.01, 10.0, 1.90)
    odd_u = st.number_input("Odd Under", 1.01, 10.0, 1.90)

    st.divider()

    ritmo = st.selectbox(
        "📈 Ritmo do jogo",
        ["🔴 Muito lento", "🟡 Normal", "🟢 Alto", "🔥 Muito alto"]
    )

    # Fluidez removida do seletor e fixada internamente

    st.divider()

    banca = st.number_input("💰 Banca (R$)", 0.0, 100000.0, 1000.0)
    kelly_factor = st.slider("Kelly (%)", 0.1, 1.0, 0.5)

# ======================================================
# CORPO PRINCIPAL
# ======================================================

st.title("⚽ Scanner Pro v9.0 — Leitura ao Vivo Realista")

media_liga = 10.0
tempo_total = 95
min_restantes = max(0, tempo_total - minuto)

# ---- LAMBDA TEÓRICO ----
lambda_teorico = (media_liga / tempo_total) * min_restantes

# ---- LAMBDA OBSERVADO ----
ritmo_obs = escanteios / minuto if minuto > 0 else 0
lambda_obs = ritmo_obs * min_restantes

# ---- AJUSTES MANUAIS ----
lambda_obs *= fator_ritmo_manual(ritmo)
lambda_obs *= fator_fluidez_fixo() # Agora usa o valor fixo de 1.00 (Neutro)

# ---- COMBINAÇÃO DINÂMICA ----
peso_obs = peso_lambda_observado(minuto)
lambda_final = (1 - peso_obs) * lambda_teorico + peso_obs * lambda_obs

# ======================================================
# VETOS AUTOMÁTICOS
# ======================================================
veto = False
motivos = []

if ritmo == "🔴 Muito lento" and linha >= 7.5:
    veto = True
    motivos.append("Ritmo muito lento para linha alta")

# Veto de fluidez truncada removido pois agora é sempre Neutro

if min_restantes < 15 and linha - escanteios >= 4:
    veto = True
    motivos.append("Pouco tempo útil restante")

# ======================================================
# PROBABILIDADES
# ======================================================
p_over, p_under, p_push = calcular_probabilidades(lambda_final, escanteios, linha)

p_lose_over = 1 - p_over - p_push
p_lose_under = 1 - p_under - p_push

ev_over = calcular_ev(p_over, p_lose_over, odd_o)
ev_under = calcular_ev(p_under, p_lose_under, odd_u)

# ======================================================
# RESULTADOS (FILTRO SOMENTE OVER)
# ======================================================
st.divider()

col1, col2, col3 = st.columns(3)
col1.metric("Prob. Over", f"{p_over:.1%}")
col2.metric("Prob. Under", f"{p_under:.1%}")
col3.metric("Push", f"{p_push:.1%}")

st.divider()

if veto:
    st.error("⛔ SEM ENTRADA")
    for m in motivos:
        st.write("•", m)
else:
    if ev_over > 0.05:
        f_k = calcular_kelly(p_over, p_lose_over, odd_o, kelly_factor)
        st.success(f"✅ ENTRAR OVER {linha}")
        st.write(f"Stake sugerida: R$
