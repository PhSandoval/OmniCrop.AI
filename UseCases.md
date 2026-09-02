# Casos de Uso (Use Cases)

O SugarCane Copilot foi desenhado para atender Agrônomos, Gestores Agrícolas e Usinas de Cana-de-Açúcar. Abaixo estão os cenários práticos de operação do sistema.

## 1. Planejamento de Colheita (Corte Mecanizado)
**Problema:** Máquinas colhedoras são pesadas. Se o solo estiver muito úmido (após chuvas), a máquina atola, compacta o solo e destrói a soqueira (raiz que vai brotar no próximo ano).
**Solução no App:** O Gestor acessa o *Simulador*, seleciona "Manejo de Colheita" e observa o GDA (calor) e a Chuva Projetada. Se o DSS apontar "Risco Operacional", o gestor adia a colheita daquele talhão e movimenta a frente de corte para uma área mais seca da fazenda.

## 2. Aplicação de Maturador Químico
**Problema:** No outono, a cana precisa parar de crescer e começar a acumular açúcar (ATR). Se continuar chovendo e fazendo calor, ela "vegeta" e perde qualidade industrial.
**Solução no App:** O Agrônomo monitora o *Dashboard*. Se o sistema identificar que o NDVI está muito alto (Cana Verde) durante a fase de maturação (Abril a Outubro), o DSS dispara o alerta "Atenção". O agrônomo então aprova a aplicação aérea (drone/avião) de maturador químico para forçar a planta a acumular açúcar.

## 3. Irrigação de Salvamento vs Desperdício
**Problema:** Irrigar custa caro (energia elétrica de bombeamento). Irrigar na hora errada é jogar dinheiro fora.
**Solução no App:** No *Simulador*, o usuário testa lâminas de irrigação (ex: 40mm/dia por 10 dias). O app calcula o custo financeiro exato (ex: R$ 2.000/ha) e projeta se essa água vai refletir em aumento de Vigor (NDVI). Se a planta estiver na fase de maturação, o sistema bloqueia/rejeita a irrigação informando que é desperdício. Se for fase de crescimento, ele aprova como "Irrigação de Salvamento".

## 4. Prevenção de Risco de Falha no Plantio
**Problema:** Plantar os "toletes" (pedaços de cana) em solo seco e frio faz com que eles não brotem, perdendo todo o investimento.
**Solução no App:** O módulo de "Planejamento de Plantio" cruza os Graus-Dia Acumulados (GDA) e a Chuva de 30 dias. O DSS só libera o status "Plantio Liberado" se houver condição termohídrica excelente para brotação rápida.
