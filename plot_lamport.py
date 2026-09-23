import re
import matplotlib.pyplot as plt

from config import EXPERIMENTOS, VALOR_INICIAL

# ==== CONFIGURAÇÕES DO GRÁFICO =======

ARQUIVO_LOG = "events_ordered.txt"

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

def leLog():

    """
    Lê o arquivo de eventos ordenados e separa os eventos por experimento.
    """

    experiments = {}
    current_experiment = None

    with open(ARQUIVO_LOG, "r", encoding="utf-8") as file:

        for line in file:

            line = line.strip()

            if not line:
                continue

            # Identifica o início de um experimento
            experiment_match = re.match(r"EXPERIMENTO (\d+) - EVENTOS ORDENADOS", line)

            if experiment_match:

                experiment_id = int(experiment_match.group(1))

                experiments[experiment_id] = []
                current_experiment = experiment_id

                continue

            # Ignora eventos fora de um experimento
            if current_experiment is None:
                continue

            # Ignora linhas que não são eventos
            if not line.startswith("[Processo "):
                continue

            event = interpretaLinha(line)

            if event is None:
                continue

            event["experimento"] = current_experiment

            experiments[current_experiment].append(event)

    return experiments


def interpretaLinha(line):

    """
    Interpreta uma linha do log e retorna os dados do evento.
    """

    pattern = (
        r"\[Processo (P\d+)\] "
        r"Evento: (\w+) \| "
        r"Relogio Logico: (\d+) \| "
        r"Detalhes: (.*)"
    )

    match = re.match(pattern, line)

    if match is None:
        return None

    process = match.group(1)
    event_type = match.group(2)
    clock = int(match.group(3))
    details = match.group(4)

    event = {
        "processo": process,
        "evento": event_type,
        "relogio": clock,
        "detalhes": details
    }

    # Extrai a origem da mensagem
    origin = re.search(r"Origem = (\w+)", details)
    if origin:
        event["origem"] = origin.group(1)

    # Extrai o destino da mensagem
    destination = re.search(r"Destino = (\w+)", details)
    if destination:
        event["destino"] = destination.group(1)

    # Extrai o valor da mensagem
    value = re.search(r"Valor = (-?\d+)", details)
    if value:
        event["valor"] = int(value.group(1))

    # Extrai o resultado da execução
    result = re.search(r"Resultado = (-?\d+)", details)
    if result:
        event["resultado"] = int(result.group(1))

    # Extrai a chain
    chain = re.search(r"Cadeia: (\w+)", details)
    if chain:
        event["chain"] = chain.group(1)

    return event


def encontraCadeias(experiment_id):

    """
    Retorna as chains configuradas para um experimento.
    """

    experiment_index = experiment_id - 1

    if experiment_index < 0 or experiment_index >= len(EXPERIMENTOS):
        return {}

    chains = {}

    for chain_id, path in EXPERIMENTOS[experiment_index]:
        chains[chain_id] = path

    return chains


def encontraProcessos(events):

    """
    Encontra os processos presentes nos eventos.
    """

    processes = []

    for event in events:
        process = event["processo"]

        if process not in processes:
            processes.append(process)

    return processes


def encontraMensagens(events):

    """
    Encontra os pares SEND -> RECEIVE presentes no log.
    """

    messages = []
    sends = []

    for event in events:

        if event["evento"] == "SEND":
            sends.append(event)
            continue

        if event["evento"] != "RECEIVE":
            continue

        origin = event.get("origem")
        destination = event["processo"]
        value = event.get("valor")

        for send in sends:
            if (send["processo"] == origin and send.get("destino") == destination and send.get("valor") == value):
                
                messages.append({
                    "origem": send["processo"],
                    "destino": destination,
                    "relogio_origem": send["relogio"],
                    "relogio_destino": event["relogio"],
                    "chain": send["chain"],
                    "valor": value
                })

                sends.remove(send)
                break

    return messages


def desenhaLinhasProcessos(ax, events, processes):

    """
    Desenha as linhas horizontais dos processos.
    """

    max_clock = max(event["relogio"] for event in events)

    for process_index, process in enumerate(processes):
        ax.plot(
            [0, max_clock],
            [process_index, process_index],
            color="#d5d8dc",
            linewidth=2,
            zorder=1
        )


