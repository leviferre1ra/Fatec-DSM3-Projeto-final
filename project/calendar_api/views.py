# calendar_api/views.py
from django.shortcuts import redirect
from django.http import JsonResponse, HttpResponseForbidden
from allauth.socialaccount.models import SocialToken
from .utils.google_calendar import get_user_calendar_service, make_event_summary, make_recurring_event, create_event_on_calendar, update_event_on_calendar, delete_event_on_calendar
import datetime

from django.shortcuts import redirect
from allauth.socialaccount.models import SocialToken

def require_auth_redirect(request):
    # se não estiver logado → redireciona
    if not request.user.is_authenticated:
        return None, redirect('/accounts/google/login/')

    # pegar token Google
    token = SocialToken.objects.filter(
        account__user=request.user,
        account__provider='google'
    ).first()

    if not token:
        return None, redirect('/accounts/google/login/')

    return token, None


def create_event(request):
    token, redirect_response = require_auth_redirect(request)

    if redirect_response:
        return redirect_response  # impede erro

    service = get_user_calendar_service(token)

    # Exemplo: criar evento amanhã às 09:00 por 1h
    start = datetime.datetime.now() + datetime.timedelta(days=1)
    start = start.replace(hour=9, minute=0, second=0, microsecond=0)
    end = start + datetime.timedelta(hours=1)

    event_body = make_event_summary(start, end,
                                   summary="Coleta de Lixo Agendada",
                                   description="Lembrete do De Olho no Lixo.")

    res = create_event_on_calendar(service, calendar_id='primary', event_body=event_body)
    return JsonResponse({'status': 'ok', 'id': res.get('id'), 'link': res.get('htmlLink')})

def schedule_weekly(request):
    token = require_auth_redirect(request)
    service = get_user_calendar_service(token)

    # calcular próxima terça às 9:00
    today = datetime.date.today()
    # Exemplo: definir BYDAY com base na necessidade
    next_tuesday = today + datetime.timedelta(days=(1 - today.weekday()) % 7)
    start = datetime.datetime.combine(next_tuesday, datetime.time(9, 0))
    end = start + datetime.timedelta(hours=1)
    event_body = make_recurring_event(start, end, rrule="RRULE:FREQ=WEEKLY;BYDAY=TU")
    res = create_event_on_calendar(service, calendar_id='primary', event_body=event_body)
    return JsonResponse({'status': 'ok', 'id': res.get('id'), 'link': res.get('htmlLink')})

def update_event(request, event_id):
    token = require_auth_redirect(request)
    service = get_user_calendar_service(token)
    # aqui você receberia dados do request (start/end/summary). Demo simples:
    # vamos apenas mover o evento 1h para frente
    event = service.events().get(calendarId='primary', eventId=event_id).execute()

    import dateutil.parser

    start = dateutil.parser.isoparse(event['start']['dateTime'])
    end = dateutil.parser.isoparse(event['end']['dateTime'])
    new_start = start + datetime.timedelta(hours=1)
    new_end = end + datetime.timedelta(hours=1)
    event['start']['dateTime'] = new_start.isoformat()
    event['end']['dateTime'] = new_end.isoformat()
    updated = update_event_on_calendar(service, event_id, event, calendar_id='primary')
    return JsonResponse({'status': 'ok', 'updated': updated.get('id')})

def delete_event(request, event_id):
    token = require_auth_redirect(request)
    service = get_user_calendar_service(token)
    delete_event_on_calendar(service, event_id, calendar_id='primary')
    return JsonResponse({'status': 'ok', 'deleted': event_id})
