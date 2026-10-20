# 🛡️ Política de Segurança — OmniCrop AI

Este documento descreve as práticas de segurança, como reportar vulnerabilidades de forma responsável e as medidas defensivas implementadas no **OmniCrop AI**.

---

## 1. Versões Suportadas

Apenas a versão ativa na branch `main` e em execução no ambiente de produção recebe atualizações e correções ativas de segurança:

| Versão / Componente | Suporte | Ambiente |
|---|:---:|---|
| **v2.0 (Streamlit Web)** | ✅ Ativo | [omnicropai.streamlit.app](https://omnicropai.streamlit.app) |
| **API RESTful (FastAPI)** | ✅ Ativo | Microsserviço local / container |
| **Versões legadas** | ❌ Não suportadas | N/A |

---

## 2. Reportando uma Vulnerabilidade

Se você identificou uma potencial falha de segurança no OmniCrop AI:

1. **Não abra uma issue pública** no GitHub com detalhes que possam comprometer a segurança dos dados ou da aplicação.
2. Utilize o canal de **Private Vulnerability Reporting** do próprio GitHub neste repositório ou envie um e-mail com os detalhes técnicos e passos de reprodução (PoC) para:  
   📬 **`pedro.sandoval@alumni.usp.br`**
3. Avaliaremos o reporte o mais breve possível para investigar e aplicar as correções necessárias.

> **Importante:** Por favor, realize testes de forma ética e responsável, sem executar ataques de negação de serviço (DoS/DDoS) e sem tentar acessar ou adulterar dados de outros usuários.

---

## 3. Medidas de Proteção Implementadas no Projeto

O OmniCrop AI adota práticas defensivas em código (*Defense-in-Depth*) para garantir integridade e isolamento de dados:

* **Auditoria de Dependências (SCA):** Verificação contínua no pipeline de CI com `pip-audit`, bloqueando dependências com vulnerabilidades conhecidas (CVEs).
* **Validação Estrita de Dados (Pydantic v2):** Schemas de entrada barram dados corrompidos ou maliciosos em contratos de API e na ingestão de telemetria.
* **Mitigação de SSRF (Server-Side Request Forgery):** Bloqueio de requisições para endereços IP privados, de loopback e link-local (`127.0.0.1`, `192.168.x.x`, `10.x.x.x`) nos disparos de webhooks de alerta.
* **Proteção contra Stored XSS e Injeções:** Sanitização com `html.escape()` na exibição de dados de propriedades e cabeçalhos no frontend.
* **Isolamento Multi-Tenant (RLS):** Toda comunicação com o banco de dados Supabase PostgreSQL utiliza Row-Level Security (RLS) baseada no token JWT do usuário ativo, impedindo acesso cruzado entre fazendas.
* **Mascaramento em Logs:** O formatador estruturado `StructuredJsonFormatter` ofusca chaves sensíveis (`password`, `token`, `secret`, `api_key`) nos registros do sistema.
