
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, List

# ================================================
# CONSTANTES E ENUMS COMPLETOS
# ================================================

class Sexo(Enum):
    MASCULINO = "Masculino"
    FEMININO = "Feminino"

class Raca(Enum):
    BRANCA = "Branca"
    NEGRA = "Negra"

class Condicao(Enum):
    OBESIDADE = "obesidade"
    DESNUTRICAO = "desnutricao"

class NivelAtividade(Enum):
    SEDENTARIA = "sedentária"
    BAIXA = "baixa atividade"
    ATIVO = "ativo"
    MUITO_ATIVO = "muito ativo"

class IndiceAntropometrico(Enum):
    PESO_IDADE = "peso_idade"
    PESO_ESTATURA = "peso_estatura"
    IMC_IDADE = "imc_idade"
    ESTATURA_IDADE = "estatura_idade"

class CondicaoMotora(Enum):
    SEM_DISFUNCAO = "sem disfunção motora"
    DEAMBULA_SEM_DISFUNCAO = "não apresentar disfunção mas deambular"
    NAO_DEAMBULA = "não deambular (caminhar)"

class NivelAtividadePC(Enum):
    LEVE_MODERADA = "leve a moderada"
    RESTRITA_INTENSA = "restrita intensa"
    RESTRICAO_GRAVE = "restrição física grave"

# ================================================
# FUNÇÕES NUTRICIONAIS COMPLETAS (27 FÓRMULAS)
# ================================================

# 1. CLASSIFICAÇÃO ANTROPOMÉTRICA (0-5 ANOS) - OMS
def classificar_antropometria_0_5_anos(percentil: float, escore_z: float, 
                                     tipo_indice: IndiceAntropometrico) -> Optional[str]:
    """Classificação OMS para crianças 0-5 anos incompletos."""
    if tipo_indice == IndiceAntropometrico.PESO_IDADE:
        if percentil < 0.1 or escore_z < -3:
            return "Muito baixo peso para a idade"
        elif 0.1 <= percentil < 3 or -3 <= escore_z < -2:
            return "Baixo peso para a idade"
        elif 3 <= percentil < 85 or -2 <= escore_z <= 1:
            return "Peso adequado para a idade"
        elif 85 < percentil <= 97 or 1 < escore_z <= 2:
            return "Peso adequado para a idade"
        elif 97 < percentil <= 99.9 or 2 < escore_z <= 3:
            return "Peso elevado para a idade"
        elif percentil > 99.9 or escore_z > 3:
            return "Obesidade"
    
    elif tipo_indice == IndiceAntropometrico.PESO_ESTATURA:
        if percentil < 0.1 or escore_z < -3:
            return "Magreza acentuada"
        elif 0.1 <= percentil < 3 or -3 <= escore_z < -2:
            return "Magreza"
        elif 3 <= percentil < 85 or -2 <= escore_z <= 1:
            return "Eutrofia"
        elif 85 < percentil <= 97 or 1 < escore_z <= 2:
            return "Risco de sobrepeso"
        elif 97 < percentil <= 99.9 or 2 < escore_z <= 3:
            return "Sobrepeso"
        elif percentil > 99.9 or escore_z > 3:
            return "Obesidade"
    
    elif tipo_indice == IndiceAntropometrico.IMC_IDADE:
        if percentil < 0.1 or escore_z < -3:
            return "Magreza acentuada"
        elif 0.1 <= percentil < 3 or -3 <= escore_z < -2:
            return "Magreza"
        elif 3 <= percentil < 85 or -2 <= escore_z <= 1:
            return "Eutrofia"
        elif 85 < percentil <= 97 or 1 < escore_z <= 2:
            return "Risco de sobrepeso"
        elif 97 < percentil <= 99.9 or 2 < escore_z <= 3:
            return "Sobrepeso"
        elif percentil > 99.9 or escore_z > 3:
            return "Obesidade"
    
    elif tipo_indice == IndiceAntropometrico.ESTATURA_IDADE:
        if percentil < 0.1 or escore_z < -3:
            return "Muito baixa estatura para a idade"
        elif 0.1 <= percentil < 3 or -3 <= escore_z < -2:
            return "Baixa estatura para a idade"
        else:
            return "Estatura adequada para a idade"
    
    return None

# 2. EQUAÇÃO DE SCHOFIELD (APENAS PESO) - Rosa
def tmb_schofield_peso(peso: float, idade: float, sexo: Sexo) -> Optional[float]:
    """Schofield apenas com peso para crianças gravemente doentes."""
    if peso <= 0 or idade < 0:
        return None
    
    if sexo == Sexo.MASCULINO:
        if idade <= 3:
            return 54.48 * peso - 30.33
        elif idade <= 10:
            return 22.7 * peso + 505
        elif idade <= 18:
            return 13.4 * peso + 693
    else:
        if idade <= 3:
            return 58.29 * peso - 31.05
        elif idade <= 10:
            return 20.3 * peso + 486
        elif idade <= 18:
            return 17.7 * peso + 659
    
    return None

# 3. EQUAÇÃO DE SCHOFIELD (PESO + ESTATURA) - Verde
def tmb_schofield_peso_estatura(peso: float, estatura: float, idade: float, 
                               sexo: Sexo) -> Optional[float]:
    """Schofield com peso e estatura para crianças gravemente doentes."""
    if peso <= 0 or estatura <= 0 or idade < 0:
        return None
    
    if sexo == Sexo.MASCULINO:
        if idade <= 3:
            return (0.167 * peso) + (1517.4 * estatura) - 617.6
        elif idade <= 10:
            return (19.6 * peso) + (130.3 * estatura) + 414.9
        elif idade <= 18:
            return (16.25 * peso) + (137.2 * estatura) + 515.5
    else:
        if idade <= 3:
            return (16.25 * peso) + (1023.2 * estatura) - 413.5
        elif idade <= 10:
            return (16.97 * peso) + (161.8 * estatura) + 371.2
        elif idade <= 18:
            return (8.365 * peso) + (465 * estatura) + 200
    
    return None

# 4. COEFICIENTES DE ATIVIDADE FÍSICA
def obter_coeficiente_atividade(sexo: Sexo, nivel: NivelAtividade) -> float:
    """Coeficientes de atividade física para crianças 3-18 anos."""
    tabela = {
        Sexo.MASCULINO: {
            NivelAtividade.SEDENTARIA: 1.00,
            NivelAtividade.BAIXA: 1.13,
            NivelAtividade.ATIVO: 1.26,
            NivelAtividade.MUITO_ATIVO: 1.42
        },
        Sexo.FEMININO: {
            NivelAtividade.SEDENTARIA: 1.00,
            NivelAtividade.BAIXA: 1.16,
            NivelAtividade.ATIVO: 1.31,
            NivelAtividade.MUITO_ATIVO: 1.56
        }
    }
    return tabela[sexo][nivel]

# 5. REQUERIMENTO ENERGÉTICO POR IDADE (0-35 MESES)
def calcular_requerimento_energetico_idade(peso: float, idade_meses: float) -> Optional[float]:
    """Requerimento energético apenas com peso para 0-35 meses."""
    if peso <= 0 or idade_meses < 0:
        return None
    
    if idade_meses <= 3:  # 0-3 meses
        return (89 * peso - 100) + 175
    elif idade_meses <= 6:  # 4-6 meses
        return (89 * peso - 100) + 56
    elif idade_meses <= 12:  # 7-12 meses
        return (89 * peso - 100) + 22
    elif idade_meses <= 35:  # 13-35 meses
        return (89 * peso - 100) + 20
    else:
        return None

# 6. REQUERIMENTO ENERGÉTICO COMPLETO (3-18 ANOS)
def calcular_requerimento_energetico_completo(peso: float, estatura: float, idade_anos: float, 
                                            sexo: Sexo, fator_atividade: float) -> Optional[float]:
    """Requerimento com peso, estatura e atividade para 3-18 anos."""
    if peso <= 0 or estatura <= 0 or idade_anos < 0 or fator_atividade <= 0:
        return None
    
    if 3 <= idade_anos < 9:
        if sexo == Sexo.MASCULINO:
            return 88.5 - 61.9 * idade_anos + fator_atividade * (26.7 * peso + 903 * estatura) + 20
        else:
            return 135.3 - 30.8 * idade_anos + fator_atividade * (10 * peso + 934 * estatura) + 20
    elif 9 <= idade_anos <= 18:
        if sexo == Sexo.MASCULINO:
            return 88.5 - 61.9 * idade_anos + fator_atividade * (26.7 * peso + 903 * estatura) + 25
        else:
            return 135.3 - 30.8 * idade_anos + fator_atividade * (10 * peso + 934 * estatura) + 25
    
    return None

# 7. CORREÇÃO DE PREMATURIDADE
def calcular_idade_corrigida(idade_cronologica_meses: float, 
                           idade_gestacional_semanas: float) -> float:
    """Correção de idade para prematuros até 2 anos."""
    if idade_gestacional_semanas < 20 or idade_gestacional_semanas > 42:
        raise ValueError("Idade gestacional deve estar entre 20-42 semanas")
    
    idade_gestacional_meses = idade_gestacional_semanas / 4.34524
    return idade_cronologica_meses - (40 / 4.34524 - idade_gestacional_meses)

# 8. PACIENTE COM PC ENFERMO (×1.1)
def necessidade_energetica_pc_enfermo(peso: float, altura_cm: float, 
                                    idade: float, sexo: Sexo) -> float:
    """Paciente com Paralisia Cerebral enfermo com fator 1.1."""
    if sexo == Sexo.MASCULINO:
        base = 66.5 + (13.75 * peso) + (5.003 * altura_cm) - (6.775 * idade)
    else:
        base = 65.1 + (9.56 * peso) + (1.85 * altura_cm) - (4.676 * idade)
    
    return base * 1.1

