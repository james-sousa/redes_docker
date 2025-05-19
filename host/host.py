import os
import sys
import time
import subprocess

class RegistroLog:
    def __init__(self, nome_host):
        self.nome_host = nome_host
        self.arquivo_log = f"/app/logs/{nome_host}.log"
    
    def registrar(self, mensagem):
        timestamp = time.strftime("[%Y-%m-%d %H:%M:%S]")
        formatado = f"{timestamp} {mensagem}"
        print(formatado, flush=True)
        try:
            with open(self.arquivo_log, "a") as f:
                f.write(formatado + "\n")
        except Exception as e:
            print(f"[ERRO] Falha ao gravar log: {e}", flush=True)

class HostRede:
    def __init__(self, meu_ip, gateway_ip, logger):
        self.meu_ip = meu_ip
        self.router_ip = gateway_ip
        self.logger = logger

    def configurar_gateway(self):
        if not self.router_ip:
            self.logger.registrar("[ERRO] gateway_ip não definido.")
            return
        self.logger.registrar(f"Definindo rota padrão via {self.router_ip}...")
        try:
            subprocess.run(["ip", "route", "del", "default"], capture_output=True)
            resultado = subprocess.run(["ip", "route", "add", "default", "via", self.router_ip], capture_output=True, text=True)
            if resultado.returncode == 0:
                self.logger.registrar("Gateway configurado com sucesso.")
            else:
                self.logger.registrar(f"Falha ao configurar gateway: {resultado.stderr.strip()}")
        except Exception as e:
            self.logger.registrar(f"[ERRO] Durante configuração do gateway: {e}")
    
    def executa_ping(self, destino):
        self.logger.registrar(f"Enviando pacotes ICMP para {destino}...")
        try:
            resultado = subprocess.run(["ping", "-c", "3", destino], capture_output=True, text=True, timeout=15)
            if resultado.returncode == 0:
                self.logger.registrar("Ping bem-sucedido.")
            else:
                self.logger.registrar(f"Ping falhou (código {resultado.returncode}).")

            for linha in resultado.stdout.splitlines():
                if "packets transmitted" in linha:
                    self.logger.registrar(f"[Estatísticas de pacotes] {linha}")
                if "rtt min" in linha or "round-trip" in linha:
                    self.logger.registrar(f"[RTT] {linha}")

            if resultado.returncode != 0:
                self.logger.registrar(f"[DEBUG] Saída do ping:\n{resultado.stdout}\n{resultado.stderr}")

        except subprocess.TimeoutExpired:
            self.logger.registrar(f"Timeout durante ping para {destino}.")
        except Exception as e:
            self.logger.registrar(f"[ERRO] Durante ping para {destino}: {e}")

def main():
    nome_host = os.environ.get("my_name", "host_generico")
    meu_ip = os.environ.get("my_ip", "")
    gateway_ip = os.environ.get("gateway_ip", "")
    logger = RegistroLog(nome_host)

    logger.registrar("Inicializando host...")
    testador = HostRede(meu_ip, gateway_ip, logger)
    testador.configurar_gateway()

    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        destinos = sys.argv[2:]
        if destinos:
            logger.registrar("Iniciando testes de conectividade...")
            for destino in destinos:
                ip_destino = destino.split()[-1]
                testador.executa_ping(ip_destino)
            logger.registrar("Testes finalizados.")
        else:
            logger.registrar("Nenhum destino fornecido para teste.")
    else:
        logger.registrar("Modo passivo. Nenhum teste de rede solicitado.")

    while True:
        time.sleep(60)

if __name__ == "__main__":
    main()
