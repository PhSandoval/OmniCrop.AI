# 📖 OmniCrop AI — Guia do Usuário e Casos de Uso (UC)

Este guia documenta o que cada tipo de usuário pode fazer na plataforma OmniCrop AI. Os Casos de Uso (UCs) foram divididos por módulo da aplicação, permitindo que a jornada do usuário fique clara e objetiva.

---

## 1. Módulo de Autenticação e Configuração Inicial

### UC01: Criar Conta e Autenticar
O usuário (Produtor, Agrônomo ou Gestor) consegue criar uma conta de forma segura. O sistema persiste a sessão e garante que nenhuma tela interna possa ser acessada sem um login válido.
- **Ação:** Preencher e-mail e senha na tela inicial.

### UC02: Cadastrar Nova Fazenda (Onboarding Georreferenciado)
O usuário pode adicionar novos talhões buscando por Cidade, Endereço completo, ou CEP. Ao clicar no mapa interativo (Folium), ele captura automaticamente a Latitude e Longitude reais para vincular as bases climáticas.
- **Ação:** Ao logar na primeira vez, ou clicando em "Adicionar Outro Talhão" nas Configurações, uma tela interativa de mapa permite buscar e validar a área plantada.

### UC03: Multi-Tenancy (Gerenciar Múltiplos Talhões)
Um mesmo usuário pode ser dono de dezenas de talhões ou fazendas diferentes. A barra lateral permite alternar entre os contextos, alterando imediatamente os dados, clima e alertas do dashboard para a propriedade selecionada.
- **Ação:** Usar a barra lateral (Sidebar) no dropdown "Mudar Fazenda".

---

## 2. Módulo de Monitoramento e IA Preditiva (Dashboard Principal)

### UC04: Visualizar Clima Atual e Histórico (Open-Meteo)
Ao acessar um talhão, o usuário vê instantaneamente a precipitação (chuva) acumulada dos últimos 30, 60 e 90 dias, Graus-Dia acumulados (GDA) e as temperaturas do dia. O sistema coleta essas informações automaticamente sem hardware em campo.
- **Ação:** Ler o painel principal superior.

### UC05: Ver Previsão Inteligente de Vigor Vegetativo (NDVI)
Em vez de esperar dias até a passagem de um satélite limpo (sem nuvens), o usuário utiliza o painel central "Satélite Virtual", onde a Inteligência Artificial da OmniCrop (baseada em XGBoost) estima o vigor atual da planta.
- **Ação:** O painel "NDVI" no meio da tela mostra o nível atual (velocímetro) e a série temporal.

### UC06: Obter Parecer Agronômico Generativo
Abaixo dos indicadores e alertas, o sistema exibe um laudo textual em português escrito pelo agrônomo da IA (via Google Gemini) ressaltando oportunidades ou criticando os perigos da condição térmica/hídrica no dia atual.
- **Ação:** Ler a seção "Parecer do Agrônomo".

---

## 3. Módulo de Simulação e Decisão (DSS)

### UC07: Simular Cenários de Risco e Investimento
O agrônomo pode alterar as variáveis do clima (ex: "E se não chover nada nos próximos 15 dias?") ou simular uma intervenção (ex: "E se eu gastar dinheiro irrigando hoje?"). A plataforma prevê se o NDVI da cultura vai cair, se manter, e se a intervenção vale a pena financeiramente (ROI de Máquinas/Insumos).
- **Ação:** Acessar a aba "Simulador" na navegação lateral, arrastar os *sliders* e clicar em "Simular".

### UC08: Analisar Previsões de Risco em Operações
O usuário checa se pode mandar as colheitadeiras e tratores para o campo ou se há risco de atolamento por chuvas. Verifica também janela segura para Adubação e Plantio.
- **Ação:** Acessar a aba "Análise" na navegação lateral.

---

## 4. Módulo de Relatórios e Suporte

### UC09: Exportar Relatório Executivo PDF
O Gestor da fazenda emite um documento formal, formatado automaticamente com tabelas limpas, gráficos de linha da evolução da safra, selo de Confiabilidade e laudo final do robô agronômico (Gemini), pronto para enviar para investidores, usinas ou diretores, ou para ser guardado em arquivo morto.
- **Ação:** Clicar no botão "Gerar Relatório Executivo (PDF)" no Dashboard principal.

### UC10: Chat Assistente de Manejo (Tira-dúvidas)
O usuário acessa o chat inteligente do sistema para perguntar dúvidas de agronomia, decifrar os dados da tela (ex: "O que é NDVI?", "Por que chover agora afeta meu GDA?"), tudo contextualizado à cana-de-açúcar e ao clima da fazenda real.
- **Ação:** Acessar a página "Assistente de Manejo".
