import socket
import threading
import time
import json
import os
import subprocess

PORTA = 5000

contadores = {
    "lsa_enviados": 0,
    "lsa_recebidos": 0,
    "lsa_propagados": 0,
    "lsa_descartados": 0,
    "recalculos": 0
}

def registrar_log(msg):
    nome = os.environ.get("my_name", "roteador")
    hora = time.strftime("%Y-%m-%d %H:%M:%S")
    caminho = f"/app/logs/{nome}_rotas.log"
    log_dict = {
        "timestamp": hora,
        "mensagem": msg
    }
    print(f"[{hora}] {msg}", flush=True)
    try:
        with open(caminho, "a") as f:
            f.write(json.dumps(log_dict) + "\n")
    except Exception as e:
        print(f"[ERRO] Falha no log: {e}", flush=True)

class Vizinho:
    def __init__(self, nome, ip, custo=1):
        self.nome = nome
        self.ip = ip
        self.custo = custo

class Roteador:
    def __init__(self, nome, ip, vizinhos):
        self.nome = nome
        self.ip = ip
        self.vizinhos = vizinhos
        self.lsas = {}
        self.sequencia = 0
        self.ultima_tabela = {}
        self.convergencia_inicio = None

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((self.ip, PORTA))
        registrar_log(f"{self.nome} ouvindo em {self.ip}:{PORTA}")
        
        threading.Thread(target=self.ouvir_mensagens, daemon=True).start()
        threading.Thread(target=self.enviar_periodicamente, daemon=True).start()


    def criar_lsa(self):
        self.sequencia += 1
        return {
            "id": self.nome,
            "ip": self.ip,
            "seq": self.sequencia,
            "vizinhos": {v.nome: {"ip": v.ip, "custo": v.custo} for v in self.vizinhos.values()}
        }

    def enviar_lsa(self):
        mensagem = json.dumps(self.criar_lsa()).encode()
        for vizinho in self.vizinhos.values():
            try:
                self.socket.sendto(mensagem, (vizinho.ip, PORTA))
                contadores["lsa_enviados"] += 1
                registrar_log(f"LSA enviado para {vizinho.nome} ({vizinho.ip})")
            except Exception as e:
                registrar_log(f"Erro ao enviar LSA para {vizinho.nome}: {e}")

    def enviar_periodicamente(self):
        while True:
            self.enviar_lsa()
            time.sleep(15)

    def ouvir_mensagens(self):
        while True:
            dados, origem = self.socket.recvfrom(4096)
            try:
                lsa = json.loads(dados.decode())
                id_remetente = lsa["id"]
                if id_remetente not in self.lsas or lsa["seq"] > self.lsas[id_remetente]["seq"]:
                    self.lsas[id_remetente] = lsa
                    contadores["lsa_recebidos"] += 1
                    registrar_log(f"LSA recebido de {id_remetente} (seq {lsa['seq']})")
                    self.convergencia_inicio = time.time()
                    self.propagar_lsa(lsa, origem)
                    self.calcular_rotas()
                else:
                    contadores["lsa_descartados"] += 1
            except Exception as e:
                registrar_log(f"Erro ao processar LSA: {e}")

    def propagar_lsa(self, lsa, origem):
        dados = json.dumps(lsa).encode()
        for vizinho in self.vizinhos.values():
            if (vizinho.ip, PORTA) != origem:
                self.socket.sendto(dados, (vizinho.ip, PORTA))
                contadores["lsa_propagados"] += 1
                registrar_log(f"Propagando LSA de {lsa['id']} para {vizinho.nome}")

    def calcular_rotas(self):
        inicio = time.time()
        grafo = {}
        for lsa in self.lsas.values():
            grafo[lsa["id"]] = {}
            for vizinho_nome, info in lsa["vizinhos"].items():
                grafo[lsa["id"]][vizinho_nome] = info["custo"]

        dist = {n: float('inf') for n in grafo}
        anterior = {n: None for n in grafo}
        dist[self.nome] = 0
        fila_rotas = [(0, self.nome)]

        while fila_rotas:
            fila_rotas.sort()
            custo_atual, atual = fila_rotas.pop(0)
            for vizinho_nome, peso in grafo.get(atual, {}).items():
                novo_custo = custo_atual + peso
                if novo_custo < dist[vizinho_nome]:
                    dist[vizinho_nome] = novo_custo
                    anterior[vizinho_nome] = atual
                    fila_rotas.append((novo_custo, vizinho_nome))

        rotas = {}
        for destino in grafo:
            if destino != self.nome and anterior[destino]:
                proximo = destino
                while anterior[proximo] != self.nome and anterior[proximo]:
                    proximo = anterior[proximo]
                rotas[destino] = (proximo, dist[destino])

        if rotas != self.ultima_tabela:
            log_linhas = ["Tabela de rotas:"]
            for destino, (via, custo) in rotas.items():
                log_linhas.append(f"{destino} -> {via} (custo {custo})")
            registrar_log("\n".join(log_linhas))
            self.ultima_tabela = rotas.copy()

        contadores["recalculos"] += 1
        duracao = time.time() - inicio
        registrar_log(f"Tempo de Dijkstra: {duracao:.6f}s | Recalculo #{contadores['recalculos']}")

        for destino, (via, custo) in rotas.items():
            ip_destino = self.lsas[destino]["ip"]
            ip_via = self.lsas[via]["ip"]
            rede = '.'.join(ip_destino.split('.')[:3]) + '.0/24'

            vizinho_direto = False
            for vizinho in self.vizinhos.values():
                if vizinho.ip == ip_destino:
                    vizinho_direto = True
                    break

            if not vizinho_direto:
                cmd = ["ip", "route", "replace", rede, "via", ip_via]
                resultado = subprocess.run(cmd, capture_output=True, text=True)
                if resultado.returncode == 0:
                    registrar_log(f"Rota para {rede} via {ip_via} aplicada")
                else:
                    registrar_log(f"Erro ao aplicar rota: {resultado.stderr}")
            
            if self.convergencia_inicio:
                tempo_convergencia = time.time() - self.convergencia_inicio
                registrar_log(f"Tempo de convergência: {tempo_convergencia:.6f}s")
                self.convergencia_inicio = None



if __name__ == "__main__":
    registrar_log("Iniciando roteador simplificado...")

    nome = os.environ["my_name"]
    ip_local = os.environ["my_ip"]
    lista_vizinhos = os.environ["router_links"].split(",")

    vizinhos = {}
    for nome_vizinho in lista_vizinhos:
        ip_vizinho = os.environ.get(f"{nome_vizinho}_ip")
        if ip_vizinho:
            vizinhos[nome_vizinho] = Vizinho(nome_vizinho, ip_vizinho)
            registrar_log(f"Vizinho {nome_vizinho} com IP {ip_vizinho} registrado")

    r = Roteador(nome, ip_local, vizinhos)

    while True:
        time.sleep(1)