def desenhaEventos(ax, events, processes):

    """
    Desenha os eventos relevantes dos processos. RESET e END são tratados como anotações.
    """

    for event in events:
        process = event["processo"]
        event_type = event["evento"]

        # RESET e END não são desenhados como eventos normais

        if event_type in ["RESET", "END"]:
            continue

        clock = event["relogio"]
        process_index = processes.index(process)

        color = CORES_CHAINS.get(event.get("chain"), "#34495e")
        marker = FORMAS_EVENTOS.get(event_type, "o")

        # Desenha o evento

        ax.scatter(
            clock,
            process_index,
            s=180,
            color=color,
            marker=marker,
            edgecolor="white",
            linewidth=1.5,
            zorder=3
        )

        # Mostra o valor do relógio

        ax.text(
            clock,
            process_index + 0.16,
            str(clock),
            ha="center",
            va="bottom",
            fontsize=9,
            fontweight="bold",
            zorder=4
        )

        # Mostra o tipo do evento

        ax.text(
            clock,
            process_index - 0.16,
            event_type,
            ha="center",
            va="top",
            fontsize=7,
            color="#2c3e50",
            zorder=4
        )


def desenhaAnotacoes(ax, events, processes):

    """
    Desenha as anotações de RESET e END dos processos.
    """

    for event in events:
        process = event["processo"]
        event_type = event["evento"]
        clock = event["relogio"]
        process_index = processes.index(process)

        
        if event_type == "RESET":
                        
            ax.annotate(
                "RESET",
                xy=(clock, process_index),
                xytext=(clock + 0.2, process_index + 0.35),
                fontsize=8,
                color="#7f8c8d",
                fontweight="bold",
                ha="left",
                va="bottom",
                arrowprops={
                    "arrowstyle": "->",
                    "color": "#7f8c8d",
                    "linewidth": 1
                },
                zorder=4
            )

        if event_type == "END":

            ax.annotate(
                "END",
                xy=(clock, process_index),
                xytext=(clock + 0.2, process_index - 0.35),
                fontsize=8,
                color="#e74c3c",
                fontweight="bold",
                ha="left",
                va="top",
                arrowprops={
                    "arrowstyle": "->",
                    "color": "#e74c3c",
                    "linewidth": 1
                },
                zorder=4
            )

def desenhaMensagens(ax, messages, processes):

    """
    Desenha as mensagens entre os processos.
    """

    for message in messages:
        origin = message["origem"]
        destination = message["destino"]
        origin_clock = message["relogio_origem"]
        destination_clock = message["relogio_destino"]
        value = message["valor"]
        chain = message["chain"]

        origin_y = processes.index(origin)
        destination_y = processes.index(destination)

        color = CORES_CHAINS.get(chain, "#34495e")

        ax.annotate(
            "",
            xy=(destination_clock, destination_y),
            xytext=(origin_clock, origin_y),
            arrowprops={
                "arrowstyle": "->",
                "color": "#34495e",
                "linewidth": 1.5,
                "connectionstyle": "arc3,rad=0.05"
            },
            zorder=2
        )

        middle_x = (origin_clock + destination_clock) / 2
        middle_y = (origin_y + destination_y) / 2

        ax.text(
            middle_x,
            middle_y + 0.10,
            f"valor = {value}",
            ha="center",
            va="center",
            fontsize=8,
            color=color,
            bbox={
                "boxstyle": "round,pad=0.2",
                "facecolor": "white",
                "edgecolor": "none",
                "alpha": 0.9
            },
            zorder=5
        )

