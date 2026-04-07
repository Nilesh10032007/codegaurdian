import requests
base = 'http://localhost:7860'

r1 = requests.post(base + '/reset', json={})
print('reset:', r1.status_code, r1.json().keys())

r2 = requests.get(base + '/state')
print('state:', r2.status_code, r2.json())

action = {'action':'flag_bug','line':4,'comment':'hello','bug_type':'syntax_error'}
r3 = requests.post(base + '/step', json=action)
print('step1:', r3.status_code, r3.json())

action2 = {'action':'approve','comment':'done'}
r4 = requests.post(base + '/step', json=action2)
print('step2 (approve):', r4.status_code, r4.json())
