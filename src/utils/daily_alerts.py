import os
import sys
import smtplib
from email.message import EmailMessage
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.data.db import get_supabase
from src.data.fetch_api import fetch_farm_data
from src.models.predict import build_payload, get_prediction

def send_alert_email(email_to, farm_name, alertas):
    msg = EmailMessage()
    msg['Subject'] = f"🚨 Alerta Operacional: {farm_name} (OmniCrop AI)"
    msg['From'] = "alertas@cropilot.ai"
    msg['To'] = email_to
    
    alertas_str = "\n".join([f"- {a}" for a in alertas])
    content = f"""Bom dia!
    
O Satélite Virtual detectou os seguintes riscos iminentes na fazenda {farm_name} hoje:

{alertas_str}

Por favor, acesse o Dashboard para redirecionar a operação ou iniciar o Simulador de Salvamento.

Atenciosamente,
IA do OmniCrop AI
"""
    msg.set_content(content)
    
    # Mocked SMTP Send
    print(f"\n--- EMAIL DISPARADO PARA: {email_to} ---")
    print(msg.as_string())
    print("-------------------------------------------\n")

def send_webhook_alert(webhook_url: str, farm_name: str, alertas: list[str], ndvi: float = None) -> bool:
    """Dispara notificação operacional estruturada para Webhooks (Discord, Slack, Telegram, Zapier)."""
    import requests
    if not webhook_url or not webhook_url.startswith("http"):
        return False
    
    # Formato compatível com Discord e Slack
    if "discord.com" in webhook_url or "slack.com" in webhook_url:
        alertas_txt = "\n".join([f"• {a}" for a in alertas])
        payload = {
            "content": f"🚨 **Alerta OmniCrop AI · Fazenda {farm_name}**\n**NDVI Atual/Projetado:** {ndvi if ndvi is not None else 'N/A'}\n**Riscos Detectados:**\n{alertas_txt}\n👉 *Acesse o dashboard para simular intervenções no pivô/adubação.*"
        }
    else:
        payload = {
            "title": f"🚨 Alerta Operacional: {farm_name} (OmniCrop AI)",
            "farm_name": farm_name,
            "ndvi_atual": ndvi,
            "alertas": alertas,
            "action_required": "Acessar Dashboard para simular intervenção e ajustar manejo."
        }
        
    try:
        r = requests.post(webhook_url, json=payload, timeout=6)
        return r.status_code in [200, 204]
    except Exception as e:
        print(f"Erro ao enviar webhook: {e}")
        return False

def dispatch_alert(destination: str, farm_name: str, alertas: list[str], ndvi: float = None) -> dict:
    """
    Roteador inteligente de alertas:
    Identifica automaticamente se o canal é Webhook ou E-mail e despacha a notificação.
    """
    if not destination:
        return {"success": False, "channel": "none", "message": "Destino não informado."}
    
    dest_clean = destination.strip()
    if dest_clean.startswith("http://") or dest_clean.startswith("https://"):
        ok = send_webhook_alert(dest_clean, farm_name, alertas, ndvi)
        return {
            "success": ok,
            "channel": "webhook",
            "message": "Notificação enviada ao Webhook com sucesso!" if ok else "Falha ao enviar webhook (verifique a URL)."
        }
    else:
        send_alert_email(dest_clean, farm_name, alertas)
        return {
            "success": True,
            "channel": "email",
            "message": f"E-mail operacional despachado para {dest_clean}."
        }


def run_daily_cron():
    print("Iniciando rotina de checagem diária...")
    supabase = get_supabase()
    
    # Busca todos os usuarios (precisa de secret service role, mas assumimos permissao de admin aqui)
    try:
        users = supabase.auth.admin.list_users()
    except:
        # Fallback para desenvolvimento sem admin_role
        print("Mockando usuarios...")
        users = [{"id": "user123", "email": "diretor@usina.com"}]
        
    # Busca todas as fazendas registradas
    res = supabase.table("fazendas").select("*").execute()
    farms = res.data
    
    for farm in farms:
        print(f"Analisando fazenda: {farm['farm_name']}")
        try:
            # 1. Puxa os dados climáticos reais dos satelites
            df_live, today = fetch_farm_data(farm['lat'], farm['lon'])
            
            # 2. Roda pelo Gradient Boosting
            payload = build_payload(today)
            resultado = get_prediction(payload)
            
            # 3. Dispara e-mail se houver alertas de risco (e se estiver ativo para a fazenda)
            alertas = resultado.get("fatores_de_risco_identificados", [])
            if len(alertas) > 0:
                if farm.get('receber_alertas', True) == False:
                    print(f"🔕 Avisos desativados pelo usuario para {farm['farm_name']}. Pulando...")
                    continue

                print(f"⚠️ {len(alertas)} alertas disparados! Enviando e-mail...")
                # Procura o email do dono da fazenda
                email_dono = "mock@email.com" # Exemplo
                send_alert_email(email_dono, farm['farm_name'], alertas)
            else:
                print("✅ Tudo OK. Sem alertas para enviar.")
                
        except Exception as e:
            print(f"Erro ao processar {farm['farm_name']}: {e}")

if __name__ == "__main__":
    run_daily_cron()
