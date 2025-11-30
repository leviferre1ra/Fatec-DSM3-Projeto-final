# calendar_api/views.py
from django.shortcuts import redirect
from django.http import JsonResponse, HttpResponseForbidden
from allauth.socialaccount.models import SocialToken
from .utils.google_calendar import get_user_calendar_service, make_event_summary, make_recurring_event, create_event_on_calendar, update_event_on_calendar, delete_event_on_calendar
import datetime
import json
try:
    from zoneinfo import ZoneInfo
except Exception:
    ZoneInfo = None

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
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'redirect': redirect_response.url}, status=401)
        return redirect_response  # impede erro

    service = get_user_calendar_service(token)

    # Tentar obter payload JSON ou form-data (compatibilidade)
    payload = {}
    try:
        if request.content_type and request.content_type.startswith('application/json'):
            payload = json.loads(request.body.decode('utf-8') or '{}')
        else:
            payload = request.POST
    except Exception:
        payload = {}

    # Suporta três formatos de entrada:
    # - payload['datetime'] : ISO8601
    # - payload['date'] (dd/mm/yyyy) e payload['time'] (HH:MM)
    start = None
    try:
        if payload and payload.get('datetime'):
            import dateutil.parser
            start = dateutil.parser.isoparse(payload.get('datetime'))
        elif payload and payload.get('date') and payload.get('time'):
            # espera dd/mm/yyyy e HH:MM
            date_str = payload.get('date')
            time_str = payload.get('time')
            day, month, year = map(int, date_str.split('/'))
            hour, minute = map(int, time_str.split(':'))
            start = datetime.datetime(year, month, day, hour, minute)
    except Exception:
        start = None

    if not start:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
            return JsonResponse({'error': 'Data ou horário inválido(es). Forneça date (dd/mm/yyyy) e time (HH:MM) ou datetime ISO.'}, status=400)
        return HttpResponseForbidden('Data ou horário inválido(es).')

    end = start + datetime.timedelta(hours=1)

    event_body = make_event_summary(start, end,
                                   summary="Coleta de Lixo Agendada",
                                   description="Lembrete do De Olho no Lixo.")

    try:
        import dateutil.parser
        tz = None
        if ZoneInfo is not None:
            try:
                tz = ZoneInfo('America/Sao_Paulo')
            except Exception:
                tz = None

        if start.tzinfo is None and tz is not None:
            start_check = start.replace(tzinfo=tz)
        else:
            start_check = start
        if end.tzinfo is None and tz is not None:
            end_check = end.replace(tzinfo=tz)
        else:
            end_check = end

        time_min = start_check.isoformat()
        time_max = end_check.isoformat()

        existing = service.events().list(
            calendarId='primary',
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy='startTime',
            q=event_body.get('summary')
        ).execute()
        items = existing.get('items', [])
        for ev in items:
            ev_summary = ev.get('summary', '')
            ev_start = ev.get('start', {}).get('dateTime')
            if not ev_start:
                continue
            try:
                ev_start_dt = dateutil.parser.isoparse(ev_start)
            except Exception:
                continue
            if ev_start_dt.tzinfo is None and tz is not None:
                ev_start_dt = ev_start_dt.replace(tzinfo=tz)

            ev_ts = ev_start_dt.astimezone(datetime.timezone.utc).timestamp()
            try:
                start_ts = start_check.astimezone(datetime.timezone.utc).timestamp()
            except Exception:
                continue
            if ev_summary == event_body.get('summary') and abs(ev_ts - start_ts) < 60:
                return JsonResponse({'status': 'exists', 'id': ev.get('id'), 'link': ev.get('htmlLink')}, status=409)
    except Exception:
        pass

    res = create_event_on_calendar(service, calendar_id='primary', event_body=event_body)
    return JsonResponse({'status': res.get('status'), 'id': res.get('id'), 'link': res.get('htmlLink')})

