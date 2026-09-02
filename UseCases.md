# Casos de Uso (Use Cases)

O SugarCane Copilot foi desenhado para atuar como o principal assistente de decisão de Agrônomos, Gestores Agrícolas e Diretores de Usinas de Cana-de-Açúcar. Abaixo estão os 6 cenários práticos de geração de valor financeiro (ROI) do sistema.

## 1. Planejamento de Colheita (Corte Mecanizado)
**O Problema:** Máquinas colhedoras pesam toneladas. Se o solo estiver muito úmido, a máquina atola, compacta a terra e "esmaga" a soqueira (a base da planta que vai brotar na próxima safra), causando prejuízos milionários.
**A Solução no App:** O Gestor acessa o *Simulador*, seleciona "Manejo de Colheita" e observa o GDA (calor) e a Chuva Projetada nos próximos 15 dias. Se o DSS apontar "Risco Operacional (>50mm)", a operação de corte naquele talhão é bloqueada e realocada para uma região mais seca.

## 2. Direcionamento Estratégico de Maturador Químico
**O Problema:** No outono, a cana precisa parar de formar folhas verdes e começar a acumular açúcar (ATR) no colmo. Se o clima continuar úmido e quente, ela "vegeta" e perde qualidade industrial.
**A Solução no App:** O Agrônomo cruza a fase de Maturação com o *Dashboard*. Se a IA identificar que o NDVI está anormalmente alto (cana verde demais) para a época do ano, o DSS dispara o alerta "Atenção". Isso justifica o gasto milionário de despachar aviões agrícolas para aplicar o maturador e "travar" a planta à força.

## 3. Irrigação de Salvamento vs Desperdício
**O Problema:** Irrigar custa uma fortuna em energia elétrica (bombeamento dos pivôs). Ligar a água na hora errada é literalmente jogar dinheiro na terra.
**A Solução no App:** No *Simulador*, o usuário testa lâminas de irrigação (ex: 40mm/dia por 10 dias). O app calcula o custo financeiro imediato (ex: R$ 2.000/ha) e a IA projeta se essa água vai refletir em aumento real de Vigor (NDVI). Na fase de maturação, a IA rejeita a ação como "Desperdício". Na fase de crescimento severo, aprova como "Salvamento".

## 4. Prevenção de Risco de Falha no Plantio
**O Problema:** Enterrar os "toletes" (pedaços de cana semente) em um solo que vai secar e esfriar na próxima semana faz com que eles não brotem, forçando um replantio total.
**A Solução no App:** O módulo de "Planejamento de Plantio" analisa os Graus-Dia Acumulados (GDA) e a Previsão de Chuva de 15 dias. O DSS só concede o "Selo Verde" se houver uma "Janela Termohídrica" excelente para a brotação garantida.

## 5. Adubação Inteligente (Risco de Lixiviação)
**O Problema:** Aplicar Ureia (Nitrogênio) sem chuva faz o produto evaporar. Aplicar antes de um temporal faz a água "lavar" o nutriente (Lixiviação).
**A Solução no App:** O simulador de adubação considera a chuva dos próximos 15 dias. Se a chuva for <10mm, ele acusa perda por volatilização. Se for >100mm, acusa lixiviação. Ele recomenda a "janela perfeita" de umidade leve para incorporar o adubo com segurança.

## 6. Monitoramento de Larga Escala (Redução de OPEX)
**O Problema:** Despachar equipes de campo em caminhonetes todo dia para avaliar o crescimento visual de centenas de talhões espalhados num raio de 100km gasta rios de diesel e homem-hora.
**A Solução no App:** Sendo um "Satélite Virtual", a usina monitora a saúde de todas as suas fazendas da sala do painel de controle. As visitas de campo passam a ser "cirúrgicas" e guiadas pelo alerta vermelho do Dashboard.

## 7. Reuniões Executivas de Diretoria (Relatórios em PDF)
**O Problema:** Diretores de Usina não ficam logados em painéis da web o dia todo. Eles tomam decisões de investimento milionárias durante a reunião de segunda-feira com base em papel ou documentos de fácil leitura na mesa.
**A Solução no App:** O Gestor da Fazenda clica no botão "Baixar Relatório Semanal (PDF)" no topo do painel. A inteligência compila o Vigor, a Seca e as anomalias da semana num arquivo enxuto, que o gestor pode imprimir ou mandar no WhatsApp para a Diretoria em 2 segundos, eliminando o gasto de horas montando apresentações no PowerPoint.

## 8. Defesa Ativa Contra Quebra de Safra (Alertas Matinais)
**O Problema:** A rotina de campo começa às 05:00 da manhã. Esperar que um engenheiro agrônomo ligue o notebook no campo, conecte na internet e entre no sistema para ver se choveu demais de madrugada é ineficiente e propenso ao esquecimento humano.
**A Solução no App:** O robô do sistema atua no turno da noite. O Motor de CRON roda às 04:00 da manhã, cruza a chuva que caiu de noite com a previsão futura usando a IA e identifica se o trator vai atolar se entrar na fazenda. O Gerente acorda e, ao olhar o celular na cama, já tem um **e-mail automático de alerta** orientando a mudança da frente de trabalho para outro talhão, salvando o dia da operação.
