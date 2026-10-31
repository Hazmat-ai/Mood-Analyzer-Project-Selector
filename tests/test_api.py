import sqlite3
import uuid
from concurrent.futures import ThreadPoolExecutor
import pytest
from app import create_app

ORIGIN='http://localhost:5000'
BODY={'specialty':'software','answer_indexes':[0]*7,'difficulty':'easy'}

def login(client):
    response=client.get('/api/session',base_url=ORIGIN)
    assert response.status_code==200
    return {'Origin':ORIGIN,'X-CSRF-Token':response.json['csrf_token'],'Idempotency-Key':str(uuid.uuid4())}

def submit(client,headers,body=None):
    return client.post('/api/submit-quiz',base_url=ORIGIN,json=BODY if body is None else body,headers=headers)

def test_session_isolation_completion_and_reopening(client,application):
    headers=login(client); picked=submit(client,headers)
    assert picked.status_code==200
    data=picked.json;assert data['result']['id'] in {p['id'] for p in data['candidates']}
    outsider=application.test_client();other_headers=login(outsider)
    assert outsider.get('/api/history',base_url=ORIGIN).json==[]
    assert outsider.get('/api/picks/'+data['pick_id'],base_url=ORIGIN).status_code==404
    assert outsider.post('/api/complete',base_url=ORIGIN,json={'pick_id':data['pick_id']},headers=other_headers).status_code==404
    assert client.post('/api/complete',base_url=ORIGIN,json={'pick_id':data['pick_id']},headers=headers).status_code==200
    saved=client.get('/api/picks/'+data['pick_id'],base_url=ORIGIN).json
    assert saved['completed'] is True
    assert saved['result']['title']==data['result']['title']
    assert 'mood_vector' not in client.get('/api/export',base_url=ORIGIN).json['picks'][0]

def test_idempotent_quiz_retry_and_payload_conflict(client):
    headers=login(client)
    first=submit(client,headers).json;second=submit(client,headers).json
    assert first['pick_id']==second['pick_id']
    assert first['result']==second['result']
    assert len(client.get('/api/history',base_url=ORIGIN).json)==1
    assert submit(client,headers,{**BODY,'difficulty':'hard'}).status_code==409

def test_concurrent_retry_creates_one_pick(client,application):
    headers=login(client);cookie=client.get_cookie('mood_session').value
    def send(_):
        with application.test_client() as c:
            c.set_cookie('mood_session',cookie,domain='localhost')
            response=submit(c,headers);assert response.status_code==200
            return response.json['pick_id']
    with ThreadPoolExecutor(max_workers=4) as pool:
        ids=list(pool.map(send,range(4)))
    assert len(set(ids))==1

@pytest.mark.parametrize('answers',[[True]*7,[-1]*7,[999]*7,[0]*6,[0]*8,['0']*7,[{}]*7,None])
def test_rejects_invalid_answer_types_and_bounds(client,answers):
    assert submit(client,login(client),{**BODY,'answer_indexes':answers}).status_code==400

@pytest.mark.parametrize('data',[[],None,{'specialty':[],'answer_indexes':[0]*7,'difficulty':'easy'},{**BODY,'unexpected':'field'},{**BODY,'difficulty':'nope'}])
def test_exact_body_schema(client,data):
    headers=login(client)
    response=client.post('/api/submit-quiz',base_url=ORIGIN,data=__import__('json').dumps(data),content_type='application/json',headers=headers)
    assert response.status_code==400

def test_csrf_origin_content_type_and_limit(client):
    headers=login(client)
    assert submit(client,{**headers,'X-CSRF-Token':'wrong'}).status_code==403
    assert submit(client,{**headers,'Origin':'https://attacker.example'}).status_code==403
    assert submit(client,{k:v for k,v in headers.items() if k!='Origin'}).status_code==403
    assert client.post('/api/submit-quiz',base_url=ORIGIN,headers=headers,data='{}',content_type='text/plain').status_code==415
    assert client.post('/api/submit-quiz',base_url=ORIGIN,headers=headers,data='{broken',content_type='application/json').status_code==400
    assert client.post('/api/submit-quiz',base_url=ORIGIN,headers=headers,data='x'*5000,content_type='application/json').status_code==413
    assert client.post('/api/complete',base_url=ORIGIN,headers=headers,json={'pick_id':'fake','project_title':'spoofed'}).status_code==400

def test_host_and_security_headers(client):
    assert client.get('/api/quiz',base_url='http://evil.example').status_code==421
    response=client.get('/api/health',base_url=ORIGIN)
    assert response.status_code==200
    assert response.headers['X-Content-Type-Options']=='nosniff'
    assert "frame-ancestors 'none'" in response.headers['Content-Security-Policy']
    assert response.headers['Cache-Control']=='no-store'