# 9. GEB PARA UTI (>2 ANOS)
def geb_uti_ventilacao_mecanica(idade_meses: float, peso: float, 
                              temperatura_c: float) -> float:
    """GEB para UTI pediátrica, ventilação mecânica, >2 anos."""
    if idade_meses < 24:
        raise ValueError("Fórmula válida apenas para idade acima de 2 anos (24 meses)")
    
    return ((17 * idade_meses) + (48 * peso) + (292 * temperatura_c) - 9677) * 0.239

# 10. PERCENTUAL ALCANÇADO
def calcular_percentual_alcançado(valor_consumido: float, necessidade: float) -> float:
    """Calcula percentual alcançado de nutrientes/energia."""
    if necessidade <= 0:
        raise ValueError("Necessidade deve ser maior que zero")
    
    return (valor_consumido / necessidade) * 100

# 11. TMB PADRÃO (NÃO SCHOFIELD)
def calcular_tmb_padrao(peso: float, idade: float, sexo: Sexo) -> Optional[float]:
    """Taxa Metabólica Basal padrão para crianças/adolescentes."""
    if peso <= 0 or idade < 0:
        return None
    
    if sexo == Sexo.MASCULINO:
        if idade <= 3:
            return 60.9 * peso - 54
        elif idade <= 10:
            return 22.7 * peso + 495
        elif idade <= 18:
            return 17.5 * peso + 651
    else:
        if idade <= 3:
            return 61 * peso - 51
        elif idade <= 10:
            return 22.5 * peso + 499
        elif idade <= 18:
            return 12.2 * peso + 746
    
    return None

# 12. PESO AJUSTADO
def calcular_peso_ajustado(peso_atual: float, peso_ideal: float, 
                          condicao: Condicao) -> Optional[float]:
    """Calcula peso ajustado para obesidade ou desnutrição."""
    if peso_atual <= 0 or peso_ideal <= 0:
        return None
    
    if condicao == Condicao.OBESIDADE:
        return (peso_atual - peso_ideal) * 0.25 + peso_ideal
    elif condicao == Condicao.DESNUTRICAO:
        return (peso_atual - peso_ideal) * 0.25 + peso_atual
    
    return None

# 13. PERDA DE PESO (%)
def calcular_perda_peso(peso_usual: float, peso_atual: float) -> Optional[float]:
    """Calcula percentual de perda de peso."""
    if peso_usual <= 0:
        return None
    return ((peso_usual - peso_atual) / peso_usual) * 100

# 14. ESTIMATIVA DE PESO (6-18 ANOS)
def estimar_peso_crianca(altura_joelho: float, perimetro_braco: float, 
                        sexo: Sexo, raca: Raca) -> Optional[float]:
    """Estimativa de peso para crianças/adolescentes 6-18 anos."""
    if altura_joelho <= 0 or perimetro_braco <= 0:
        return None
    
    if sexo == Sexo.MASCULINO:
        if raca == Raca.BRANCA:
            return altura_joelho * 0.68 + perimetro_braco * 2.64 - 50.08
        elif raca == Raca.NEGRA:
            return altura_joelho * 0.59 + perimetro_braco * 2.73 - 48.32
    elif sexo == Sexo.FEMININO:
        if raca == Raca.BRANCA:
            return altura_joelho * 0.77 + perimetro_braco * 2.47 - 50.16
        elif raca == Raca.NEGRA:
            return altura_joelho * 0.71 + perimetro_braco * 2.59 - 50.43
    return None

# 15. ESTIMATIVA DE ESTATURA PELA TÍBIA
def estimar_estatura_tibia(comprimento_tibia: float) -> float:
    """Estimativa de estatura pela medida da tíbia."""
    if comprimento_tibia <= 0:
        raise ValueError("Comprimento da tíbia deve ser positivo")
    return 3.26 * comprimento_tibia + 30.8

# 16. ESTIMATIVA DE ESTATURA PELA ULNA
def estimar_estatura_ulna(comprimento_ulna: float) -> float:
    """Estimativa de estatura pela medida da ulna."""
    if comprimento_ulna <= 0:
        raise ValueError("Comprimento da ulna deve ser positivo")
    return 5.45 * comprimento_ulna + 20.7

# 17. PERCENTUAL DE GORDURA CORPORAL
def calcular_percentual_gordura(soma_dobras: float, sexo: Sexo, 
                              estagio_tanner: int, raca: Raca) -> Optional[float]:
    """Estimativa do percentual de gordura corporal (Slaughter)."""
    if soma_dobras <= 0:
        return None
    
    if estagio_tanner not in [1, 2, 3, 4, 5]:
        return None
    
    if soma_dobras > 35:
        if sexo == Sexo.MASCULINO:
            return 0.783 * soma_dobras + 1.6
        else:
            return 0.546 * soma_dobras + 9.7
    else:
        if sexo == Sexo.MASCULINO:
            if raca == Raca.BRANCA:
                if estagio_tanner in [1, 2]:
                    return 1.21 * soma_dobras - 0.008 * (soma_dobras ** 2) - 1.7
                elif estagio_tanner == 3:
                    return 1.21 * soma_dobras - 0.008 * (soma_dobras ** 2) - 3.4
                elif estagio_tanner in [4, 5]:
                    return 1.21 * soma_dobras - 0.008 * (soma_dobras ** 2) - 5.5
            elif raca == Raca.NEGRA:
                if estagio_tanner in [1, 2]:
                    return 1.21 * soma_dobras - 0.008 * (soma_dobras ** 2) - 3.2
                elif estagio_tanner == 3:
                    return 1.21 * soma_dobras - 0.008 * (soma_dobras ** 2) - 5.2
                elif estagio_tanner in [4, 5]:
                    return 1.21 * soma_dobras - 0.008 * (soma_dobras ** 2) - 6.8
        else:
            return 1.33 * soma_dobras - 0.013 * (soma_dobras ** 2) - 2.5
    
    return None

# 18. CIRCUNFERÊNCIA MUSCULAR DO BRAÇO (CMB)
def calcular_circ_muscular_braco(perimetro_braco: float, 
                               dobra_tricipital: float) -> float:
    """Calcula a circunferência muscular do braço."""
    if perimetro_braco <= 0 or dobra_tricipital <= 0:
        raise ValueError("Medidas devem ser positivas")
    return perimetro_braco - (0.314 * (dobra_tricipital / 10))

# 19. ÁREA MUSCULAR DO BRAÇO (AMB)
def calcular_area_muscular_braco(circunferencia_braco: float, 
                               dobra_tricipital: float) -> float:
    """Calcula a área muscular do braço."""
    if circunferencia_braco <= 0 or dobra_tricipital <= 0:
        raise ValueError("Medidas devem ser positivas")
    dobra_cm = dobra_tricipital / 10
    return ((circunferencia_braco - 0.314 * dobra_cm) ** 2) / 12.56

# 20. ÁREA GORDA DO BRAÇO (AGB)
def calcular_area_gorda_braco(circunferencia_braco: float, 
                            area_muscular_braco: float) -> float:
    """Calcula a área gorda do braço."""
    if circunferencia_braco <= 0 or area_muscular_braco <= 0:
        raise ValueError("Medidas devem ser positivas")
    return 0.79 * ((circunferencia_braco / 3.14) ** 2) - area_muscular_braco

# 21. ESTIMATIVA DE ESTATURA PC (2-12 ANOS)
def estimar_estatura_paralisia_cerebral(comprimento_superior: float, 
                                       comprimento_tibial: float, 
                                       comprimento_joelho: float) -> Dict[str, float]:
    """Estimativa de estatura para crianças com PC 2-12 anos."""
    medidas = {
        'Estimada_CT': 3.26 * comprimento_tibial + 30.8 + 1.4,
        'Estimada_CS': 4.35 * comprimento_superior + 21.8 + 1.7,
        'Estimada_CJ': 2.69 * comprimento_joelho + 24.2 + 1.1
    }
    return medidas

# 22. ESTIMATIVA DE ESTATURA ADOLESCENTE PC
def estimar_estatura_paralisia_adolescente(idade: float, sexo: Sexo, 
                                          comprimento_ulna: float) -> float:
    """Estimativa de estatura para adolescentes com PC."""
    sexo_bin = 1 if sexo == Sexo.MASCULINO else 0
    return 30.35 + (1.29 * idade) + (0.77 * sexo_bin) + (4.32 * comprimento_ulna)

# 23. PESO CORRIGIDO PARA AMPUTAÇÃO
def calcular_peso_corrigido_amputacao(peso_atual: float, 
                                     percentual_amputacao: float) -> float:
    """Calcula peso corrigido para pacientes amputados."""
    if peso_atual <= 0:
        raise ValueError("Peso atual deve ser positivo")
    if percentual_amputacao < 0 or percentual_amputacao >= 100:
        raise ValueError("Percentual de amputação deve estar entre 0-100%")
    return peso_atual * 100 / (100 - percentual_amputacao)

# 24. GASTO ENERGÉTICO TOTAL (GET)
def calcular_gasto_energetico_total(ere: float, 
                                   fator_atividade: Optional[float] = None, 
                                   fator_estresse: Optional[float] = None) -> float:
    """Calcula gasto energético total com fatores."""
    if ere <= 0:
        raise ValueError("ERE deve ser positivo")
    
    if fator_atividade and fator_estresse:
        raise ValueError("Use apenas fator de atividade OU fator de estresse")
    
    if fator_atividade:
        return ere * fator_atividade
    elif fator_estresse:
        return ere * fator_estresse
    return ere

