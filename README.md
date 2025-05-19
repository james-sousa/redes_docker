
# redes_docker
# Projeto de Simulacao de Roteamento por Estado de Enlace com Docker e Python

Este projeto tem como objetivo simular uma rede de computadores utilizando Docker e Python, onde os roteadores implementam o algoritmo de roteamento por Estado de Enlace (Link State Routing Algorithm). Cada roteador comunica-se com os outros utilizando o protocolo UDP e calcula rotas com base no algoritmo de Dijkstra, atualizando dinamicamente a tabela de roteamento.

## Tecnologias Utilizadas

* Python 3.10+
* Docker e Docker Compose
* Protocolo UDP para envio de pacotes de controle (LSAs)
* Comando `ip route` para atualização da tabela de roteamento

## Topologias Implementadas

O sistema permite duas topologias de interconexão entre os roteadores:

* **Topologia Linear:** Cada roteador conecta-se ao próximo em uma cadeia (ex: R1-R2-R3...)
* **Topologia em Anel:** Cada roteador conecta-se ao seguinte e o último conecta-se ao primeiro, formando um ciclo
* Topologia Aleatoria Parcialmente conectada: A topologia da rede entre os roteadores é gerada de forma aleatória, garantindo que todos os roteadores estejam conectados direta ou indiretamente (grafo conexo), mas sem formar uma malha completa

Cada roteador é ligado a dois hosts, formando uma subrede /24 por conjunto de roteador e hosts.

##  Estrutura da Rede

Para cada roteador, temos:

* 1 container do roteador
* 2 containers de hosts conectados ao roteador
* Subrede exclusiva (172.18.X.0/24) entre o roteador e os dois hosts
* Subredes dedicadas entre roteadores vizinhos

## Formato dos Pacotes de Estado de Enlace (LSAs)

Os pacotes LSAs são enviados via UDP e possuem o seguinte formato JSON:

```json
{
  "id": "router1",
  "ip": "172.18.0.2",
  "seq": 3,
  "vizinhos": {
    "router2": {
      "ip": "172.18.0.6",
      "custo": 1
    },
    "router3": {
      "ip": "172.18.0.10",
      "custo": 1
    }
  }
}

```

* `id`: Nome único do roteador emissor do LSA
* `ip`: Endereço IP do roteador emissor
* `seq`: Número de sequência do LSA (incrementado a cada novo envio, usado para garantir a versão mais recente)
* `vizinhos`: dicionário com os roteadores vizinhos e seus custos

## Justificativa do Protocolo UDP

O protocolo **UDP** foi escolhido por ser mais leve e eficiente em cenários de rede controlada. Como os roteadores estão em um ambiente de simulação (Docker), onde a perda de pacotes é minimamente controlada, o overhead do TCP seria desnecessário. Além disso:

* UDP permite envio de pacotes sem conexão
* Menor latência
* Maior controle do formato dos pacotes

## Atualização da Tabela de Roteamento

Cada roteador:

1. Recebe LSAs em uma thread
2. Transmite seus LSAs periodicamente em outra thread
3. Atualiza sua LSDB
4. Executa o algoritmo de Dijkstra
5. Aplica as rotas usando `ip route`

## Execução do Projeto

1. Clone o repositório:

```bash
git clone https://github.com/seuusuario/nome-do-projeto.git
cd nome-do-projeto
```

2. Construa os containers:

```bash
sudo docker-compose up --build
```

3. Listar Containers Ativos:

```bash
sudo docker ps
```

4. Comando para encerrar e limpar completamente o ambiente Docker:

```bash
sudo docker-compose down --volumes --remove-orphans
```

5. Teste conectividade:

```bash
sudo docker exec -it host1a 
ping 172.18.X.Y
```

## Arquivos do Projeto

* `docker-compose.yml` — define todos os containers da rede
* `Dockerfile` — instala dependências para os roteadores
* `router.py` — implementa o comportamento do roteador (envio/recebimento de LSAs, Dijkstra)
* `host.py` — comportamento simples dos hosts
* `gerador.py` — gera a topologia da rede (aleatória, linear ou anel)
* `logs/` —guarda os logs gerados pelo router e pelo host
* `README.md` — este arquivo

## 🔧 Manutenção e Escalabilidade

* O projeto permite adicionar mais roteadores facilmente, alterando o `gerador.py`

* Como executar o gerador:\\
    ```bash
        python3 gerador.py
    ```
    ```bash
        Escolha a forma de definir as vizinhanças:
        1 - Gerar aleatoriamente (máx. 2 vizinhos)
        2 - Topologia linear (em linha)
        3 - Topologia anel (linha + conexão entre extremos)

    ```

  Os logs e tempos de convergência podem ser analisados via arquivos de log gerados pelos roteadores dentro da pasta de logs

## Limiares e Stress

Testes mostraram que a rede suporta até 8 roteadores com 16 hosts com:

* Convergência em menos de 2 segundos
* Tabelas de rota estáveis

Gráficos de performance estão incluídos no relatório em PDF.

## Vantagens da Abordagem

* Arquitetura modular e extensível
* Utiliza UDP para maior eficiência
* Execução distribuída realista com Docker

## Desvantagens da Abordagem

* UDP não garante entrega dos pacotes
* Falhas em containers podem afetar a simulação
* Maior complexidade no controle de sincronização e topologia

## Verificação de Conectividade

Sim. Um host consegue realizar um `ping` qualquer outro host da rede, desde que as rotas tenham convergido corretamente após a troca de LSAs.

## Autor

Aluno: James de Sousa
Curso de Sistemas de Informação - UFPI CSHNB

## 🎥 Demonstração

O vídeo com a demonstração do funcionamento está disponível em:
[YouTube - Simulação Estado de Enlace](https://drive.google.com/file/d/1kjQPEHe-Ydq0zAV2c8-f5aus6JXfcZ49/view?usp=drive_link)

---

Este projeto foi desenvolvido como parte da disciplina **Redes de Computadores II**, sob orientação do professor da Universidade Federal do Piauí - CSHNB.




