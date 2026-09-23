# ==== CONFIGURAÇÃO DO CONTROLADOR =======

VALOR_INICIAL = 10

SEQUENCIA_1 = [
    ("C1", ["P1", "P2", "P3", "P2", "P3", "P2", "P1"])
]

SEQUENCIA_2 = [
    ("C1", ["P1", "P2", "P3", "P2", "P1", "P3"]),
    ("C2", ["P3", "P2", "P3", "P2", "P3"])
]

SEQUENCIA_3 = [
    ("C1", ["P1", "P2", "P3", "P2", "P1"]),
    ("C2", ["P2", "P3", "P1", "P2", "P3"]),
    ("C3", ["P3", "P1", "P3", "P2"])
]

EXPERIMENTOS = [
    SEQUENCIA_1,
    SEQUENCIA_2,
    SEQUENCIA_3
]


# ==== CONFIGURAÇÃO DOS PROCESSOS =======

"""
Formatação:
 "PX": {
	"operador": + - * ou /
	"constante": int n,
	"porta": 
 }
"""

PROCESSOS = {
    "P1": {
        "operador": "-",
        "constante": 1,
        "porta": 5001
    },

    "P2": {
        "operador": "*",
        "constante": 2,
        "porta": 5002
    },

    "P3": {
        "operador": "+",
        "constante": 3,
        "porta": 5003
    }
}

# ==== CONFIGURAÇÃO DA REDE =======

HOST = "127.0.0.1"


# ==== CONFIGURAÇÃO DOS LOGS =======

END_LOG = "events.txt"
LOG_ORDENADO = "events_ordered.txt"

# ===============================

# ==== CONFIGURAÇÕES DO GRÁFICO =======


FORMAS_EVENTOS = {
    "RECEIVE": "o",
    "EXEC": "s",
    "SEND": "^"
}

CORES_CHAINS = {
    "C1": "#3498db",
    "C2": "#e67e22",
    "C3": "#2ecc71"
}

TAMANHO_FIGURA = (16, 7)

# ===============================