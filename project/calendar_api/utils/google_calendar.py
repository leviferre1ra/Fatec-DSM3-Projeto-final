# calendar_api/utils/google_calendar.py
import datetime
import os
from googleapiclient.discovery import build
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

# SCOPES necessários (Calendar)
SCOPES = ['https://www.googleapis.com/auth/calendar']

# ---------- SERVICE ACCOUNT (opcional) ----------
def get_service_account_service():
    """Retorna service object usando Service Account JSON."""
    sa_file = os.environ.get('GOOGLE_SERVICE_ACCOUNT_FILE')  # ou caminho relativo project/calendar_api/...
    if not sa_file or not os.path.exists(sa_file):
        raise FileNotFoundError("Service account file não encontrado. Defina GOOGLE_SERVICE_ACCOUNT_FILE.")
    creds = service_account.Credentials.from_service_account_file(sa_file, scopes=SCOPES)
    service = build('calendar', 'v3', credentials=creds)
    return service

# ---------- OAUTH (usuário) ----------
def build_creds_from_allauth_token(social_token_obj):
    """
    social_token_obj: instancia allauth.socialaccount.models.SocialToken
      - .token: access token
      - .token_secret: refresh_token (varia conforme provider)
    Retorna google.oauth2.credentials.Credentials (com refresh suportado).
    """
    client_id = os.environ.get('SOCIAL_APP_CLIENT_ID')
    client_secret = os.environ.get('SOCIAL_APP_SECRET_KEY')
    if not client_id or not client_secret:
        raise RuntimeError("Defina GOOGLE_CLIENT_ID e GOOGLE_CLIENT_SECRET nas variáveis de ambiente.")

    creds = Credentials(
        token=social_token_obj.token,
        refresh_token=social_token_obj.token_secret,
        token_uri='https://oauth2.googleapis.com/token',
        client_id=client_id,
        client_secret=client_secret,
        scopes=SCOPES,
    )
    # refresha se necessário
    if not creds.valid and creds.refresh_token:
        request = Request()
        creds.refresh(request)
    return creds

def get_user_calendar_service(social_token_obj):
    creds = build_creds_from_allauth_token(social_token_obj)
    service = build('calendar', 'v3', credentials=creds)
    return service

# ---------- CRUD de eventos ----------
def create_event_on_calendar(service, calendar_id='primary', event_body=None):
    """Insere um evento e retorna o resultado."""
    if event_body is None:
        raise ValueError("event_body required")
    return service.events().insert(calendarId=calendar_id, body=event_body).execute()

def update_event_on_calendar(service, event_id, event_body, calendar_id='primary'):
    return service.events().update(calendarId=calendar_id, eventId=event_id, body=event_body).execute()

def delete_event_on_calendar(service, event_id, calendar_id='primary'):
    return service.events().delete(calendarId=calendar_id, eventId=event_id).execute()

# ---------- helpers para corpo do evento ----------
def make_event_summary(start_dt, end_dt, summary="Coleta de Lixo", description="Lembrete automático"):
    """
    start_dt / end_dt são datetime aware (ou ISO strings). Retorna dict pronto.
    Exemplo de reminders: popup 10 min antes + email 30 min antes.
    """
    # garantir ISO format com timezone: use start_dt.isoformat()
    event = {
        'summary': summary,
        'description': description,
        'start': {'dateTime': start_dt.isoformat(), 'timeZone': 'America/Sao_Paulo'},
        'end': {'dateTime': end_dt.isoformat(), 'timeZone': 'America/Sao_Paulo'},
        'reminders': {
            'useDefault': False,
            'overrides': [
                {'method': 'popup', 'minutes': 10},
                {'method': 'email', 'minutes': 30},
            ],
        },
    }
    return event

def make_recurring_event(start_dt, end_dt, rrule="RRULE:FREQ=WEEKLY;BYDAY=TU", summary="Coleta Semanal", description="Coleta recorrente"):
    event = make_event_summary(start_dt, end_dt, summary, description)
    event['recurrence'] = [rrule]
    return event
