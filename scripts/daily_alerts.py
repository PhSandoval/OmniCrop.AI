import os
import sys
import smtplib
from email.message import EmailMessage
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from components.db import get_supabase
from components.live_data import fetch_farm_data
from components.api_client import build_payload, get_prediction

def send_alert_email(email_to, farm_name, alertas):
    msg = EmailMessage()
    msg['Subject'] = f"🚨 Alerta Operacional: {farm_name} (SugarCane Copilot)"
    msg['From'] = "alertas@sugarcanecopilot.com"
    msg['To'] = email_to
    
    alertas_str = "\n".join([f"- {a}" for a in alertas])
    content = f"""Bom dia!
    
O Satélite Virtual detectou os seguintes riscos iminentes na fazenda {farm_name} hoje:

{alertas_str}

Por favor, acesse o Dashboard para redirecionar a operação ou iniciar o Simulador de Salvamento.

Atenciosamente,
IA do SugarCane Copilot
"""
    msg.set_content(content)
    
    # Mocked SMTP Send
    print(f"\n--- EMAIL DISPARADO PARA: {email_to} ---")
    print(msg.as_string())
    print("-------------------------------------------\n")

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
            
            # 2. Roda pelo XGBoost
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