# 25. NECESSIDADE ENERGÉTICA PC 5-11 ANOS
def necessidade_energetica_pc_5_11(altura: float, 
                                  nivel_atividade: str) -> float:
    """Necessidade energética para crianças com PC 5-11 anos."""
    if nivel_atividade == NivelAtividadePC.LEVE_MODERADA.value:
        return 13.9 * altura
    elif nivel_atividade == NivelAtividadePC.RESTRITA_INTENSA.value:
        return 10 * altura
    elif nivel_atividade == NivelAtividadePC.RESTRICAO_GRAVE.value:
        return 11.1 * altura
    return 0

# 26. NECESSIDADE ENERGÉTICA PC ESTÁVEIS
def necessidade_energetica_pc_estaveis(altura: float, 
                                     condicao_motora: str) -> float:
    """Necessidade energética para crianças/adolescentes com PC estáveis."""
    if condicao_motora == CondicaoMotora.SEM_DISFUNCAO.value:
        return 15 * altura
    elif condicao_motora == CondicaoMotora.NAO_DEAMBULA.value:
        return 11 * altura
    elif condicao_motora == CondicaoMotora.DEAMBULA_SEM_DISFUNCAO.value:
        return 14 * altura
    return 0

# 27. NECESSIDADE ENERGÉTICA PC GERAL
def necessidade_energetica_pc(peso: float, altura: float, 
                             idade: float, sexo: Sexo) -> float:
    """Necessidades energéticas em crianças com PC (Harris-Benedict adaptado)."""
    if sexo == Sexo.MASCULINO:
        return 66.5 + (13.75 * peso) + (5.003 * altura) - (6.775 * idade)
    else:
        return 65.1 + (9.56 * peso) + (1.85 * altura) - (4.676 * idade)

# 28. NECESSIDADE SÍNDROME DE DOWN
def necessidade_sindrome_down(altura: float, sexo: Sexo) -> float:
    """Necessidade energética para crianças com Síndrome de Down."""
    if sexo == Sexo.MASCULINO:
        return 16.1 * altura
    else:
        return 14.3 * altura

# 29. NECESSIDADES NUTRICIONAIS PC (COM FATOR ESTRESSE)
def calcular_necessidade_pc(peso: float, altura: float, sexo: Sexo, 
                           idade: float, fator_estresse: float) -> Optional[float]:
    """Calcula necessidades nutricionais para paralisia cerebral."""
    if peso <= 0 or altura <= 0 or idade < 0 or fator_estresse <= 0:
        return None
    
    if sexo == Sexo.FEMININO:
        if idade <= 3:
            base = 16.25 * peso + 1023.2 * altura - 413.5
        elif idade <= 10:
            base = 16.97 * peso + 161.8 * altura + 371.2
        elif idade <= 18:
            base = 8.365 * peso + 465 * altura + 200
    else:
        if idade <= 3:
            base = 0.167 * peso + 1517.4 * altura - 617.6
        elif idade <= 10:
            base = 19.6 * peso + 130.3 * altura + 414.9
        elif idade <= 18:
            base = 16.25 * peso + 137.2 * altura + 515.5
    return base * fator_estresse

# 30. GEB CRÍTICA
def geb_critica(idade_meses: float, peso: float, temp_c: float) -> float:
    """Gasto Energético Basal para crianças criticamente enfermas."""
    return ((17 * idade_meses) + (48 * peso) + (292 * temp_c) - 9677) * 0.239

# ================================================
# INTERFACE STREAMLIT COMPLETA
# ================================================

