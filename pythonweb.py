
import time
import pandas as pd
import numpy as np
import json
from collections import Counter
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
import uvicorn
import requests
import json

app = FastAPI()

database = json.loads(open("database.json", "r").read())
df = pd.read_json('database.json')




def component_heroSelection(herodatabase):
    # time saved:
    # 0.07 - 0.1
    # 0.01 - 0.02
    # try:
    #     # check if component already compiled
    #     heroselection = open("components/heroselection.html", "r").read()
    #     return heroselection
    # except FileNotFoundError:
    heroselection = '<select onchange="location = this.value;">'
    heroselection += f'<option value="/"></option>'
    herodatabase = sorted(herodatabase, key=lambda k: k['localized_name'])
    for hero in herodatabase:
            heroselection += f'<option value="/{hero["id"]}">{hero["localized_name"]}</option>'
    heroselection += '</select>'
    # open("components/heroselection.html", "w").write(heroselection)
    return heroselection


# a,b,c = analysis(df, 114,106)
def analysis(df,hero,rival):#
    start = time.time()
    # calculates the winrates agresively
    findall = df[(df['winner'] == hero) & (df['looser'] == rival) | (df['winner'] == rival) & (df['looser'] == hero)]
    hardwinrate = len(findall[findall['winner'] == hero]) / len(findall) *100 
    # calculates the winrates including draws
    df['result'] = np.where(abs(df['winner_efficiency'] - df['looser_efficiency']) <= 20, 'draw', df['winner'])
    findall = df[((df['winner'] == hero) & (df['looser'] == rival)) | ((df['winner'] == rival) & (df['looser'] == hero))]
    drawwinrate = (len(findall[findall['result'] == hero]) + 0.5 * len(findall[findall['result'] == 'draw'])) / len(findall) * 100
    # calculate the average difference between the lane_efficiency_pct of the winner and the looser
    winshero = findall[df['winner'] == hero]
    compare = winshero['winner_efficiency'] - winshero['looser_efficiency']
    looseshero = findall[df['looser'] == hero]
    compare2 = looseshero['looser_efficiency'] - looseshero['winner_efficiency']
    compare = pd.concat([compare, compare2])
    mean = compare.mean()
    end = time.time()
    print(end - start)
    return hardwinrate, drawwinrate, mean

def get_hero_name(hero_id):
    for hero in herodatabase:
        if hero['id'] == hero_id:
            return hero['localized_name']
    return "Unknown"

def list_pairs(database,hero_id):
    # gets winners and looser that match the hero_id
    pairs = [(match['winner'], match['looser']) for match in database if match['winner'] == hero_id or match['looser'] == hero_id]
    # swaps the pairs so that the hero_id is always the first element
    pairs = [(a,b) if a != hero_id else (b,a) for a,b in pairs]
    counter = Counter(pairs)
    list = []
    for pair, count in sorted(counter.items(), key=lambda item: item[1], reverse=True):
        # counter object makes groups matching pairs and counts them
        # this loop sorts frequency of pairs
        a,b = pair
        list.append((a, b, count))
    return list



def component_summary(homeSummary):
    homeSummarya = homeSummary[:50]
    homeSummarya = sorted(homeSummarya, key=lambda k: k['laneWinrate'], reverse=True)
    summary = "<table>"
    summary += "<tr><th>Hero</th><th>Matches Played</th><th>Lane Winrate</th><th>Game Winrate</th></tr>"
    for hero in homeSummarya:
        summary += f"""<tr>
            <td>{get_hero_name(hero["playerID"])}</td>
            <td>{hero["matches_played"]}</td>
            <td>{hero["laneWinrate"]*100:.1f}%</td>
            <td>{hero["gameWinrate"]*100:.1f}%</td>
        </tr>"""
    summary += "</table>"
    # open("components/summary.html", "w").write(summary)
    return summary




herodatabase = json.loads(open("herodatabase.json", "r").read())
heroselection = component_heroSelection(herodatabase)


homeSummary = json.loads(open("summary.json", "r").read())
summary = component_summary(homeSummary)

dblen = len(database)
v2dblen = len([match for match in database if 'didWinnerWin' in match])





@app.get("/")
async def root():
    return HTMLResponse(content=html_content, status_code=200)



@app.get("/{hero_id}")
async def root(hero_id: int):
    hero = hero_id
    html_itemContentHero = f"this displays how well {get_hero_name(hero_id)} performs versus frequent opponents,Draw Winrate is a more rounded metric giving half score if match was close</br>"
    html_itemContentHero += "<table><tr><th>Pair</th><th>Count</th><th>Agressive Winrate</th><th>Draw Winrate</th><th>Average Efficiency Difference</th></tr>"
    for pair in list_pairs(database,hero):
        a,b,c = analysis(df, pair[1],pair[0])
        html_itemContentHero += f"<tr><td>{get_hero_name(pair[0])}</td><td>{pair[2]}</td><td>{a:.2f}%</td><td>{b:.2f}%</td><td>{c:.0f}</td></tr>"
    html_itemContentHero += "</table>"
    html_content = f"""
        <html>
            <head>
                <title>Mid lane counter info</title>
            </head>
            {style}
            <body>
                <div>
                    {intro}</br>
                    {homebutton}hero_id<br>
                    {heroselection}
                    {html_itemContentHero}
                </div>
            </body>
        </html>
        """
    aa  = html_content.replace("hero_id", f"hero_id: {get_hero_name(hero_id)}")
    return HTMLResponse(content=aa, status_code=200)




# bassic components

homebutton = """
<button onclick="location.href=\'/\'">Home</button>
"""

style = """
<style>
    body {
        background-color: #f0f0f2;
        margin: 0;
        padding: 0;
        font-family: -apple-system, system-ui, BlinkMacSystemFont, "Segoe UI", "Open Sans", "Helvetica Neue", Helvetica, Arial, sans-serif;
        
    }
    div {
        width: 600px;
        margin: 5em auto;
        padding: 2em;
        background-color: #fdfdff;
        border-radius: 0.5em;
        box-shadow: 2px 3px 7px 2px rgba(0,0,0,0.02);
    }
    a:link, a:visited {
        color: #38488f;
        text-decoration: none;
    }
    @media (max-width: 700px) {
        div {
            margin: 0 auto;
            width: auto;
        }
    }
    
</style>
"""


intro = f"""

<p>
    1. You can use this data as a counter picker:<br>
    select the hero your opponent picked and scroll to the botton to see its worst matchups
</p>
<p>
    2. You can you this data as a knowlege check for your hero:<br>
    what heroes on average beat you in lane and which heroes you beat. To be more aware how you can behave in lane without having experienced the matchup.
</p>
<p>matches in the databse   &emsp; &emsp;&emsp;:{dblen}</p>
<p>v2 matches in the databse &emsp;&emsp;:{v2dblen}</p>

"""


html_content = f"""
<html>
    <head>
        <title>Mid lane counter info</title>
    </head>
    {style}
    <body>
        <div>
            {intro}</br>
            {homebutton} hero_id<br>
            {heroselection}
            {summary}
        </div>
    </body>
</html>
"""


# uvicorn.run(app, host="0.0.0.0", port=5000)

