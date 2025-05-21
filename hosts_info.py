import yaml

def pegar_hosts_ips(filename='docker-compose.yml'):
    with open(filename, 'r') as f:
        docker_compose = yaml.safe_load(f)

    services = docker_compose.get('services', {})
    hosts_info = []

    for service_name, service_data in services.items():
        if not service_name.startswith('host'):
            continue

        env_vars = service_data.get('environment', [])
        host_name = None
        for env in env_vars:
            if isinstance(env, str) and env.startswith('my_name='):
                host_name = env.split('=', 1)[1]
                break
            elif isinstance(env, dict) and 'my_name' in env:
                host_name = env['my_name']
                break

        networks = service_data.get('networks', {})
        ips = []
        for net, net_data in networks.items():
            if isinstance(net_data, dict):
                ip = net_data.get('ipv4_address')
                if ip:
                    ips.append(ip)

        hosts_info.append({
            'service': service_name,
            'host_name': host_name,
            'ips': ips
        })

    return hosts_info


def salvar_txt(hosts_info, filename='lista_ip_hosts_.txt'):
    with open(filename, 'w') as f:
        for h in hosts_info:
            f.write(f"Serviço: {h['service']}\n")
            f.write(f"Host name: {h['host_name']}\n")
            f.write(f"IPs: {', '.join(h['ips'])}\n")
            f.write('-' * 30 + '\n')

if __name__ == "__main__":
    hosts = pegar_hosts_ips()
    salvar_txt(hosts)
    print(f"Arquivo 'hosts_info.txt' criado com sucesso!")
