# simulador-lamport

O código foi escrito em Python. Ele não recebe argumentos de linha de execução. Deve ser chamado através da main (py ./main.py).

As configurações do projeto podem ser acessadas e alteradas livremente dentro de config.py contanto que respeitem o formato adequado. Dessa maneira, é possível alterar o valor inicial de uma cadeia de processos e outros detalhes dos experimentos. 

O arquivo main.py funciona como coordenador. Ele inicializa os processos e fornece um valor inicial para o primeiro processo da cadeia de execução do experimento corrente. É possível rodar vários experimentos sequencialmente, conforme estiver indicado em config.py. O coordenador também é responsável pela ordenação do log ao fim da execução dos experimentos. 

O arquivo process.py contém o código específico dos processos. O comportamento dos processos é de receber uma mensagem com um valor, realizar uma operação predefinida utilizando o valor recebido e uma constante, e por fim enviar o resultado dessa operação por mensagem para o próximo processo dentro da cadeia de execução atual. Se o processo for o último dentro dessa cadeia, ele sinaliza o seu término ao controlador (main.py). Os detalhes de definição dos processos estão definidos em config.py.

O log de eventos (events.txt, por padrão) é gerado incrementalmente ao longo da execução das funções dos processos. O domínio de cada experimento é demarcado através de linhas de controle. Ao fim de todas as execuções, a função exibeEventosOrdenados() da main percorre o log gerado e contrói um novo log ordenado segundo o relógio lógico dos processos (events_ordered.txt), respeitando a demarcação entre experimentos.

Foi implementada a funcionalidade de plotar a execução de um experimento a partir do log ordenado, chamando o script plot_lamport.py. Para isso, é preciso ter a biblioteca matplotlib instalada. Por definição, foram definidas cores para três cadeias de execução simultâneas. Caso o experimento realizado use mais cadeias, as cores para o plot deverão ser especificadas em config.py
