# 🛡️ Política de Segurança e Divulgação Coordenada (NIS-2 & ISA-62443) — OmniCrop AI

O **OmniCrop AI** está comprometido com os mais altos padrões de segurança da informação, privacidade de dados e resiliência cibernética, em estrita conformidade com a **Diretiva NIS-2 (União Europeia 2022/2555)** e a norma internacional de cibersegurança industrial **ISA-62443 / IEC 62443**.

---

## 1. Versões Suportadas

Apenas a versão ativa em produção na branch `main` recebe correções de segurança imediatas:

| Versão / Ambiente | Suporte de Segurança | Repositório / Endpoint |
|---|:---:|---|
| **v2.0 (Produção Nuvem)** | ✅ Ativo e Suportado | [omnicropai.streamlit.app](https://omnicropai.streamlit.app) |
| **API RESTful Headless** | ✅ Ativo e Suportado | `src/api/` (Porta 8000) |
| **Versões legadas (< 2.0)** | ❌ Descontinuadas | N/A |

---

## 2. Coordinated Vulnerability Disclosure (CVD) — Diretiva NIS-2 Art. 21

Apoiamos a divulgação responsável e coordenada de potenciais vulnerabilidades. Se você identificou uma falha de segurança no OmniCrop AI:

### Como Reportar:
- **Canal Seguro:** Envie um e-mail com a descrição técnica e passos de reprodução (PoC) para:  
  📬 `security@omnicrop.ai` ou `pedro.sandoval@alumni.usp.br`
- **Criptografia:** É incentivado o uso de criptografia PGP quando disponível.
- **O que NÃO fazer:**
  - Não execute testes de negação de serviço (DoS/DDoS) contra a infraestrutura em produção.
  - Não altere, destrua ou acesse dados de terceiros (respeito irrestrito ao multi-tenancy e LGPD).

### Prazos Formais de Resposta (NIS-2 Artigo 23):
- **Confirmação de Recebimento (Triagem Inicial):** até **24 horas** úteis.
- **Avaliação de Impacto e Alerta Inicial (*Early Warning*):** até **24 horas** após a confirmação.
- **Remediação e Relatório Completo de Resolução (*Final Incident Report*):** até **72 horas** para incidentes de alta severidade.

---

## 3. Matriz de Severidade (Baseada em CVSS v3.1 / NIS-2)

| Nível | Impacto Operacional | SLA de Remediação |
|---|---|:---:|
| **CRITICAL** | Execução Remota de Código (RCE), Bypasses de Autenticação/RLS, comprometimento de segredos de produção | < 24 horas |
| **HIGH** | Injeção de dados falsos em telemetria IoT (Data Poisoning), SSRF em endpoints internos, Stored XSS | < 48 horas |
| **MEDIUM** | Falhas de rate limiting, vazamento de metadados em logs, inconsistências de autorização de leitura | < 5 dias úteis |
| **LOW** | Problemas de cabeçalhos de resposta HTTP, sugestões de endurecimento de configurações | Próxima release |

---

## 4. Conformidade ISA-62443 (Zonas de Automação & IoT Agrícola)

1. **Segmentação de Zonas:** Sensores de campo (Zona 1/2) comunicam-se com a Nuvem (Zona 4) exclusivamente através de condutos criptografados (HTTPS/TLS 1.3) com autenticação e validação estrita de esquemas Pydantic.
2. **Proteção Anti-Data Poisoning:** Todas as medições de solo, temperatura e umidade passam por filtros de plausibilidade física agronômica antes de serem processadas pelos modelos de Machine Learning.
3. **Trilha Imutável de Auditoria:** Qualquer tentativa de acesso anômalo, erro de autorização ou alteração de parâmetros agronômicos críticos é persistida na tabela `audit_logs` no PostgreSQL com isolamento RLS.
