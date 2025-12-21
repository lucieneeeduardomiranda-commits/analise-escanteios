# -*- coding: utf-8 -*-
"""
Analisador de Escanteios v5.0
Calcula valor esperado (EV) para apostas Over/Under em escanteios
Considera tempo total de 95 minutos (incluindo acréscimos)
Usa média de escanteios específica do campeonato
"""
import math
import os

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

def exibir_resultados(resultados, linha_over, media_campeonato):
    """
    Formata e exibe os resultados da análise.
    """
    if not resultados:
        print("\n[ERRO] Não foi possível calcular os resultados. Verifique os dados de entrada.\n")
        return

    print("\n" + "="*60)
    print(f"           RESULTADOS: OVER/UNDER {linha_over}")
    print("="*60)
    print(f"Média do Campeonato: {media_campeonato:.1f} escanteios/jogo")
    print(f"Tempo Total Considerado: {resultados['tempo_total']} minutos (com acréscimos)")
    print(f"Minutos Restantes: {resultados['minutos_restantes']} minutos")
    print(f"Taxa: {resultados['taxa_por_minuto']:.4f} escanteios/minuto")
    print("-" * 60)
    print(f"Escanteios Projetados (restantes): {resultados['projecao_restante']:.2f}")
    print(f"Escanteios Projetados (total final): {resultados['projecao_final']:.2f}")
    print(f"Escanteios Necessários para Over: {resultados['escanteios_necessarios']}")
    print("-" * 60)
    print(f"Probabilidade Over {linha_over}: {resultados['prob_over']*100:.2f}%")
    print(f"Probabilidade Under {linha_over}: {resultados['prob_under']*100:.2f}%")
    print("-" * 60)
    print(f"Valor Esperado (EV) Over: {resultados['ev_over']:.4f}")
    print(f"Valor Esperado (EV) Under: {resultados['ev_under']:.4f}")
    print("=" * 60)
    
    if resultados['ev_over'] > 0.05:
        print(f">>> ✓ RECOMENDAÇÃO: APOSTE NO OVER {linha_over} <<<")
        print(f">>> EV Positivo: {resultados['ev_over']*100:.2f}%) <<<")
    elif resultados['ev_under'] > 0.05:
        print(f">>> ✓ RECOMENDAÇÃO: APOSTE NO UNDER {linha_over} <<<")
        print(f">>> EV Positivo: {resultados['ev_under']*100:.2f}%) <<<")
    else:
        print(">>> ✗ RECOMENDAÇÃO: NÃO APOSTAR (EV INSUFICIENTE) <<<")
        print(f">>> Melhor EV disponível: {max(resultados['ev_over'], resultados['ev_under']):.4f} <<<")
    
    print("=" * 60 + "\n")

def obter_media_campeonato():
    """
    Solicita ao usuário a média de escanteios do campeonato.
    """
    print("\n" + "-" * 60)
    print("MÉDIAS DE REFERÊNCIA (temporada 2024/2025):")
    print("  Premier League: ~11.8 | Bundesliga: ~11.2 | La Liga: ~10.5")
    print("  Serie A: ~10.0 | Brasileirão: ~9.8 | Ligue 1: ~9.2")
    print("-" * 60)
    
    while True:
        try:
            media = float(input("Digite a média de escanteios do campeonato: "))
            if media > 0:
                return media
            else:
                print("[ERRO] A média deve ser maior que zero.")
        except ValueError:
            print("[ERRO] Digite um número válido.")

def main():
    """Função principal para o loop de análise interativa."""
    media_campeonato = obter_media_campeonato()
    
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("="*60)
        print("       ANALISADOR DE ESCANTEIOS v5.0")
        print(f"   Campeonato: {media_campeonato:.1f} escanteios/jogo | Tempo: 95 min")
        print("="*60)
        print("\nDigite os dados da partida ou 'S' para sair, 'M' para mudar a média\n")
        
        try:
            entrada = input("1. Minutos jogados: ").strip().upper()
            if entrada == 'S': break
            if entrada == 'M':
                media_campeonato = obter_media_campeonato()
                continue

            minutos = int(entrada)
            atuais = int(input("2. Escanteios já cobrados: "))
            linha = float(input("3. Linha da aposta (ex: 10.5): "))
            o_over = float(input("4. Odd do Over: "))
            o_under = float(input("5. Odd do Under: "))

            if not (0 <= minutos <= 120 and atuais >= 0 and linha > 0 and o_over > 1 and o_under > 1):
                print("\n[ERRO] Dados inválidos. Verifique os valores e tente novamente.")
                input("\nPressione ENTER para continuar...")
                continue

            resultados = calcular_ev_e_prob(minutos, atuais, linha, o_over, o_under, media_campeonato)
            exibir_resultados(resultados, linha, media_campeonato)
            
            input("Análise concluída. Pressione ENTER para a próxima partida...")

        except (ValueError, TypeError):
            print("\n[ERRO] Use apenas números e ponto (.) para decimais.")
            input("Pressione ENTER para continuar...")
        except KeyboardInterrupt:
            print("\n\nPrograma interrompido.")
            break

if __name__ == "__main__":
    main()
