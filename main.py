import json
import time
import socket

from config import VALOR_INICIAL, EXPERIMENTOS, PROCESSOS, HOST
from multiprocessing import Process, Queue, Lock
from process import Process as DistributedProcess

def rodaProcesso(process_id, completion_queue, log_lock):
    
    """
    Inicializa cada processo.
    """

    process = DistributedProcess(process_id, completion_queue, log_lock)

    process.start()

def enviaReset(process_id):
    
    """
    Envia uma mensagem RESET para um processo distribuído.
    """

    config = PROCESSOS[process_id]

    message = {
        "type": "RESET",
        "sender": "MAIN",
        "receiver": process_id
    }

    host = HOST
    port = config["porta"]

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:

        sock.connect((host, port))

        sock.sendall(json.dumps(message).encode("utf-8"))


def resetaProcessos(completion_queue):
    
    """
    Reseta o relógio de todos os processos e espera até que todos confirmem o reset.
    """

    processos = set(PROCESSOS.keys())

    # Envia RESET para todos
    for process_id in processos:
        enviaReset(process_id)

    # Espera confirmação de todos
    processos_resetados = set()

    while processos_resetados != processos:

        message = completion_queue.get()

        if message.get("type") != "RESET_DONE":
            continue

        process_id = message.get("process")

        processos_resetados.add(process_id)

    #print("Todos os processos foram resetados.")


def enviaMensagemInicial(experiment_id, chain_id, path, value):
    
    """
    Inicia uma sequencia de um experimento, enviando o valor inicial para o primeiro processo
    """

    config = PROCESSOS[path[0]]

    message = {
        "type": "MESSAGE",
        "experiment": experiment_id,
        "chain": chain_id,
        "sender": "MAIN",
        "receiver": path[0],
        "timestamp": 0,
        "value": value,
        "path": path,
        "position": 0
    }

    host = HOST
    port = config["porta"]

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:

        sock.connect((host, port))
        sock.sendall(json.dumps(message).encode("utf-8"))


def iniciaExperimento(experiment_id, sequencias, completion_queue):
    
    """
    Inicia todas as sequencias de um experimento e espera até que todas tenham terminado.
    """

    resetaProcessos(completion_queue)

    chains = {
        chain_id
        for chain_id, path in sequencias
    }

    #print(f"\nIniciando experimento {experiment_id} com {len(chains)} chain(s)")

    # Inicia todas as chains
    for chain_id, path in sequencias:
        enviaMensagemInicial(experiment_id, chain_id, path, VALOR_INICIAL)

    # Guarda as chains que já terminaram
    chains_concluidas = set()

    # Espera até todas terminarem
    while chains_concluidas != chains:

        completion = completion_queue.get()

        # Ignora notificações de outro experimento
        if completion["experiment"] != experiment_id:
            continue

        chain_id = completion["chain"]

        chains_concluidas.add(chain_id)

        #print(f"Experimento {experiment_id}: {chain_id} concluída ({len(chains_concluidas)}/{len(chains)})")


def exibeEventosOrdenados():
    
    """
    Ordena os eventos de cada experimento separadamente, primeiro pelo relógio de Lamport e depois pelo ID do processo.

    Linhas que não correspondem a eventos válidos são ignoradas.

    O resultado é gravado em events_ordered.txt.
    """

    experimentos = {}
    experimento_atual = None

    with open("events.txt", "r") as file:

        for linha in file:
            linha = linha.strip()

            if not linha:
                continue

            # Identifica o início de um experimento
            if linha.startswith("INICIO EXPERIMENTO"):

                try:
                    experiment_id = int(linha.split()[-1])
                except ValueError:
                    continue

                experimentos[experiment_id] = []
                experimento_atual = experiment_id

                continue

            # Identifica o fim de um experimento
            if linha.startswith("FIM EXPERIMENTO"):
                experimento_atual = None
                continue

            # Ignora linhas de separação / controle
            if linha.startswith("="):
                continue

            # Ignora eventos fora de experimentos
            if experimento_atual is None:
                continue

            # Confere se a formatação da linha é válida
            if not linha.startswith("[Processo "):
                continue

            # Identifica o processo responsável pelo evento
            processo_inicio = (linha.find("[Processo ") + len("[Processo "))

            processo_fim = linha.find("]", processo_inicio)

            if processo_fim == -1:
                continue

            processo = linha[processo_inicio:processo_fim]

            # Extrai o relógio associado ao evento
            relogio_inicio = linha.find("Relogio Logico: ")

            if relogio_inicio == -1:
                continue

            relogio_inicio += len("Relogio Logico: ")

            relogio_fim = linha.find(" | ", relogio_inicio)

            if relogio_fim == -1:
                continue

            try:
                relogio = int(linha[relogio_inicio:relogio_fim])

            except ValueError:
                continue

            # Guarda o evento na lista
            experimentos[experimento_atual].append((relogio, processo, linha))

    # Escreve os eventos da lista em um arquivo
    with open("events_ordered.txt", "w") as file:

        for experiment_id in sorted(experimentos):

            eventos = experimentos[experiment_id]

            # Ordenar por relógio lógico e desempata usando o id do processo
            eventos.sort(key=lambda evento: (evento[0], evento[1]))

            file.write("\n")
            file.write("=" * 70 + "\n")
            file.write(f"EXPERIMENTO {experiment_id} - EVENTOS ORDENADOS\n")
            file.write("=" * 70 + "\n")

            for relogio, processo, linha in eventos:
                file.write(linha + "\n")

def registraMarcador(texto):
    
    """
    Printa uma linha de controle no log de eventos
    """

    with open("events.txt", "a") as file:
        file.write("\n")
        file.write("=" * 70 + "\n")
        file.write(f"{texto}\n")
        file.write("=" * 70 + "\n")


if __name__ == "__main__":

    # Limpando o log de eventos
    with open("events.txt", "w"):
        pass

    # Queue usada pelos processos distribuídos para avisar a main que uma sequencia terminou
    completion_queue = Queue()

    # Trava usada para controlar acesso ao log de eventos
    log_lock = Lock()

    processes = [
        Process(target=rodaProcesso, args=("P1", completion_queue, log_lock)),
        Process(target=rodaProcesso, args=("P2", completion_queue, log_lock)),
        Process(target=rodaProcesso, args=("P3", completion_queue, log_lock))
    ]

    for process in processes:
        process.start()

    time.sleep(1)

    # ==========================================
    # EXPERIMENTOS
    # ==========================================


    for experiment_id, sequencias in enumerate(EXPERIMENTOS, start=1):

        registraMarcador(f"INICIO EXPERIMENTO {experiment_id}")

        iniciaExperimento(
            experiment_id=experiment_id,
            sequencias=sequencias,
            completion_queue=completion_queue
        )

        registraMarcador(f"FIM EXPERIMENTO {experiment_id}")

    # ==========================================
    # FINALIZAÇÃO
    # ==========================================

    exibeEventosOrdenados()

    for process in processes:
        process.terminate()

    for process in processes:
        process.join()