def main():
    st.set_page_config(
        page_title="Calculadora Nutricional Completa",
        page_icon="🍎",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # CSS Estilos
    st.markdown("""
    <style>
    .main-header {
        background-color: #4CAF50;
        color: white;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .result-box {
        background-color: #f0f8ff;
        padding: 25px;
        border-radius: 10px;
        border-left: 6px solid #4CAF50;
        margin: 20px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .warning-box {
        background-color: #fff3cd;
        padding: 15px;
        border-radius: 8px;
        border-left: 5px solid #ffc107;
        margin: 15px 0;
    }
    .info-box {
        background-color: #d1ecf1;
        padding: 15px;
        border-radius: 8px;
        border-left: 5px solid #17a2b8;
        margin: 15px 0;
    }
    .formula-box {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #dee2e6;
        font-family: 'Courier New', monospace;
        margin: 10px 0;
    }
    .section-divider {
        border-top: 2px solid #4CAF50;
        margin: 30px 0;
    }
    .sidebar-header {
        color: #4CAF50;
        font-weight: bold;
        margin-top: 20px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # ================================================
    # BARRA LATERAL - MENU PRINCIPAL
    # ================================================
    with st.sidebar:
        st.markdown('<div class="main-header">🍏 Calculadora Nutricional Completa</div>', unsafe_allow_html=True)
        
        # Menu de Navegação
        st.markdown("### 📋 Menu Principal")
        modulo = st.selectbox(
            "Selecione o módulo:",
            [
                "🏠 Página Inicial",
                "📊 Classificação Antropométrica (0-5 anos)",
                "⚡ Metabolismo - Schofield",
                "🔥 Requerimento Energético",
                "📐 Antropometria Avançada",
                "🦽 Paralisia Cerebral",
                "🏥 Condições Especiais",
                "📈 Monitoramento Nutricional",
                "⚖️ Cálculos Gerais"
            ],
            index=0
        )
        
        st.markdown("---")
        
        # Info sobre fórmulas
        st.markdown("### 📚 Fórmulas Disponíveis")
        st.info("""
        **Total: 30 fórmulas**
        - Antropometria: 9 fórmulas
        - Metabolismo: 5 fórmulas
        - PC/Especiais: 9 fórmulas
        - Gerais: 7 fórmulas
        """)
        
        st.markdown("---")
        
        # Histórico simples
        if 'historico' not in st.session_state:
            st.session_state.historico = []
        
        if st.button("🗑️ Limpar Histórico"):
            st.session_state.historico = []
    
    # ================================================
    # PÁGINA INICIAL
    # ================================================
    if modulo == "🏠 Página Inicial":
        st.markdown('<div class="main-header">🍏 Calculadora Nutricional Completa</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown("""
            ### 🌟 Sistema Completo de Cálculos Nutricionais
            
            Esta aplicação reúne **30 fórmulas nutricionais** validadas para avaliação 
            e prescrição nutricional pediátrica e de condições especiais.
            
            **Desenvolvido para:** Nutricionistas, Médicos e Profissionais de Saúde
            """)
        
        with col2:
            st.metric("📊 Fórmulas", "30", "+27 desde v1.0")
            st.metric("🏥 Condições", "12", "Especiais")
            st.metric("👶 Faixa Etária", "0-18 anos", "Completa")
        
        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
        
        # Categorias de Fórmulas
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("### 📊 Antropometria")
            st.markdown("""
            - **Classificação 0-5 anos** - OMS
            - **Estimativa de peso** (6-18 anos)
            - **Estimativa de estatura** (Tíbia/Ulna)
            - **Composição corporal**:
              * Percentual de gordura
              * CMB, AMB, AGB
            """)
        
        with col2:
            st.markdown("### ⚡ Metabolismo")
            st.markdown("""
            - **Equação de Schofield**:
              * Apenas peso (rosa)
              * Peso + estatura (verde)
            - **TMB padrão** (0-18 anos)
            - **Requerimento energético**:
              * 0-35 meses
              * 3-18 anos com atividade
            - **Gasto energético total** (GET)
            """)
        
        with col3:
            st.markdown("### 🏥 Condições Especiais")
            st.markdown("""
            - **Paralisia Cerebral**:
              * PC enfermo (×1.1)
              * PC 5-11 anos
              * PC estáveis
              * PC geral
            - **Síndrome de Down**
            - **UTI pediátrica**
            - **Prematuridade**
            """)
        
        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
        
        # Lista completa de fórmulas
        st.markdown("### 📋 Fórmulas Implementadas (30 Total)")
        
        formulas_categorizadas = {
            "📊 Antropometria (9)": [
                "✅ Classificação antropométrica OMS (0-5 anos)",
                "✅ Estimativa de peso (crianças 6-18 anos)",
                "✅ Estimativa de estatura pela tíbia",
                "✅ Estimativa de estatura pela ulna",
                "✅ Percentual de gordura corporal",
                "✅ Circunferência muscular do braço (CMB)",
                "✅ Área muscular do braço (AMB)",
                "✅ Área gorda do braço (AGB)",
                "✅ Estimativa estatura PC (2-12 anos)"
            ],
            "⚡ Metabolismo (5)": [
                "✅ Equação de Schofield (peso)",
                "✅ Equação de Schofield (peso+estatura)",
                "✅ TMB padrão (0-18 anos)",
                "✅ Requerimento energético por idade",
                "✅ Gasto energético total (GET)"
            ],
            "🦽 Paralisia Cerebral (9)": [
                "✅ PC enfermo (×1.1)",
                "✅ Necessidade PC 5-11 anos",
                "✅ Necessidade PC estáveis",
                "✅ Necessidade PC geral",
                "✅ Necessidades nutricionais PC",
                "✅ Estimativa estatura adolescente PC",
                "✅ Coeficientes de atividade física",
                "✅ Peso ajustado (obesidade/desnutrição)",
                "✅ Perda de peso (%)"
            ],
            "🏥 Condições Especiais (7)": [
                "✅ Síndrome de Down",
                "✅ UTI pediátrica (>2 anos)",
                "✅ Correção de prematuridade",
                "✅ GEB criança criticamente enferma",
                "✅ Peso corrigido para amputação",
                "✅ Percentual alcançado",
                "✅ Peso ajustado e perda de peso"
            ]
        }
        
        for categoria, formulas in formulas_categorizadas.items():
            with st.expander(categoria):
                for formula in formulas:
                    st.markdown(f"• {formula}")
        
        st.markdown("---")
        st.info("💡 **Dica:** Use o menu lateral para navegar entre os diferentes módulos.")
    
    # ================================================
    # MÓDULO: CLASSIFICAÇÃO ANTROPOMÉTRICA
    # ================================================
    elif modulo == "📊 Classificação Antropométrica (0-5 anos)":
        st.markdown('<div class="main-header">📊 Classificação Antropométrica (0-5 anos incompletos)</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown("""
            ### 📏 Classificação OMS
            
            Classificação do estado nutricional conforme padrões da 
            Organização Mundial da Saúde para crianças de 0 a 5 anos incompletos.
            """)
        
        with col2:
            st.info("""
            **Referência:**
            - OMS, 2006
            - Curvas de crescimento
            - Valores em percentil ou escore Z
            """)
        
        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
        
        # Interface de entrada
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.subheader("📈 Valores Antropométricos")
            percentil = st.number_input("Percentil", 
                                       min_value=0.0, 
                                       max_value=100.0, 
                                       value=50.0, 
                                       step=0.1,
                                       help="Percentil da medida (0-100)")
            
            escore_z = st.number_input("Escore Z", 
                                      min_value=-5.0, 
                                      max_value=5.0, 
                                      value=0.0, 
                                      step=0.1,
                                      help="Escore Z padrão (-5 a +5)")
        
        with col2:
            st.subheader("📋 Índice Antropométrico")
            indice = st.selectbox(
                "Selecione o índice:",
                options=[e.value for e in IndiceAntropometrico],
                format_func=lambda x: {
                    "peso_idade": "📊 Peso para Idade",
                    "peso_estatura": "⚖️ Peso para Estatura", 
                    "imc_idade": "📐 IMC para Idade",
                    "estatura_idade": "📏 Estatura para Idade"
                }[x],
                help="Índice antropométrico para classificação"
            )
        
        with col3:
            st.subheader("🎯 Interpretação")
            st.markdown("""
            **Classificação por cores:**
            - 🔴 **Vermelho**: Muito baixo / Obesidade
            - 🟠 **Laranja**: Baixo / Sobrepeso
            - 🟢 **Verde**: Adequado
            - 🟡 **Amarelo**: Risco
            """)
        
        # Botão de cálculo
        if st.button("🔍 Classificar Estado Nutricional", type="primary", use_container_width=True):
            resultado = classificar_antropometria_0_5_anos(
                percentil, escore_z, IndiceAntropometrico(indice)
            )
            
            if resultado:
                # Determinar cor
                if "muito baixo" in resultado.lower() or "magreza acentuada" in resultado.lower() or "obesidade" in resultado.lower():
                    cor = "#dc3545"  # Vermelho
                    emoji = "🔴"
                elif "baixo" in resultado.lower() or "magreza" in resultado.lower() or "sobrepeso" in resultado.lower() or "elevado" in resultado.lower():
                    cor = "#fd7e14"  # Laranja
                    emoji = "🟠"
                elif "adequado" in resultado.lower() or "eutrofia" in resultado.lower():
                    cor = "#28a745"  # Verde
                    emoji = "🟢"
                elif "risco" in resultado.lower():
                    cor = "#ffc107"  # Amarelo
                    emoji = "🟡"
                else:
                    cor = "#17a2b8"  # Azul
                    emoji = "🔵"
                
                # Exibir resultado
                st.markdown(f"""
                <div class="result-box" style="border-left-color:{cor}">
                    <h2>{emoji} Resultado da Classificação</h2>
                    <h1 style="color:{cor}">{resultado}</h1>
                    <p><strong>Percentil:</strong> {percentil:.1f}</p>
                    <p><strong>Escore Z:</strong> {escore_z:.2f}</p>
                    <p><strong>Índice:</strong> {{
                        'peso_idade': 'Peso para Idade',
                        'peso_estatura': 'Peso para Estatura',
                        'imc_idade': 'IMC para Idade',
                        'estatura_idade': 'Estatura para Idade'
                    }}['{indice}']</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Adicionar ao histórico
                st.session_state.historico.append({
                    'modulo': modulo,
                    'resultado': resultado,
                    'data': datetime.now().strftime("%H:%M")
                })
                
                # Tabela de referência
                with st.expander("📊 Tabela de Classificação (OMS)"):
                    if "peso_idade" in indice:
                        df = pd.DataFrame({
                            'Classificação': ['Muito baixo peso', 'Baixo peso', 'Peso adequado', 
                                            'Peso adequado (risco)', 'Peso elevado', 'Obesidade'],
                            'Percentil': ['<0,1', '≥0,1 e <3', '≥3 e <85', '>85 e ≤97', '>97 e ≤99,9', '>99,9'],
                            'Escore Z': ['<-3', '≥-3 e <-2', '≥-2 e ≤+1', '>+1 e ≤+2', '>+2 e ≤+3', '>+3']
                        })
                    elif "peso_estatura" in indice or "imc_idade" in indice:
                        df = pd.DataFrame({
                            'Classificação': ['Magreza acentuada', 'Magreza', 'Eutrofia', 
                                            'Risco de sobrepeso', 'Sobrepeso', 'Obesidade'],
                            'Percentil': ['<0,1', '≥0,1 e <3', '≥3 e <85', '≥85 e ≤97', '>97 e ≤99,9', '>99,9'],
                            'Escore Z': ['<-3', '≥-3 e <-2', '≥-2 e ≤+1', '>+1 e ≤+2', '>+2 e ≤+3', '>+3']
                        })
                    else:  # estatura_idade
                        df = pd.DataFrame({
                            'Classificação': ['Muito baixa estatura', 'Baixa estatura', 'Estatura adequada'],
                            'Percentil': ['<0,1', '≥0,1 e <3', '≥3'],
                            'Escore Z': ['<-3', '≥-3 e <-2', '≥-2']
                        })
                    
                    st.dataframe(df, use_container_width=True, hide_index=True)
            
            else:
                st.error("❌ Não foi possível classificar. Verifique os valores inseridos.")
    
    # ================================================
    # MÓDULO: EQUAÇÃO DE SCHOFIELD
    # ================================================
    elif modulo == "⚡ Metabolismo - Schofield":
        st.markdown('<div class="main-header">⚡ Equação de Schofield para Crianças Gravemente Doentes</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown("""
            ### 🔬 Equação de Schofield
            
            Duas versões da equação para crianças gravemente doentes:
            1. **🌸 Apenas Peso** (Rosa) - Quando não há medida de estatura
            2. **🌿 Peso + Estatura** (Verde) - Mais precisa com estatura
            """)
        
        with col2:
            st.warning("""
            **Atenção:**
            - Para crianças **gravemente doentes**
            - Faixa etária: **0-18 anos**
            - Não usar para adultos
            """)
        
        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
        
        # Dados do paciente
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("👤 Dados do Paciente")
            peso = st.number_input("Peso (kg)", 
                                  min_value=0.1, 
                                  max_value=150.0, 
                                  value=15.0, 
                                  step=0.1,
                                  help="Peso em quilogramas")
            
            estatura = st.number_input("Estatura (metros)", 
                                      min_value=0.3, 
                                      max_value=2.5, 
                                      value=1.0, 
                                      step=0.01,
                                      help="Estatura em metros")
            
            idade = st.number_input("Idade (anos)", 
                                   min_value=0.0, 
                                   max_value=18.0, 
                                   value=5.0, 
                                   step=0.1,
                                   help="Idade em anos completos")
            
            sexo = st.selectbox("Sexo", 
                               options=[s.value for s in Sexo],
                               help="Sexo biológico")
        
        with col2:
            st.subheader("⚙️ Configuração do Cálculo")
            
            tipo_formula = st.radio(
                "Selecione a fórmula:",
                ["🌸 Apenas Peso (Rosa)", "🌿 Peso e Estatura (Verde)"],
                index=0,
                help="Escolha a fórmula apropriada"
            )
            
            st.markdown("""
            <div class="info-box">
            <strong>Diferenças:</strong><br>
            • <strong style="color:#ff69b4">Rosa:</strong> 54.48 × Peso - 30.33 (M 0-3 anos)<br>
            • <strong style="color:#28a745">Verde:</strong> 0.167 × Peso + 1517.4 × Estatura - 617.6 (M 0-3 anos)
            </div>
            """, unsafe_allow_html=True)
        
        # Botão de cálculo
        if st.button("⚡ Calcular TMB Schofield", type="primary", use_container_width=True):
            sexo_enum = Sexo.MASCULINO if sexo == "Masculino" else Sexo.FEMININO
            
            if "Apenas Peso" in tipo_formula:
                resultado = tmb_schofield_peso(peso, idade, sexo_enum)
                formula_usada = "Apenas Peso (Rosa)"
                cor = "#ff69b4"
                emoji = "🌸"
            else:
                resultado = tmb_schofield_peso_estatura(peso, estatura, idade, sexo_enum)
                formula_usada = "Peso e Estatura (Verde)"
                cor = "#28a745"
                emoji = "🌿"
            
            if resultado is None:
                st.error("❌ Idade fora da faixa suportada (0-18 anos)")
            else:
                # Exibir resultado
                st.markdown(f"""
                <div class="result-box" style="border-left-color:{cor}">
                    <h2>{emoji} Taxa Metabólica Basal (Schofield)</h2>
                    <h1 style="color:{cor}">{resultado:.0f} kcal/dia</h1>
                    <p><strong>Fórmula:</strong> {formula_usada}</p>
                    <p><strong>Detalhes:</strong> {sexo}, {idade:.1f} anos, {peso:.1f} kg{', ' + str(estatura) + ' m' if 'Verde' in formula_usada else ''}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Comparação com TMB padrão
                tmb_padrao = calcular_tmb_padrao(peso, idade, sexo_enum)
                if tmb_padrao:
                    diferenca = resultado - tmb_padrao
                    percentual = (diferenca / tmb_padrao) * 100
                    
                    st.markdown("### 📊 Comparação com TMB Padrão")
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("TMB Schofield", f"{resultado:.0f} kcal", "")
                    
                    with col2:
                        st.metric("TMB Padrão", f"{tmb_padrao:.0f} kcal", "")
                    
                    with col3:
                        st.metric("Diferença", f"{diferenca:+.0f} kcal", f"{percentual:+.1f}%")
                
                # Adicionar ao histórico
                st.session_state.historico.append({
                    'modulo': modulo,
                    'resultado': f"{resultado:.0f} kcal",
                    'data': datetime.now().strftime("%H:%M")
                })
    
    # ================================================
    # MÓDULO: REQUERIMENTO ENERGÉTICO
    # ================================================
    elif modulo == "🔥 Requerimento Energético":
        st.markdown('<div class="main-header">🔥 Requerimento Energético para Crianças/Adolescentes</div>', unsafe_allow_html=True)
        
        # Seleção de faixa etária
        idade_tipo = st.radio(
            "Selecione a faixa etária:",
            ["👶 0-35 meses (apenas peso)", "🧒 3-18 anos (peso, estatura e atividade)"],
            index=1,
            horizontal=True
        )
        
        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
        
        # 0-35 MESES
        if "0-35" in idade_tipo:
            st.subheader("👶 Bebês (0-35 meses)")
            
            col1, col2 = st.columns(2)
            
            with col1:
                peso = st.number_input("Peso (kg)", 
                                      min_value=0.1, 
                                      max_value=50.0, 
                                      value=8.0, 
                                      step=0.1,
                                      help="Peso atual em kg")
            
            with col2:
                idade_meses = st.number_input("Idade (meses)", 
                                            min_value=0.0, 
                                            max_value=35.0, 
                                            value=6.0, 
                                            step=0.1,
                                            help="Idade em meses completos")
            
            # Botão de cálculo
            if st.button("🔥 Calcular Requerimento", type="primary", use_container_width=True):
                resultado = calcular_requerimento_energetico_idade(peso, idade_meses)
                
                if resultado is None:
                    st.error("❌ Dados inválidos ou idade fora da faixa")
                else:
                    # Determinar faixa específica
                    if idade_meses <= 3:
                        faixa = "0-3 meses"
                        constante = 175
                    elif idade_meses <= 6:
                        faixa = "4-6 meses"
                        constante = 56
                    elif idade_meses <= 12:
                        faixa = "7-12 meses"
                        constante = 22
                    else:
                        faixa = "13-35 meses"
                        constante = 20
                    
                    # Exibir resultado
                    st.markdown(f"""
                    <div class="result-box">
                        <h2>👶 Requerimento Energético</h2>
                        <h1 style="color:#FF6B6B">{resultado:.0f} kcal/dia</h1>
                        <p><strong>Faixa etária:</strong> {faixa}</p>
                        <p><strong>Fórmula:</strong> (89 × {peso} - 100) + {constante} = {resultado:.0f}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Tabela de referência
                    with st.expander("📋 Tabela de Referência"):
                        df = pd.DataFrame({
                            'Faixa Etária': ['0-3 meses', '4-6 meses', '7-12 meses', '13-35 meses'],
                            'Fórmula': ['(89×P-100)+175', '(89×P-100)+56', '(89×P-100)+22', '(89×P-100)+20'],
                            'Exemplo (8kg)': ['(89×8-100)+175 = 787', '(89×8-100)+56 = 668', 
                                            '(89×8-100)+22 = 634', '(89×8-100)+20 = 632']
                        })
                        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # 3-18 ANOS
        else:
            st.subheader("🧒 Crianças/Adolescentes (3-18 anos)")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("#### 📏 Dados Antropométricos")
                peso = st.number_input("Peso (kg)", 
                                      min_value=1.0, 
                                      max_value=150.0, 
                                      value=25.0, 
                                      step=0.1)
                
                estatura = st.number_input("Estatura (metros)", 
                                         min_value=0.5, 
                                         max_value=2.5, 
                                         value=1.2, 
                                         step=0.01)
            
            with col2:
                st.markdown("#### 👤 Dados Pessoais")
                idade_anos = st.number_input("Idade (anos)", 
                                           min_value=3.0, 
                                           max_value=18.0, 
                                           value=8.0, 
                                           step=0.1)
                
                sexo = st.selectbox("Sexo", 
                                   options=[s.value for s in Sexo])
            
            with col3:
                st.markdown("#### 🏃 Nível de Atividade")
                nivel = st.selectbox(
                    "Nível:",
                    options=[n.value for n in NivelAtividade],
                    help="Nível de atividade física habitual"
                )
            
            # Obter coeficiente
            sexo_enum = Sexo.MASCULINO if sexo == "Masculino" else Sexo.FEMININO
            nivel_enum = NivelAtividade(nivel)
            fator_atividade = obter_coeficiente_atividade(sexo_enum, nivel_enum)
            
            # Mostrar coeficiente
            st.markdown(f"""
            <div class="info-box">
                <strong>📊 Coeficiente de Atividade:</strong> {fator_atividade:.2f}<br>
                <strong>Tabela para {sexo}:</strong><br>
                • 🛋️ Sedentária: 1.00<br>
                • 🚶 Baixa atividade: {1.13 if sexo == "Masculino" else 1.16}<br>
                • 🏃 Ativo: {1.26 if sexo == "Masculino" else 1.31}<br>
                • 🏋️ Muito ativo: {1.42 if sexo == "Masculino" else 1.56}
            </div>
            """, unsafe_allow_html=True)
            
            # Botão de cálculo
            if st.button("🔥 Calcular Requerimento Completo", type="primary", use_container_width=True):
                resultado = calcular_requerimento_energetico_completo(
                    peso, estatura, idade_anos, sexo_enum, fator_atividade
                )
                
                if resultado is None:
                    st.error("❌ Idade fora da faixa suportada (3-18 anos)")
                else:
                    faixa = "3-8 anos" if idade_anos < 9 else "9-18 anos"
                    constante = 20 if idade_anos < 9 else 25
                    
                    # Exibir resultado
                    st.markdown(f"""
                    <div class="result-box">
                        <h2>🧒 Requerimento Energético Total</h2>
                        <h1 style="color:#4ECDC4">{resultado:.0f} kcal/dia</h1>
                        <p><strong>Faixa etária:</strong> {faixa}</p>
                        <p><strong>Nível de atividade:</strong> {nivel} (×{fator_atividade:.2f})</p>
                        <p><strong>Detalhes:</strong> {sexo}, {idade_anos:.1f} anos, {peso:.1f} kg, {estatura:.2f} m</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Adicionar ao histórico
                    st.session_state.historico.append({
                        'modulo': modulo,
                        'resultado': f"{resultado:.0f} kcal",
                        'data': datetime.now().strftime("%H:%M")
                    })
    
    # ================================================
    # MÓDULO: ANTROPOMETRIA AVANÇADA
    # ================================================
    elif modulo == "📐 Antropometria Avançada":
        st.markdown('<div class="main-header">📐 Antropometria Avançada</div>', unsafe_allow_html=True)
        
        # Menu de subcálculos
        submodulo = st.selectbox(
            "Selecione o cálculo antropométrico:",
            [
                "📏 Estimativa de Peso (6-18 anos)",
                "📐 Estimativa de Estatura (Tíbia/Ulna)",
                "⚖️ Composição Corporal",
                "🦵 Circunferência Muscular do Braço",
                "🦽 Estimativas para Paralisia Cerebral",
                "🦿 Peso Corrigido para Amputação"
            ]
        )
        
        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
        
        # ESTIMATIVA DE PESO (6-18 anos)
        if "Estimativa de Peso" in submodulo:
            st.subheader("📏 Estimativa de Peso para Crianças/Adolescentes (6-18 anos)")
            
            st.info("""
            **Fórmulas específicas por:**
            - Sexo (Masculino/Feminino)
            - Raça (Branca/Negra)
            - Baseada em: Altura do joelho + Perímetro do braço
            """)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 👤 Dados Pessoais")
                sexo = st.selectbox("Sexo", options=[s.value for s in Sexo])
                raca = st.selectbox("Raça", options=[r.value for r in Raca])
            
            with col2:
                st.markdown("#### 📐 Medidas Antropométricas")
                altura_joelho = st.number_input("Altura do Joelho (cm)", 
                                               min_value=10.0, 
                                               max_value=60.0, 
                                               value=30.0, 
                                               step=0.1)
                perimetro_braco = st.number_input("Perímetro do Braço (cm)", 
                                                 min_value=5.0, 
                                                 max_value=40.0, 
                                                 value=20.0, 
                                                 step=0.1)
            
            if st.button("⚖️ Calcular Peso Estimado", type="primary"):
                sexo_enum = Sexo.MASCULINO if sexo == "Masculino" else Sexo.FEMININO
                raca_enum = Raca.BRANCA if raca == "Branca" else Raca.NEGRA
                resultado = estimar_peso_crianca(altura_joelho, perimetro_braco, sexo_enum, raca_enum)
                
                if resultado:
                    # Determinar fórmula usada
                    if sexo == "Masculino" and raca == "Branca":
                        formula = f"{altura_joelho} × 0.68 + {perimetro_braco} × 2.64 - 50.08"
                    elif sexo == "Masculino" and raca == "Negra":
                        formula = f"{altura_joelho} × 0.59 + {perimetro_braco} × 2.73 - 48.32"
                    elif sexo == "Feminino" and raca == "Branca":
                        formula = f"{altura_joelho} × 0.77 + {perimetro_braco} × 2.47 - 50.16"
                    else:
                        formula = f"{altura_joelho} × 0.71 + {perimetro_braco} × 2.59 - 50.43"
                    
                    st.markdown(f"""
                    <div class="result-box">
                        <h2>⚖️ Peso Estimado</h2>
                        <h1 style="color:#6C5CE7">{resultado:.1f} kg</h1>
                        <p><strong>Fórmula ({sexo}, {raca}):</strong> {formula}</p>
                        <p><strong>Medidas:</strong> Joelho: {altura_joelho} cm, Braço: {perimetro_braco} cm</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Tabela de referência
                    with st.expander("📊 Tabela de Fórmulas"):
                        df = pd.DataFrame({
                            'Sexo': ['Masculino', 'Masculino', 'Feminino', 'Feminino'],
                            'Raça': ['Branca', 'Negra', 'Branca', 'Negra'],
                            'Fórmula': [
                                'AltJoelho × 0.68 + PerBraço × 2.64 - 50.08',
                                'AltJoelho × 0.59 + PerBraço × 2.73 - 48.32',
                                'AltJoelho × 0.77 + PerBraço × 2.47 - 50.16',
                                'AltJoelho × 0.71 + PerBraço × 2.59 - 50.43'
                            ]
                        })
                        st.dataframe(df, use_container_width=True, hide_index=True)
                else:
                    st.error("❌ Erro no cálculo. Verifique os valores inseridos.")
        
        # ESTIMATIVA DE ESTATURA
        elif "Estimativa de Estatura" in submodulo:
            st.subheader("📐 Estimativa de Estatura por Medidas Ósseas")
            
            metodo = st.radio(
                "Método de estimativa:",
                ["🦵 Por Tíbia", "🦴 Por Ulna"],
                horizontal=True
            )
            
            if "Tíbia" in metodo:
                comprimento = st.number_input("Comprimento da Tíbia (cm)", 
                                             min_value=10.0, 
                                             max_value=50.0, 
                                             value=30.0, 
                                             step=0.1)
                
                if st.button("📏 Calcular Estatura", type="primary"):
                    resultado = estimar_estatura_tibia(comprimento)
                    
                    st.markdown(f"""
                    <div class="result-box">
                        <h2>🦵 Estatura Estimada (Tíbia)</h2>
                        <h1 style="color:#00B894">{resultado:.1f} cm</h1>
                        <p><strong>Fórmula:</strong> 3.26 × {comprimento} + 30.8 = {resultado:.1f}</p>
                    </div>
                    """, unsafe_allow_html=True)
            
            else:
                comprimento = st.number_input("Comprimento da Ulna (cm)", 
                                            min_value=10.0, 
                                            max_value=40.0, 
                                            value=25.0, 
                                            step=0.1)
                
                if st.button("📏 Calcular Estatura", type="primary"):
                    resultado = estimar_estatura_ulna(comprimento)
                    
                    st.markdown(f"""
                    <div class="result-box">
                        <h2>🦴 Estatura Estimada (Ulna)</h2>
                        <h1 style="color:#00B894">{resultado:.1f} cm</h1>
                        <p><strong>Fórmula:</strong> 5.45 × {comprimento} + 20.7 = {resultado:.1f}</p>
                    </div>
                    """, unsafe_allow_html=True)
        
        # COMPOSIÇÃO CORPORAL
        elif "Composição Corporal" in submodulo:
            st.subheader("⚖️ Percentual de Gordura Corporal")
            
            col1, col2 = st.columns(2)
            
            with col1:
                soma_dobras = st.number_input("Soma das Dobras Cutâneas (mm)", 
                                             min_value=5.0, 
                                             max_value=100.0, 
                                             value=30.0, 
                                             step=0.1)
                sexo = st.selectbox("Sexo", options=[s.value for s in Sexo])
            
            with col2:
                estagio_tanner = st.selectbox("Estágio de Tanner", 
                                             options=[1, 2, 3, 4, 5],
                                             help="Estágio de maturação sexual")
                raca = st.selectbox("Raça", options=[r.value for r in Raca])
            
            if st.button("📊 Calcular % Gordura", type="primary"):
                sexo_enum = Sexo.MASCULINO if sexo == "Masculino" else Sexo.FEMININO
                raca_enum = Raca.BRANCA if raca == "Branca" else Raca.NEGRA
                resultado = calcular_percentual_gordura(soma_dobras, sexo_enum, estagio_tanner, raca_enum)
                
                if resultado:
                    # Classificação
                    if sexo == "Masculino":
                        if resultado < 8:
                            classificacao = "Muito baixo"
                            cor = "#dc3545"
                        elif resultado < 15:
                            classificacao = "Normal"
                            cor = "#28a745"
                        elif resultado < 20:
                            classificacao = "Moderado"
                            cor = "#fd7e14"
                        else:
                            classificacao = "Alto"
                            cor = "#dc3545"
                    else:
                        if resultado < 15:
                            classificacao = "Muito baixo"
                            cor = "#dc3545"
                        elif resultado < 25:
                            classificacao = "Normal"
                            cor = "#28a745"
                        elif resultado < 30:
                            classificacao = "Moderado"
                            cor = "#fd7e14"
                        else:
                            classificacao = "Alto"
                            cor = "#dc3545"
                    
                    st.markdown(f"""
                    <div class="result-box" style="border-left-color:{cor}">
                        <h2>⚖️ Composição Corporal</h2>
                        <h1 style="color:{cor}">{resultado:.1f}%</h1>
                        <p style="color:{cor}"><strong>Classificação: {classificacao}</strong></p>
                        <p><strong>Dobras cutâneas:</strong> {soma_dobras} mm</p>
                        <p><strong>Estágio Tanner:</strong> {estagio_tanner}</p>
                    </div>
                    """, unsafe_allow_html=True)
        
        # CIRCUNFERÊNCIA MUSCULAR DO BRAÇO
        elif "Circunferência Muscular" in submodulo:
            st.subheader("💪 Circunferência Muscular do Braço (CMB)")
            
            col1, col2 = st.columns(2)
            
            with col1:
                perimetro_braco = st.number_input("Perímetro do Braço (cm)", 
                                                 min_value=5.0, 
                                                 max_value=50.0, 
                                                 value=25.0, 
                                                 step=0.1)
            
            with col2:
                dobra_tricipital = st.number_input("Dobra Tricipital (mm)", 
                                                  min_value=3.0, 
                                                  max_value=40.0, 
                                                  value=15.0, 
                                                  step=0.1)
            
            if st.button("📏 Calcular CMB", type="primary"):
                resultado = calcular_circ_muscular_braco(perimetro_braco, dobra_tricipital)
                
                # Avaliação nutricional
                if resultado < 15:
                    status = "Desnutrição grave"
                    cor = "#dc3545"
                elif resultado < 20:
                    status = "Desnutrição moderada"
                    cor = "#fd7e14"
                elif resultado < 25:
                    status = "Normal"
                    cor = "#28a745"
                else:
                    status = "Adequado"
                    cor = "#17a2b8"
                
                st.markdown(f"""
                <div class="result-box" style="border-left-color:{cor}">
                    <h2>💪 Circunferência Muscular do Braço</h2>
                    <h1 style="color:{cor}">{resultado:.1f} cm</h1>
                    <p style="color:{cor}"><strong>Avaliação: {status}</strong></p>
                    <p><strong>Fórmula:</strong> {perimetro_braco} - (0.314 × ({dobra_tricipital} / 10))</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Calcular AMB e AGB também
                amb = calcular_area_muscular_braco(perimetro_braco, dobra_tricipital)
                agb = calcular_area_gorda_braco(perimetro_braco, amb)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("CMB", f"{resultado:.1f} cm")
                with col2:
                    st.metric("AMB", f"{amb:.1f} cm²")
                with col3:
                    st.metric("AGB", f"{agb:.1f} cm²")
    
    # ================================================
    # MÓDULO: PARALISIA CEREBRAL
    # ================================================
    elif modulo == "🦽 Paralisia Cerebral":
        st.markdown('<div class="main-header">🦽 Cálculos para Paralisia Cerebral</div>', unsafe_allow_html=True)
        
        # Menu de fórmulas PC
        formula_pc = st.selectbox(
            "Selecione a fórmula de Paralisia Cerebral:",
            [
                "🏥 PC Enfermo (×1.1)",
                "👶 PC 5-11 anos (por altura)",
                "🧒 PC Estáveis (condição motora)",
                "📊 PC Geral (Harris-Benedict)",
                "📐 Estimativa de Estatura PC",
                "⚖️ Necessidades Nutricionais PC"
            ]
        )
        
        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
        
        # PC ENFERMO
        if "Enfermo" in formula_pc:
            st.subheader("🏥 Paciente com PC Enfermo (Fator ×1.1)")
            
            col1, col2 = st.columns(2)
            
            with col1:
                peso = st.number_input("Peso (kg)", 
                                      min_value=1.0, 
                                      max_value=100.0, 
                                      value=20.0, 
                                      step=0.1)
                altura_cm = st.number_input("Altura (cm)", 
                                          min_value=30.0, 
                                          max_value=200.0, 
                                          value=120.0, 
                                          step=0.1)
            
            with col2:
                idade = st.number_input("Idade (anos)", 
                                       min_value=0.0, 
                                       max_value=18.0, 
                                       value=8.0, 
                                       step=0.1)
                sexo = st.selectbox("Sexo", options=[s.value for s in Sexo])
            
            if st.button("🦽 Calcular", type="primary"):
                sexo_enum = Sexo.MASCULINO if sexo == "Masculino" else Sexo.FEMININO
                resultado = necessidade_energetica_pc_enfermo(peso, altura_cm, idade, sexo_enum)
                
                # Calcular base
                if sexo == "Masculino":
                    base = 66.5 + (13.75 * peso) + (5.003 * altura_cm) - (6.775 * idade)
                else:
                    base = 65.1 + (9.56 * peso) + (1.85 * altura_cm) - (4.676 * idade)
                
                st.markdown(f"""
                <div class="result-box">
                    <h2>🏥 Necessidade Energética PC Enfermo</h2>
                    <h1 style="color:#FF6B6B">{resultado:.0f} kcal/dia</h1>
                    <p><strong>Cálculo:</strong> {base:.0f} × 1.1 = {resultado:.0f}</p>
                    <p><strong>Fator de estresse:</strong> 1.1</p>
                </div>
                """, unsafe_allow_html=True)
        
        # PC 5-11 ANOS
        elif "5-11" in formula_pc:
            st.subheader("👶 Necessidade Energética PC (5-11 anos)")
            
            altura = st.number_input("Altura (cm)", 
                                    min_value=50.0, 
                                    max_value=200.0, 
                                    value=120.0, 
                                    step=0.1)
            
            nivel = st.selectbox("Nível de Atividade", 
                               options=[n.value for n in NivelAtividadePC])
            
            if st.button("🦽 Calcular", type="primary"):
                resultado = necessidade_energetica_pc_5_11(altura, nivel)
                
                # Determinar fórmula
                if nivel == "leve a moderada":
                    formula = f"13.9 × {altura}"
                elif nivel == "restrita intensa":
                    formula = f"10 × {altura}"
                else:
                    formula = f"11.1 × {altura}"
                
                st.markdown(f"""
                <div class="result-box">
                    <h2>👶 Necessidade PC 5-11 anos</h2>
                    <h1 style="color:#4ECDC4">{resultado:.0f} kcal/dia</h1>
                    <p><strong>Fórmula ({nivel}):</strong> {formula} = {resultado:.0f}</p>
                </div>
                """, unsafe_allow_html=True)
        
        # PC ESTÁVEIS
        elif "Estáveis" in formula_pc:
            st.subheader("🧒 PC Estáveis (por condição motora)")
            
            altura = st.number_input("Altura (cm)", 
                                    min_value=50.0, 
                                    max_value=200.0, 
                                    value=120.0, 
                                    step=0.1)
            
            condicao = st.selectbox("Condição Motora", 
                                  options=[c.value for c in CondicaoMotora])
            
            if st.button("🦽 Calcular", type="primary"):
                resultado = necessidade_energetica_pc_estaveis(altura, condicao)
                
                st.markdown(f"""
                <div class="result-box">
                    <h2>🧒 Necessidade PC Estáveis</h2>
                    <h1 style="color:#00B894">{resultado:.0f} kcal/dia</h1>
                    <p><strong>Condição:</strong> {condicao}</p>
                </div>
                """, unsafe_allow_html=True)
    
    # ================================================
    # MÓDULO: CONDIÇÕES ESPECIAIS
    # ================================================
    elif modulo == "🏥 Condições Especiais":
        st.markdown('<div class="main-header">🏥 Condições Especiais e Pediatria Crítica</div>', unsafe_allow_html=True)
        
        # Menu de condições
        condicao = st.selectbox(
            "Selecione a condição especial:",
            [
                "🧬 Síndrome de Down",
                "🏥 UTI Pediátrica (>2 anos)",
                "👶 Correção de Prematuridade",
                "🔥 Criança Criticamente Enferma",
                "🦿 Peso Corrigido para Amputação"
            ]
        )
        
        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
        
        # SÍNDROME DE DOWN
        if "Down" in condicao:
            st.subheader("🧬 Síndrome de Down")
            
            altura = st.number_input("Altura (cm)", 
                                    min_value=50.0, 
                                    max_value=200.0, 
                                    value=120.0, 
                                    step=0.1)
            
            sexo = st.selectbox("Sexo", options=[s.value for s in Sexo])
            
            if st.button("🧬 Calcular Necessidade", type="primary"):
                sexo_enum = Sexo.MASCULINO if sexo == "Masculino" else Sexo.FEMININO
                resultado = necessidade_sindrome_down(altura, sexo_enum)
                
                # Comparação com crianças típicas
                if sexo == "Masculino":
                    tipico = 16.1 * altura * 1.15
                    formula = f"16.1 × {altura}"
                else:
                    tipico = 14.3 * altura * 1.15
                    formula = f"14.3 × {altura}"
                
                st.markdown(f"""
                <div class="result-box">
                    <h2>🧬 Necessidade Energética - Síndrome de Down</h2>
                    <h1 style="color:#6C5CE7">{resultado:.0f} kcal/dia</h1>
                    <p><strong>Fórmula ({sexo}):</strong> {formula} = {resultado:.0f}</p>
                    <p><strong>Comparação com criança típica:</strong> ~{tipico:.0f} kcal/dia (+15%)</p>
                </div>
                """, unsafe_allow_html=True)
        
        # UTI PEDIÁTRICA
        elif "UTI" in condicao:
            st.subheader("🏥 UTI Pediátrica - Ventilação Mecânica")
            
            st.warning("⚠️ **Atenção:** Fórmula válida apenas para pacientes acima de 2 anos e não queimados.")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                idade_meses = st.number_input("Idade (meses)", 
                                            min_value=24.0, 
                                            max_value=240.0, 
                                            value=48.0, 
                                            step=1.0)
            
            with col2:
                peso = st.number_input("Peso (kg)", 
                                      min_value=1.0, 
                                      max_value=100.0, 
                                      value=15.0, 
                                      step=0.1)
            
            with col3:
                temperatura = st.number_input("Temperatura (°C)", 
                                           min_value=30.0, 
                                           max_value=45.0, 
                                           value=37.0, 
                                           step=0.1)
            
            if st.button("🏥 Calcular GEB UTI", type="primary"):
                try:
                    resultado = geb_uti_ventilacao_mecanica(idade_meses, peso, temperatura)
                    
                    st.markdown(f"""
                    <div class="result-box">
                        <h2>🏥 Gasto Energético Basal (UTI)</h2>
                        <h1 style="color:#FF6B6B">{resultado:.0f} kcal/dia</h1>
                        <p><strong>Fórmula:</strong> [(17 × {idade_meses}) + (48 × {peso}) + (292 × {temperatura}) - 9677] × 0.239</p>
                    </div>
                    """, unsafe_allow_html=True)
                except ValueError as e:
                    st.error(f"❌ {str(e)}")
        
        # CORREÇÃO DE PREMATURIDADE
        elif "Prematuridade" in condicao:
            st.subheader("👶 Correção de Idade para Prematuros")
            
            col1, col2 = st.columns(2)
            
            with col1:
                idade_cron = st.number_input("Idade Cronológica (meses)", 
                                           min_value=0.0, 
                                           max_value=24.0, 
                                           value=6.0, 
                                           step=0.1)
            
            with col2:
                idade_gest = st.number_input("Idade Gestacional (semanas)", 
                                           min_value=20.0, 
                                           max_value=42.0, 
                                           value=32.0, 
                                           step=0.1)
            
            if st.button("👶 Calcular Idade Corrigida", type="primary"):
                resultado = calcular_idade_corrigida(idade_cron, idade_gest)
                
                prematuridade = 40 - idade_gest
                
                st.markdown(f"""
                <div class="result-box">
                    <h2>👶 Idade Corrigida para Prematuro</h2>
                    <h1 style="color:#00B894">{resultado:.1f} meses</h1>
                    <p><strong>Idade cronológica:</strong> {idade_cron:.1f} meses</p>
                    <p><strong>Prematuridade:</strong> {prematuridade:.1f} semanas</p>
                    <p><strong>Fórmula:</strong> {idade_cron:.1f} - (40 - {idade_gest:.1f}) / 4.34524</p>
                </div>
                """, unsafe_allow_html=True)
    
    # ================================================
    # MÓDULO: MONITORAMENTO NUTRICIONAL
    # ================================================
    elif modulo == "📈 Monitoramento Nutricional":
        st.markdown('<div class="main-header">📈 Monitoramento Nutricional</div>', unsafe_allow_html=True)
        
        st.subheader("📊 Percentual Alcançado de Metas Nutricionais")
        
        col1, col2 = st.columns(2)
        
        with col1:
            tipo = st.selectbox(
                "Parâmetro nutricional:",
                ["🔥 Energia (kcal)", "🥩 Proteína (g)", "💧 Líquidos (ml)", "📋 Outro"]
            )
            
            consumido = st.number_input(f"Valor Consumido", 
                                      min_value=0.0, 
                                      max_value=10000.0, 
                                      value=1500.0, 
                                      step=10.0)
        
        with col2:
            necessidade = st.number_input(f"Necessidade/ Meta", 
                                        min_value=0.1, 
                                        max_value=10000.0, 
                                        value=2000.0, 
                                        step=10.0)
            
            st.info("""
            **Interpretação:**
            - ✅ 100%+: Meta alcançada
            - ⚠️ 90-99%: Próximo da meta
            - 🟠 70-89%: Atenção necessária
            - ❌ <70%: Meta não alcançada
            """)
        
        if st.button("📈 Calcular % Alcançado", type="primary", use_container_width=True):
            try:
                percentual = calcular_percentual_alcançado(consumido, necessidade)
                
                # Determinar status e cor
                if percentual >= 100:
                    status = "✅ Meta alcançada ou superada"
                    cor = "#28a745"
                    emoji = "✅"
                elif percentual >= 90:
                    status = "⚠️ Próximo da meta (90-99%)"
                    cor = "#ffc107"
                    emoji = "⚠️"
                elif percentual >= 70:
                    status = "🟠 Atenção necessária (70-89%)"
                    cor = "#fd7e14"
                    emoji = "🟠"
                else:
                    status = "❌ Meta não alcançada (<70%)"
                    cor = "#dc3545"
                    emoji = "❌"
                
                # Exibir resultado
                st.markdown(f"""
                <div class="result-box" style="border-left-color:{cor}">
                    <h2>{emoji} Percentual Alcançado</h2>
                    <h1 style="color:{cor}">{percentual:.1f}%</h1>
                    <p style="color:{cor}"><strong>{status}</strong></p>
                    <p><strong>Consumido:</strong> {consumido:.1f}</p>
                    <p><strong>Necessidade:</strong> {necessidade:.1f}</p>
                    <p><strong>Déficit/Superávit:</strong> {consumido - necessidade:+.1f}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Barra de progresso
                progresso = min(percentual / 100, 1.0)
                st.progress(float(progresso))
                
                # Gráfico simples
                col1, col2 = st.columns([3, 1])
                with col1:
                    data = pd.DataFrame({
                        'Categoria': ['Consumido', 'Restante'],
                        'Valor': [consumido, max(0, necessidade - consumido)]
                    })
                    
                    # Mostrar apenas se houver dados
                    if necessidade > 0:
                        st.markdown("### 📊 Visualização")
                        st.bar_chart(data.set_index('Categoria'))
                
                with col2:
                    st.metric("Alcançado", f"{percentual:.1f}%")
                    st.metric("Meta", f"{necessidade:.0f}")
                    
            except ValueError as e:
                st.error(f"❌ {str(e)}")
    
    # ================================================
    # MÓDULO: CÁLCULOS GERAIS
    # ================================================
    elif modulo == "⚖️ Cálculos Gerais":
        st.markdown('<div class="main-header">⚖️ Cálculos Nutricionais Gerais</div>', unsafe_allow_html=True)
        
        # Menu de cálculos
        calculo = st.selectbox(
            "Selecione o cálculo:",
            [
                "⚖️ Peso Ajustado (obesidade/desnutrição)",
                "📉 Perda de Peso (%)",
                "⚡ TMB Padrão (não Schofield)",
                "🔥 Gasto Energético Total (GET)",
                "📐 Estimativas de Estatura PC"
            ]
        )
        
        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
        
        # PESO AJUSTADO
        if "Peso Ajustado" in calculo:
            st.subheader("⚖️ Peso Ajustado para Obesidade/Desnutrição")
            
            col1, col2 = st.columns(2)
            
            with col1:
                peso_atual = st.number_input("Peso Atual (kg)", 
                                            min_value=0.1, 
                                            max_value=300.0, 
                                            value=70.0)
                peso_ideal = st.number_input("Peso Ideal (kg)", 
                                           min_value=0.1, 
                                           max_value=300.0, 
                                           value=65.0)
            
            with col2:
                condicao = st.selectbox(
                    "Condição:",
                    [Condicao.OBESIDADE.value, Condicao.DESNUTRICAO.value],
                    format_func=lambda x: "⚖️ Obesidade" if x == "obesidade" else "📉 Desnutrição"
                )
            
            if st.button("⚖️ Calcular Peso Ajustado", type="primary"):
                resultado = calcular_peso_ajustado(peso_atual, peso_ideal, Condicao(condicao))
                
                if resultado:
                    if condicao == "obesidade":
                        formula = f"({peso_atual} - {peso_ideal}) × 0.25 + {peso_ideal}"
                        cor = "#FF6B6B"
                    else:
                        formula = f"({peso_atual} - {peso_ideal}) × 0.25 + {peso_atual}"
                        cor = "#4ECDC4"
                    
                    st.markdown(f"""
                    <div class="result-box" style="border-left-color:{cor}">
                        <h2>⚖️ Peso Ajustado</h2>
                        <h1 style="color:{cor}">{resultado:.1f} kg</h1>
                        <p><strong>Fórmula:</strong> {formula}</p>
                        <p><strong>Peso atual:</strong> {peso_atual:.1f} kg</p>
                        <p><strong>Peso ideal:</strong> {peso_ideal:.1f} kg</p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.error("❌ Erro no cálculo. Verifique os valores.")
        
        # PERDA DE PESO
        elif "Perda de Peso" in calculo:
            st.subheader("📉 Percentual de Perda de Peso")
            
            col1, col2 = st.columns(2)
            
            with col1:
                peso_usual = st.number_input("Peso Usual (kg)", 
                                           min_value=0.1, 
                                           max_value=300.0, 
                                           value=70.0)
            
            with col2:
                peso_atual = st.number_input("Peso Atual (kg)", 
                                           min_value=0.1, 
                                           max_value=300.0, 
                                           value=65.0)
            
            if st.button("📉 Calcular Perda de Peso", type="primary"):
                resultado = calcular_perda_peso(peso_usual, peso_atual)
                
                if resultado is not None:
                    # Classificação
                    if resultado < 5:
                        classificacao = "Perda insignificante"
                        cor = "#28a745"
                        emoji = "✅"
                    elif resultado < 10:
                        classificacao = "Perda moderada"
                        cor = "#fd7e14"
                        emoji = "⚠️"
                    else:
                        classificacao = "Perda grave"
                        cor = "#dc3545"
                        emoji = "❌"
                    
                    perda_absoluta = peso_usual - peso_atual
                    
                    st.markdown(f"""
                    <div class="result-box" style="border-left-color:{cor}">
                        <h2>{emoji} Perda de Peso</h2>
                        <h1 style="color:{cor}">{resultado:.1f}%</h1>
                        <p style="color:{cor}"><strong>{classificacao}</strong></p>
                        <p><strong>Peso usual:</strong> {peso_usual:.1f} kg</p>
                        <p><strong>Peso atual:</strong> {peso_atual:.1f} kg</p>
                        <p><strong>Perda absoluta:</strong> {perda_absoluta:.1f} kg</p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.error("❌ Erro no cálculo.")
        
        # TMB PADRÃO
        elif "TMB Padrão" in calculo:
            st.subheader("⚡ Taxa Metabólica Basal (Padrão)")
            
            col1, col2 = st.columns(2)
            
            with col1:
                peso = st.number_input("Peso (kg)", 
                                      min_value=0.1, 
                                      max_value=300.0, 
                                      value=70.0, 
                                      step=0.1)
                idade = st.number_input("Idade (anos)", 
                                      min_value=0.0, 
                                      max_value=120.0, 
                                      value=30.0, 
                                      step=0.1)
            
            with col2:
                sexo = st.selectbox("Sexo", options=[s.value for s in Sexo])
            
            if st.button("⚡ Calcular TMB Padrão", type="primary"):
                sexo_enum = Sexo.MASCULINO if sexo == "Masculino" else Sexo.FEMININO
                resultado = calcular_tmb_padrao(peso, idade, sexo_enum)
                
                if resultado is None:
                    st.error("❌ Idade fora da faixa suportada (0-18 anos)")
                else:
                    st.markdown(f"""
                    <div class="result-box">
                        <h2>⚡ Taxa Metabólica Basal</h2>
                        <h1 style="color:#6C5CE7">{resultado:.0f} kcal/dia</h1>
                        <p><strong>Detalhes:</strong> {sexo}, {idade:.1f} anos, {peso:.1f} kg</p>
                    </div>
                    """, unsafe_allow_html=True)
        
        # GASTO ENERGÉTICO TOTAL
        elif "GET" in calculo:
            st.subheader("🔥 Gasto Energético Total (GET)")
            
            ere = st.number_input("Taxa Metabólica Basal (kcal)", 
                                min_value=500.0, 
                                max_value=5000.0, 
                                value=1500.0, 
                                step=10.0)
            
            col1, col2 = st.columns(2)
            
            with col1:
                fator_atividade = st.number_input("Fator de Atividade Física", 
                                                min_value=1.0, 
                                                max_value=2.5, 
                                                value=1.2, 
                                                step=0.1,
                                                help="Ex: 1.2 para sedentário, 1.5 para ativo")
            
            with col2:
                fator_estresse = st.number_input("Fator de Estresse", 
                                               min_value=1.0, 
                                               max_value=2.5, 
                                               value=1.0, 
                                               step=0.1,
                                               help="Ex: 1.1 para leve, 1.3 para moderado")
            
            if st.button("🔥 Calcular GET", type="primary"):
                try:
                    if fator_atividade > 1.0 and fator_estresse > 1.0:
                        st.warning("⚠️ Use apenas um fator adicional (atividade OU estresse)")
                    else:
                        resultado = calcular_gasto_energetico_total(
                            ere, 
                            fator_atividade if fator_atividade > 1.0 else None,
                            fator_estresse if fator_estresse > 1.0 else None
                        )
                        
                        if fator_atividade > 1.0:
                            tipo = f"Atividade Física (×{fator_atividade})"
                            cor = "#4ECDC4"
                        elif fator_estresse > 1.0:
                            tipo = f"Estresse (×{fator_estresse})"
                            cor = "#FF6B6B"
                        else:
                            tipo = "Basal (sem fatores)"
                            cor = "#6C5CE7"
                        
                        st.markdown(f"""
                        <div class="result-box" style="border-left-color:{cor}">
                            <h2>🔥 Gasto Energético Total</h2>
                            <h1 style="color:{cor}">{resultado:.0f} kcal/dia</h1>
                            <p><strong>Fator aplicado:</strong> {tipo}</p>
                            <p><strong>ERE base:</strong> {ere:.0f} kcal</p>
                        </div>
                        """, unsafe_allow_html=True)
                except ValueError as e:
                    st.error(f"❌ {str(e)}")
    
    # ================================================
    # RODAPÉ
    # ================================================
    st.markdown("---")
    
    # Exibir histórico
    if st.session_state.historico:
        with st.expander("📝 Histórico de Cálculos (últimos 5)"):
            for item in reversed(st.session_state.historico[-5:]):
                st.write(f"**{item['modulo']}**: {item['resultado']} - {item['data']}")
    
    # Informações do sistema
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.caption("🍏 **Calculadora Nutricional Completa**")
    
    with col2:
        st.caption("📊 **30 fórmulas implementadas**")
    
    with col3:
        st.caption("© 2024 - Desenvolvido para profissionais de saúde")

if __name__ == "__main__":
    main()
