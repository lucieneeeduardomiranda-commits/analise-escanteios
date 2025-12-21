# -*- coding: utf-8 -*-
import math

def poisson_prob(k, lamb):
    """Calcula a probabilidade de Poisson P(X=k) dado o lambda (média)."""
    if k < 0:
        return 0.0
    return (lamb**k * math.exp(-lamb)) / math.factorial(k)

def calcular_ev_e_prob(minutos_jogados, escanteios_atuais, linha_over, odd_over, odd_under, media_escanteios_por_jogo=10.0):
    """
    Calcula as probabilidades e o Valor Esperado (EV) para a aposta em escanteios.
    Suporta linhas de meio ponto (ex: 8.5) e linhas asiáticas (inteiras, ex: 8.0).
    A média de escanteios por jogo pode ser especificada.
    """
    
    # Constantes
    TEMPO_TOTAL_REGULAMENTAR = 95 # ALTERADO PARA 95 MINUTOS (CONSIDERANDO ACRÉSCIMOS)
    
    # Usa a média fornecida ou a padrão de 10.0
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
    
    # O cálculo do EV é o mesmo para ambos os tipos de linha, pois o push é um evento de lucro zero.
    # EV = (Prob Ganhar * Lucro) - (Prob Perder * Perda)
    ev_over = (prob_over * (odd_over - 1)) - (prob_under * 1)
    ev_under = (prob_under * (odd_under - 1)) - (prob_over * 1)

    # 5. Saída dos resultados (para debug e análise completa)
    print("\n--- Análise Estatística de Escanteios ---")
    print(f"Dados Iniciais: {escanteios_atuais} escanteios em {minutos_jogados} minutos.")
    print(f"Linha de Aposta: Over/Under {linha_over} ({'Meio Ponto' if is_half_line else 'Asiática'})")
    print(f"Odds: Over {odd_over} / Under {odd_under}")
    print(f"Média de Escanteios (95 min): {MEDIA_ESCANTEIOS_POR_JOGO:.2f}")
    print("-" * 40)
    print(f"Minutos Restantes: {minutos_restantes} minutos.")
    print(f"Escanteios Projetados para o Restante (Lambda): {escanteios_projetados_restantes:.2f}")
    print("-" * 40)
    print("Probabilidades Calculadas:")
    print(f"Probabilidade Over {linha_over}: {prob_over * 100:.2f}%")
    if not is_half_line:
        print(f"Probabilidade Push (Anulada): {prob_push * 100:.2f}%")
    print(f"Probabilidade Under {linha_over}: {prob_under * 100:.2f}%")
    print("-" * 40)
    print("Valor Esperado (EV):")
    print(f"EV Over {linha_over}: {ev_over:.4f}")
    print(f"EV Under {linha_over}: {ev_under:.4f}")
    print("-" * 40)
    
    # 6. Recomendação
    if ev_over > 0.05 and ev_over > ev_under:
        print(f"RECOMENDAÇÃO: APOSTE NO OVER {linha_over}")
    elif ev_under > 0.05 and ev_under > ev_over:
        print(f"RECOMENDAÇÃO: APOSTE NO UNDER {linha_over}")
    else:
        print("RECOMENDAÇÃO: EVITAR A APOSTA")

# Função para ser chamada de forma simplificada
def analisar_rapido(minutos, escanteios, linha, odd_over, odd_under, media_escanteios_por_jogo=10.0):
    """Executa a análise e retorna apenas a recomendação."""
    
    # Redireciona a saída para capturar a recomendação
    import io
    import sys
    old_stdout = sys.stdout
    redirected_output = sys.stdout = io.StringIO()
    
    calcular_ev_e_prob(minutos, escanteios, linha, odd_over, odd_under, media_escanteios_por_jogo)
    
    sys.stdout = old_stdout
    output = redirected_output.getvalue()
    
    # Extrai a recomendação da saída
    for line in output.split('\n'):
        if line.startswith("RECOMENDAÇÃO:"):
            return line.replace("RECOMENDAÇÃO: ", "")
    return "ERRO NA ANÁLISE"

# Para uso externo
if __name__ == "__main__":
    # Para rodar de forma interativa no seu computador:
    
    print("--- Analisador de Apostas em Escanteios (Modelo de Poisson) ---")
    print("Tempo Total de Jogo Considerado: 95 minutos (com acréscimos).")
    print("Média de Escanteios por Jogo Padrão: 10.0 (pode ser alterada).")
    
    try:
        minutos_jogados = int(input("1. Minutos de Jogo (ex: 36 ou 45): "))
        escanteios_atuais = int(input("2. Escanteios Atuais (ex: 5 ou 8): "))
        linha_over = float(input("3. Linha de Aposta (ex: 10.5 ou 8.0): "))
        odd_over = float(input("4. Odd do Over (ex: 2.01): "))
        odd_under = float(input("5. Odd do Under (ex: 1.83): "))
        
        # Opcional: Média de escanteios por jogo (use 10.0 se não souber)
        media_input = input("6. Média de Escanteios do Jogo (Opcional, Padrão: 10.0): ")
        media_escanteios = float(media_input) if media_input else 10.0
        
        if minutos_jogados < 0 or minutos_jogados > 95 or escanteios_atuais < 0 or linha_over <= 0 or odd_over <= 1 or odd_under <= 1:
            print("\nERRO: Por favor, insira valores válidos.")
        else:
            calcular_ev_e_prob(minutos_jogados, escanteios_atuais, linha_over, odd_over, odd_under, media_escanteios)

    except ValueError:
        print("\nERRO: Por favor, insira números válidos para todos os campos.")
    except Exception as e:
        print(f"\nOcorreu um erro inesperado: {e}")