def schedule_weekly(request):
    token, redirect_response = require_auth_redirect(request)

    # tratar redirect/auth similar a create_event
    if redirect_response:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'redirect': redirect_response.url}, status=401)
        return redirect_response

    service = get_user_calendar_service(token)

    # receber payload JSON (espera { days: [...], date: 'dd/mm/yyyy', time: 'HH:MM' })
    payload = {}
    try:
        if request.content_type and request.content_type.startswith('application/json'):
            payload = json.loads(request.body.decode('utf-8') or '{}')
        else:
            payload = request.POST
    except Exception:
        payload = {}

    # extrair days (aceita lista de códigos BYDAY, índices 0..6, ou nomes em pt/en)
    raw_days = None
    if isinstance(payload, dict):
        raw_days = payload.get('days')
    elif hasattr(payload, 'getlist'):
        try:
            raw_days = payload.getlist('days')
        except Exception:
            raw_days = None

    # normalizar string -> list
    if isinstance(raw_days, str):
        try:
            raw_days = json.loads(raw_days)
        except Exception:
            raw_days = [d.strip() for d in raw_days.split(',') if d.strip()]

    dayCodeMap = ['SU','MO','TU','WE','TH','FR','SA']
    dia_map = {'domingo':'SU','segunda':'MO','terca':'TU','quarta':'WE','quinta':'TH','sexta':'FR','sabado':'SA'}

    bydays = []
    if isinstance(raw_days, (list, tuple)):
        for d in raw_days:
            if d is None:
                continue
            # números 0..6
            try:
                if isinstance(d, (int, float)) or (isinstance(d, str) and d.isdigit()):
                    idx = int(d)
                    if 0 <= idx <= 6:
                        code = dayCodeMap[idx]
                        if code not in bydays: bydays.append(code)
                        continue
            except Exception:
                pass
            s = str(d).strip()
            up = s.upper()
            if up in ['MO','TU','WE','TH','FR','SA','SU']:
                if up not in bydays: bydays.append(up); continue
            # tentar nomes em portugues
            try:
                import unicodedata
                key = unicodedata.normalize('NFD', s.lower())
                key = ''.join(ch for ch in key if not unicodedata.combining(ch))
                if key in dia_map:
                    code = dia_map[key]
                    if code not in bydays: bydays.append(code)
            except Exception:
                continue

    # aceitar também payload.date + payload.time (date no formato dd/mm/yyyy)
    start = None
    try:
        if payload and payload.get('datetime'):
            import dateutil.parser
            start = dateutil.parser.isoparse(payload.get('datetime'))
        elif payload and payload.get('date') and payload.get('time'):
            date_str = payload.get('date')
            time_str = payload.get('time')
            day, month, year = map(int, date_str.split('/'))
            hour, minute = map(int, time_str.split(':'))
            start = datetime.datetime(year, month, day, hour, minute)
    except Exception:
        start = None

    # se não vier start, escolher próximo dia do primeiro byday (ou erro se não tiver days)
    if not start:
        if not bydays:
            return JsonResponse({'error': 'Nenhum dia fornecido. Envie days como lista de dias.'}, status=400)
        # map byday code to weekday number (Monday=0..Sunday=6)
        code_to_wd = {'MO':0,'TU':1,'WE':2,'TH':3,'FR':4,'SA':5,'SU':6}
        first_code = bydays[0]
        today = datetime.date.today()
        target_wd = code_to_wd.get(first_code, 0)
        days_ahead = (target_wd - today.weekday() + 7) % 7
        if days_ahead == 0:
            days_ahead = 7
        d = today + datetime.timedelta(days=days_ahead)
        # default time 09:00
        start = datetime.datetime.combine(d, datetime.time(9,0))

    end = start + datetime.timedelta(hours=1)

    # construir RRULE
    rrule = f"RRULE:FREQ=WEEKLY;BYDAY={','.join(bydays)}"
    event_body = make_recurring_event(start, end, rrule=rrule, summary="Coleta de Lixo Agendada", description="Lembrete do De Olho no Lixo.")

    # checar duplicados: procurar eventos com mesma summary e recurrence contendo mesmo BYDAY e horário
    try:
        existing = service.events().list(calendarId='primary', singleEvents=False, q=event_body.get('summary')).execute()
        items = existing.get('items', [])
        import dateutil.parser
        tz = None
        if ZoneInfo is not None:
            try:
                tz = ZoneInfo('America/Sao_Paulo')
            except Exception:
                tz = None

        for ev in items:
            ev_summary = ev.get('summary','')
            if ev_summary != event_body.get('summary'):
                continue
            recs = ev.get('recurrence') or []
            matched = False
            for r in recs:
                if 'BYDAY' in r:
                    # extrair BYDAY parte
                    part = r.split('BYDAY=')[-1]
                    ev_by = part.split(';')[0]
                    ev_by_list = [x.strip() for x in ev_by.split(',') if x.strip()]
                    if set(ev_by_list) == set(bydays):
                        matched = True
                        break
            if not matched:
                continue
            # comparar horário de início
            ev_start = ev.get('start', {}).get('dateTime')
            if not ev_start:
                continue
            try:
                ev_start_dt = dateutil.parser.isoparse(ev_start)
            except Exception:
                continue
            if ev_start_dt.tzinfo is None and tz is not None:
                ev_start_dt = ev_start_dt.replace(tzinfo=tz)
            # comparar horas/minutos
            if ev_start_dt.hour == start.hour and ev_start_dt.minute == start.minute:
                return JsonResponse({'status':'exists','id': ev.get('id'),'link': ev.get('htmlLink')}, status=409)
    except Exception:
        pass

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
