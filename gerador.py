#!/usr/bin/env python3
import random

def gerar_docker_compose_custom(links_roteadores):
    version = "3.8"
    base_subnet = "172.19"

    roteadores_ordenados = sorted(links_roteadores.keys())

    ip_contadores = {}  # Próximo IP disponível por sub-rede
    router_ips = {}
    router_net_ips = {}

    # IP principal para cada roteador (usado para identificação)
    for i, router in enumerate(roteadores_ordenados, 1):
        subnet = f"subnet_{i}"
        base_ip = f"{base_subnet}.{i}"
        ip_contadores[subnet] = 2  # começa do .2
        ip = f"{base_ip}.{ip_contadores[subnet]}"
        ip_contadores[subnet] += 1
        router_ips[router] = ip
        router_net_ips[router] = {subnet: ip}

    # Adiciona IPs nas subnets dos vizinhos, evitando conflitos
    for router in roteadores_ordenados:
        for vizinho in links_roteadores[router]:
            if vizinho not in roteadores_ordenados:
                continue
            vizinho_index = roteadores_ordenados.index(vizinho) + 1
            subnet = f"subnet_{vizinho_index}"
            base_ip = f"{base_subnet}.{vizinho_index}"
            if subnet not in router_net_ips[router]:
                if subnet not in ip_contadores:
                    ip_contadores[subnet] = 2
                ip = f"{base_ip}.{ip_contadores[subnet]}"
                ip_contadores[subnet] += 1
                router_net_ips[router][subnet] = ip

    # Variáveis de ambiente
    router_env_vars = {}
    for router in roteadores_ordenados:
        env = [f"my_name={router}", f"my_ip={router_ips[router]}", f"router_links={','.join(links_roteadores[router])}"]
        for viz in links_roteadores[router]:
            if viz in router_ips:
                env.append(f"{viz}_ip={router_ips[viz]}")
        router_env_vars[router] = env

    # IPs dos hosts
    host_ips = []
    for i in range(1, len(roteadores_ordenados) + 1):
        host_ips.append(f"{base_subnet}.{i}.10")
        host_ips.append(f"{base_subnet}.{i}.11")
    router_ips_list = list(router_ips.values())

    def comando_ping(meu_ip):
        targets = [ip for ip in host_ips + router_ips_list if ip != meu_ip]
        return ' '.join([f"'ping {ip}'" for ip in targets])

    # Geração do docker-compose
    content = f"version: '{version}'\n\nservices:\n"

    # Routers
    for router in roteadores_ordenados:
        content += f"  {router}:\n"
        content += "    build:\n"
        content += "      context: ./router\n"
        content += "      dockerfile: Dockerfile\n"
        content += "    environment:\n"
        for env_var in router_env_vars[router]:
            content += f"      - {env_var}\n"
        content += "    networks:\n"
        for net, ip in sorted(router_net_ips[router].items()):
            content += f"      {net}:\n"
            content += f"        ipv4_address: {ip}\n"
        content += "    cap_add:\n"
        content += "      - NET_ADMIN\n"
        content += "    volumes:\n"
        content += "      - ./logs:/app/logs\n"
        content += "\n"

    # Hosts
    for i in range(1, len(roteadores_ordenados) + 1):
        for suffix in ['a', 'b']:
            host_name = f"host{i}{suffix}"
            host_ip = f"{base_subnet}.{i}.1{0 + (ord(suffix) - ord('a'))}"
            content += f"  {host_name}:\n"
            content += "    build:\n"
            content += "      context: ./host\n"
            content += "      dockerfile: Dockerfile\n"
            content += "    environment:\n"
            content += f"      - my_name={host_name}\n"
            content += f"      - my_ip={host_ip}\n"
            content += "    networks:\n"
            content += f"      subnet_{i}:\n"
            content += f"        ipv4_address: {host_ip}\n"
            content += "    depends_on:\n"
            content += f"      - {roteadores_ordenados[i - 1]}\n"
            content += "    command: [\"sh\", \"-c\", \"sleep 10 && python host.py --test " + comando_ping(host_ip) + "\"]\n"
            content += "    volumes:\n"
            content += "      - ./logs:/app/logs\n"
            content += "    cap_add:\n"
            content += "      - NET_ADMIN\n"
            content += "\n"

    # Networks
    content += "networks:\n"
    for i in range(1, len(roteadores_ordenados) + 1):
        content += f"  subnet_{i}:\n"
        content += "    driver: bridge\n"
        content += "    ipam:\n"
        content += "      config:\n"
        content += f"      - subnet: {base_subnet}.{i}.0/24\n"

    return content


def criar_topologia():
    while True:
        try:
            n = int(input("Digite o número de roteadores: "))
            if n < 2:
                print("Número deve ser pelo menos 2.")
                continue
            break
        except ValueError:
            print("Digite um número válido.")

    roteadores = [f"router{i + 1}" for i in range(n)]

    print("\nEscolha a forma de definir as vizinhanças:")
    print("1 - Gerar aleatoriamente (máx. 2 vizinhos)")
    print("2 - Topologia linear (em linha)")
    print("3 - Topologia anel (linha + conexão entre extremos)")
    opc = input("Opção (1/2/3): ").strip()

    links = {r: [] for r in roteadores}

    if opc == "1":
        print("\nGerando topologia aleatória parcialmente conectada...")

        for i, r in enumerate(roteadores):
            if i == 0:
                # Evita escolher o último roteador como vizinho direto do primeiro
                vizinhos_possiveis = roteadores[1:-1] if len(roteadores) > 2 else [roteadores[1]]
                vizinhos = random.sample(vizinhos_possiveis, k=min(2, len(vizinhos_possiveis)))
            elif i == len(roteadores) - 1:
                vizinhos = [roteadores[i - 1]]
            else:
                vizinhos = [roteadores[i - 1]]
                if i + 1 < len(roteadores) and random.random() < 0.7:
                    vizinhos.append(roteadores[i + 1])
            links[r] = vizinhos

        # Garante que as conexões sejam bidirecionais
        for r, viz in links.items():
            for v in viz:
                if r not in links[v]:
                    links[v].append(r)


    elif opc == "2":
        for i, r in enumerate(roteadores):
            if i > 0:
                links[r].append(roteadores[i - 1])
            if i < len(roteadores) - 1:
                links[r].append(roteadores[i + 1])
    elif opc == "3":
        for i, r in enumerate(roteadores):
            if i > 0:
                links[r].append(roteadores[i - 1])
            if i < len(roteadores) - 1:
                links[r].append(roteadores[i + 1])
        links[roteadores[0]].append(roteadores[-1])
        links[roteadores[-1]].append(roteadores[0])
    else:
        print("Opção inválida. Nenhuma vizinhança definida.")

    for r in links:
        links[r] = list(set(links[r]))

    return links


if __name__ == "__main__":
    print("=== Gerador interativo de docker-compose.yml para topologia de roteadores ===\n")
    links = criar_topologia()

    print("\nTopologia definida:")
    for r, v in links.items():
        print(f"  {r}: {v}")

    conteudo = gerar_docker_compose_custom(links)

    with open("docker-compose.yml", "w") as f:
        f.write(conteudo)

    print("\nArquivo docker-compose.yml gerado com sucesso!")
