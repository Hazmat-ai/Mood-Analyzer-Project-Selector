import json
from datetime import datetime
from pathlib import Path

checks=json.loads(Path('docs/release-signoff.json').read_text())
problems=[]
for name in ('uat','securityReview','deploymentSmoke','restoreDrill','contentReview'):
    item=checks.get(name,{})
    try:datetime.fromisoformat(item.get('date') or '')
    except (ValueError,TypeError):problems.append(name+': valid review date required')
    if item.get('approved') is not True or not item.get('reviewer') or not item.get('evidence'):
        problems.append(name+': human signoff and evidence required')
if not Path('frontend/dist/index.html').is_file():problems.append('Production frontend build missing')
if problems:raise SystemExit('RELEASE BLOCKED\n'+'\n'.join(problems))
print('Recorded human gates present. Deploy only the exact tested release candidate.')
