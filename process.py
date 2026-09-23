import json
import socket

from config import PROCESSOS, END_LOG, HOST

class Process:

    def __init__(self, process_id, completion_queue, log_lock):

        if process_id not in PROCESSOS:
            raise ValueError(f"Processo desconhecido: {process_id}")

        config = PROCESSOS[process_id]

        self.process_id = process_id
        self.operation = config["operador"]
        self.constant = config["constante"]
        self.port = config["porta"]

        self.completion_queue = completion_queue
        self.log_lock = log_lock

        self.running = True

        # Relógio de Lamport
        self.clock = 0

    def incrementaRelogio(self):
        self.clock += 1

    def registraEvento(self, type, details="", chain=""):

        """
        Registra um evento do tipo type com a descrição details no log de eventos
        """

        try:
            with self.log_lock:
                with open(END_LOG, "a", encoding="utf-8") as file:

                    chain_details = ""

                    if type != "RESET" and chain:
                        chain_details = f" | Cadeia: {chain}"

                    file.write(
                        f"[Processo {self.process_id}] "
                        f"Evento: {type} | "
                        f"Relogio Logico: {self.clock} | "
                        f"Detalhes: {details}"
                        f"{chain_details}\n"
                    )

        except Exception as e:
            print(f"Erro ao registrar evento: {e}")


    def processa(self, connection):
        
        """
        Comportamento padrão de um processo: recebe mensagem -> efetua operação -> envia mensagem
        """

        with connection:

            try:
                data = connection.recv(4096)

            except ConnectionResetError:
                return

            if not data:
                return

            message = json.loads(data.decode("utf-8"))

            # ==========================================
            # 0. MENSAGEM DE CONTROLE ENTRE EXPERIMENTOS
            # ==========================================

            if message.get("type") == "RESET":

                self.clock = 0

                self.registraEvento("RESET", "Relogio resetado para 0")

                self.completion_queue.put({"type": "RESET_DONE", "process": self.process_id })

                return

            # ==========================================
            # 1. RECEBE A MENSAGEM
            # ==========================================

            value, cadeia, caminho, posicao, experimento = self.recebeMensagem(message)

            # ==========================================
            # 2. REALIZA SUA OPERAÇÃO
            # ==========================================

            result = self.eventoInterno(value, cadeia)

            # ==========================================
            # 3. VERIFICA A POSIÇÃO NA SEQUÊNCIA
            # ==========================================

            # Ainda existem processos na chain
            if posicao < len(caminho) - 1:

                proximo = caminho[posicao + 1]

                self.enviaMensagem(
                    destination = proximo,
                    value = result,
                    experiment = experimento,
                    chain = cadeia,
                    path = caminho,
                    position = posicao + 1
                )

            # ==========================================
            # 4. FIM DA SEQUÊNCIA
            # ==========================================

            else:
                self.encerraCadeia(message)

    def encerraCadeia(self, message):
        
        """
        Função que sinaliza ao controlador (main.py) que uma sequência foi finalizada
        """

        completion = {"type": "CHAIN_DONE",
            "experiment": message.get("experiment"),
            "chain": message.get("chain")}

        self.completion_queue.put(completion)

        details = "Experimento = " + str(message.get("experiment")) + " Cadeia = " + message.get("chain")

        self.registraEvento("END", details, message.get("chain"))

    def operacao(self, value=None):
        
        """
        Lógica que aplica a operação de um processo sobre o valor recebido
        """
        
        if value is None:
            value = self.constant

        if self.operation == "-":
            return value - self.constant

        elif self.operation == "+":
            return value + self.constant

        elif self.operation == "*":
            return value * self.constant

        elif self.operation == "/":
            return value / self.constant

        raise ValueError(f"Operação desconhecida: {self.operation}")

    def eventoInterno(self, value=None, chain=""):
        
        """
        Função de processamento interno (EXEC)
        """
        
        self.incrementaRelogio()

        result = self.operacao(value)

        details = "Valor = " + str(value) + " Resultado = " + str(result)

        self.registraEvento("EXEC", details, chain)

        return result

    def enviaMensagem(self, destination, value=None, experiment=None, chain=None, path=None, position=None):
        
        """
        Função de envio de mensagem entre processos (SEND)
        """
        
        self.incrementaRelogio()

        message = {
            "type": "MESSAGE",

            "experiment": experiment,
            "chain": chain,

            "sender": self.process_id,
            "receiver": destination,

            "timestamp": self.clock,

            "value": value,

            "path": path,
            "position": position
        }

        port = PROCESSOS[destination]["porta"]

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:

            sock.connect((HOST, port))

            sock.sendall(json.dumps(message).encode("utf-8"))

        details = "Destino = " + destination + " Valor = " + str(value)

        self.registraEvento("SEND", details, chain)

    def recebeMensagem(self, message):
        
        """
        Função de recebimento de mensagem entre processos (RECEIVE)
        """
        
        timestamp = message.get("timestamp")

        self.clock = max(self.clock, timestamp) + 1

        value = message.get("value")
        chain = message.get("chain")
        path = message.get("path")
        position = message.get("position")
        experiment = message.get("experiment")

        details = "Origem = " + message.get("sender") + " Valor = " + str(value)

        self.registraEvento("RECEIVE", details, chain)

        return value, chain, path, position, experiment

    def start(self):
        
        """
        Loop de funcionamento do processo
        """

        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        server.bind((HOST, self.port))
        server.listen()

        server.settimeout(1)

        print(f"{self.process_id} escutando em {HOST}:{self.port}")

        while self.running:
            try:
                connection, address = server.accept()

                self.processa(connection)

            except socket.timeout:
                continue

        server.close()

        print(f"{self.process_id} encerrado.")