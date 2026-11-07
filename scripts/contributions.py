"""Build a profile heatmap from GitHub's contribution calendar."""
import json
import os
from datetime import date, timedelta
from pathlib import Path
from urllib.request import Request, urlopen

query = '''query($login:String!) { user(login:$login) { contributionsCollection {
  contributionCalendar { weeks { contributionDays { date weekday contributionCount contributionLevel } } }
} } }'''
request = Request('https://api.github.com/graphql', data=json.dumps({
    'query': query, 'variables': {'login': '7awwad'}
}).encode(), headers={'Authorization': 'Bearer ' + os.environ['GH_TOKEN'], 'Content-Type': 'application/json'})
with urlopen(request, timeout=30) as response:
    payload = json.load(response)
if payload.get('errors'):
    raise ValueError(payload['errors'])
weeks = payload['data']['user']['contributionsCollection']['contributionCalendar']['weeks']
colors = dict(zip(['NONE','FIRST_QUARTILE','SECOND_QUARTILE','THIRD_QUARTILE','FOURTH_QUARTILE'],
                  ['#282945','#545185','#837ac4','#b1b2ed','#bcf0ff']))
counts = {}
cells = []
labels = []
last_month = None
for column, week in enumerate(weeks):
    for day in week['contributionDays']:
        when = date.fromisoformat(day['date'])
        count = day['contributionCount']
        counts[when] = count
        x = 22 + column * 17
        y = 85 + day['weekday'] * 17
        if when.month != last_month and (column < len(weeks)-2):
            labels.append(f'<text x="{x}" y="73">{when:%b}</text>')
            last_month = when.month
        cells.append(f'<rect x="{x}" y="{y}" width="13" height="13" rx="3" fill="{colors[day["contributionLevel"]]}"><title>{when}: {count} contributions</title></rect>')
today = max(counts)
cursor = today if counts[today] else today - timedelta(days=1)
current = 0
while counts.get(cursor, 0):
    current += 1
    cursor -= timedelta(days=1)
best = run = 0
for when in sorted(counts):
    run = run + 1 if counts[when] else 0
    best = max(run, best)
width = 44 + len(weeks)*17
svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} 257"><title>GitHub contribution map through {today}</title>
<rect width="100%" height="100%" rx="14" fill="#15162d"/><g font-family="monospace" fill="#d5d9f4">
<text x="22" y="38" font-size="22">Contribution calendar</text><text x="{width-22}" y="38" text-anchor="end" font-size="15">{today:%d %b %Y}</text>
<g font-size="13">{''.join(labels)}</g>{''.join(cells)}
<text x="22" y="235" font-size="16">{sum(counts.values())} contributions   ·   Current streak: {current} days   ·   Best in view: {best} days</text></g></svg>'''
Path('assets/contributions.svg').write_text(svg+'\n', encoding='utf-8')