def desenhaValores(ax, events, processes, chains):

    """
    Desenha os valores inicial e final de cada chain.
    """

    for chain_id, path in chains.items():

        if not path:
            continue

        color = CORES_CHAINS.get(chain_id, "#34495e")

        # ==== VALOR INICIAL =======

        first_process = path[0]
        first_process_index = processes.index(first_process)

        first_event = None

        for event in events:
            if (event["processo"] == first_process and event.get("chain") == chain_id):
                if (first_event is None or event["relogio"] < first_event["relogio"]):
                    first_event = event

        if first_event is not None:

            first_clock = first_event["relogio"]

            ax.annotate(
                f"valor inicial = {VALOR_INICIAL}",
                xy=(first_clock, first_process_index),
                xytext=(
                    first_clock - 0.2,
                    first_process_index + 0.45
                ),
                ha="right",
                va="bottom",
                fontsize=8,
                color=color,
                fontweight="bold",
                arrowprops={
                    "arrowstyle": "->",
                    "color": color,
                    "linewidth": 1
                },
                bbox={
                    "boxstyle": "round,pad=0.25",
                    "facecolor": "white",
                    "edgecolor": color,
                    "alpha": 0.9
                },
                zorder=5
            )

        # ==== VALOR FINAL =======

        chain_events = [
            event
            for event in events
            if event.get("chain") == chain_id
        ]

        exec_events = [
            event
            for event in chain_events
            if event["evento"] == "EXEC"
        ]

        if not exec_events:
            continue

        final_event = max(
            exec_events,
            key=lambda event: event["relogio"]
        )

        final_process = final_event["processo"]
        final_process_index = processes.index(
            final_process
        )

        final_clock = final_event["relogio"]
        final_value = final_event.get("resultado")

        ax.annotate(
            f"valor final = {final_value}",
            xy=(final_clock, final_process_index),
            xytext=(
                final_clock + 0.2,
                final_process_index - 0.45
            ),
            ha="left",
            va="top",
            fontsize=8,
            color=color,
            fontweight="bold",
            arrowprops={
                "arrowstyle": "->",
                "color": color,
                "linewidth": 1
            },
            bbox={
                "boxstyle": "round,pad=0.25",
                "facecolor": "white",
                "edgecolor": color,
                "alpha": 0.9
            },
            zorder=5
        )

def configuraGrafico(ax, events, processes, experiment_id, chains):

    """
    Configura os eixos e a aparência do gráfico.
    """

    max_clock = max(event["relogio"] for event in events)

    ax.set_xlim(-0.5, max_clock + 0.8)
    ax.set_ylim(-0.7, len(processes) - 0.3)
    ax.set_xticks(range(max_clock + 1))
    ax.set_yticks(range(len(processes)))
    ax.set_yticklabels(processes, fontsize=11, fontweight="bold")

    ax.set_xlabel("Relógio de Lamport", fontsize=11)
    ax.set_ylabel("Processo", fontsize=11)

    chain_text = " | ".join(
        f"{chain_id}: {' → '.join(path)}"
        for chain_id, path in chains.items()
    )

    ax.set_title(
        f"Evolução dos Relógios de Lamport - Experimento {experiment_id}\n"
        f"{chain_text}",
        fontsize=13,
        fontweight="bold"
    )

    ax.grid(axis="x", linestyle="--", alpha=0.25)
    ax.grid(axis="y", linestyle="-", alpha=0.12)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    for cadeia, color in CORES_CHAINS.items():
        ax.scatter(
            [],
            [],
            s=100,
            color=color,
            label=cadeia
        )

    ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, -0.08),
        ncol=len(CORES_CHAINS),
        frameon=False
    )


def geraGraficoLamport():

    """
    Lê os eventos, identifica os experimentos e gera um gráfico para cada experimento.
    """

    experiments = leLog()

    if not experiments:
        print("Nenhum evento encontrado.")
        return

    for experiment_id, events in experiments.items():

        chains = encontraCadeias(experiment_id)

        if not chains:
            print(f"Experimento {experiment_id} não encontrado na configuração.")
            continue

        processes = encontraProcessos(events)
        messages = encontraMensagens(events)

        figure, ax = plt.subplots(figsize=TAMANHO_FIGURA)

        desenhaLinhasProcessos(ax, events, processes)
        desenhaMensagens(ax, messages, processes)
        desenhaEventos(ax, events, processes)
        #desenhaAnotacoes(ax, events, processes)
        desenhaValores(ax, events, processes, chains)

        configuraGrafico(
            ax,
            events,
            processes,
            experiment_id,
            chains
        )

        plt.tight_layout()
        plt.show()


# ==== EXECUÇÃO =======

if __name__ == "__main__":
    geraGraficoLamport()