def test_export_delete_and_expiration(client,application):
    headers=login(client);submit(client,headers)
    assert len(client.get('/api/export',base_url=ORIGIN).json['picks'])==1
    assert client.delete('/api/history',base_url=ORIGIN,headers=headers).status_code==200
    assert client.get('/api/history',base_url=ORIGIN).json==[]
    submit(client,{**headers,'Idempotency-Key':str(uuid.uuid4())})
    assert client.delete('/api/session',base_url=ORIGIN,headers=headers).status_code==200
    assert client.get('/api/history',base_url=ORIGIN).status_code==401
    with sqlite3.connect(application.config['DATABASE']) as db:
        assert db.execute('SELECT count(*) FROM picks').fetchone()[0]==0
    login(client)
    with sqlite3.connect(application.config['DATABASE']) as db:db.execute('UPDATE sessions SET expires=0')
    assert client.get('/api/history',base_url=ORIGIN).status_code==401

def test_history_survives_app_restart(client,application):
    headers=login(client);data=submit(client,headers).json;raw=client.get_cookie('mood_session').value
    restarted=create_app({'DATABASE':application.config['DATABASE'],'TESTING':True}).test_client()
    restarted.set_cookie('mood_session',raw,domain='localhost')
    assert restarted.get('/api/history',base_url=ORIGIN).json[0]['id']==data['pick_id']

def test_static_boundaries_and_missing_api(client):
    assert client.get('/',base_url=ORIGIN).status_code==200
    assert client.get('/missing.js',base_url=ORIGIN).status_code==404
    assert client.get('/../app.py',base_url=ORIGIN).status_code in (400,404)
    login(client)
    assert client.get('/api/missing',base_url=ORIGIN).status_code==404

def test_production_cookie_and_config(tmp_path):
    with pytest.raises(RuntimeError):create_app({'PRODUCTION':True,'APP_ORIGIN':'http://localhost:5000','DATABASE':str(tmp_path/'bad.sqlite')})
    app=create_app({'PRODUCTION':True,'APP_ORIGIN':'https://example.test','DATABASE':str(tmp_path/'prod.sqlite')})
    response=app.test_client().get('/api/session',base_url='https://example.test')
    value=response.headers['Set-Cookie']
    for part in ('__Host-mood=', 'Secure','HttpOnly','SameSite=Strict','Path=/'):assert part in value

def test_rate_limit_and_authenticated_proxy(tmp_path):
    app=create_app({'DATABASE':str(tmp_path/'rate.sqlite'),'RATE_LIMIT':1,'PROXY_TOKEN':'a'*64})
    c=app.test_client();headers={'X-Real-IP':'192.0.2.1','X-Mood-Proxy-Token':'a'*64}
    assert c.get('/api/quiz',base_url=ORIGIN,headers=headers).status_code==200
    assert c.get('/api/quiz',base_url=ORIGIN,headers=headers).status_code==429
    assert c.get('/api/quiz',base_url=ORIGIN,headers={**headers,'X-Real-IP':'192.0.2.2'}).status_code==200
    assert c.get('/api/quiz',base_url=ORIGIN,headers={'X-Real-IP':'192.0.2.3'}).status_code==200
    assert c.get('/api/quiz',base_url=ORIGIN,headers={'X-Real-IP':'192.0.2.4'}).status_code==429

def test_creation_quota_does_not_block_existing_session(tmp_path):
    app=create_app({'DATABASE':str(tmp_path/'quota.sqlite'),'SESSION_CREATION_LIMIT':1})
    a=app.test_client();login(a)
    assert app.test_client().get('/api/session',base_url=ORIGIN).status_code==429
    assert a.get('/api/session',base_url=ORIGIN).status_code==200

def test_backup_restore_round_trip(client,application,tmp_path):
    from scripts.backup import backup
    headers=login(client);picked=submit(client,headers).json
    raw=client.get_cookie('mood_session').value
    destination=tmp_path/'snapshot.sqlite'
    backup(application.config['DATABASE'],destination)
    with pytest.raises(ValueError):backup(application.config['DATABASE'],destination)
    app=create_app({'DATABASE':str(destination),'TESTING':True})
    restored=app.test_client();restored.set_cookie('mood_session',raw,domain='localhost')
    assert restored.get('/api/history',base_url=ORIGIN).json[0]['id']==picked['pick_id']

def test_history_retention_is_bounded_and_completion_is_per_pick(client):
    headers=login(client)
    first=submit(client,headers).json
    second=submit(client,{**headers,'Idempotency-Key':str(uuid.uuid4())}).json
    client.post('/api/complete',base_url=ORIGIN,json={'pick_id':first['pick_id']},headers=headers)
    history=client.get('/api/history',base_url=ORIGIN).json
    by_id={item['id']:item for item in history}
    assert by_id[first['pick_id']]['completed'] is True
    assert by_id[second['pick_id']]['completed'] is False
    for _ in range(199):
        assert submit(client,{**headers,'Idempotency-Key':str(uuid.uuid4())}).status_code==200
    assert len(client.get('/api/history',base_url=ORIGIN).json)==200
