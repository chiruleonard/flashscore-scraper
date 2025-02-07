#!/usr/bin/env python

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

from bs4 import BeautifulSoup

import datetime
import json
import os
import random
import re
import time


# Create an empty list to store all match_ids
match_ids = []

# Path to where is stored match_ids
path = os.getcwd() + r'\prerequisite\json.txt'

# Open .txt file in read mode and create a list with all match_ids
with open(path, 'r') as match_ids_results:
    for line in match_ids_results.readlines():
        match_ids.append(line.strip())

# Create an empty list to store all dict matches
data_processed = []

# Create a dictionary to store each data
def emtpy_dict_data():
    global data
    data = {}

    data['match_id'] = None
    data['country'] = None
    data['league'] = None
    data['round'] = None
    data['date'] = None
    data['HomeTeam'] = {'name':None,
                        'formation':None}
    data['AwayTeam'] = {'name':None,
                        'formation':None}
    data['referee'] = None
    data['venue'] = None
    data['capacity'] = None
    data['attendance'] = None
    data['status'] = None
    data['EndTime'] = None
    data['score'] = {'fullTime':{
                        'HomeTeam':None,
                        'AwayTeam':None},
                    'halfTime':{
                        'HomeTeam':None,
                        'AwayTeam':None},
                    'extraTime':{
                        'HomeTeam':None,
                        'AwayTeam':None},
                    'penalties':{
                        'HomeTeam':None,
                        'AwayTeam':None}
                    }
    data['odds'] = {'1':None,
                    'X':None,
                    '2':None}
    data['goals'] = []
    data['cards'] = []
    data['subs'] = []
    data['man_of_the_match'] = None
    data['commentary'] = None
    data['lineup'] = {'HomeTeam':[],
                    'AwayTeam':[]}
    data['FT'] = {'HomeTeam':{},
                'AwayTeam':{}
                }
    data['H1'] = {'HomeTeam':{},
                'AwayTeam':{}
                }
    data['H2'] = {'HomeTeam':{},
                'AwayTeam':{}
                }
    data['extraTime'] = {'HomeTeam':{},
                'AwayTeam':{}
                }
    return data

def match_summary(driver):
    soup = BeautifulSoup(driver.page_source, features="html.parser")
    # Country, League, Round, Date
    variable = soup.find('span', attrs={'class':'tournamentHeader__country'}).text

    data['country'] = variable.split(': ')[0].title()
    data['league'] = variable.split(': ')[-1].split(' - ')[0]
    data['round'] = variable.split(': ')[-1].split(' - ', 1)[-1]

    date_v = soup.find('div', attrs={'class':'duelParticipant__startTime'}).text
    data['date'] = datetime.datetime.strptime(date_v, '%d.%m.%Y %H:%M').isoformat()

    # Home and Away team
    data['HomeTeam']['name'] = soup.find('div', attrs={"class": re.compile('^duelParticipant__home')}).text
    data['AwayTeam']['name'] = soup.find('div', attrs={"class": re.compile('^duelParticipant__away')}).text

    # Save info in a variable
    raw = soup.find('div', attrs={'class':re.compile('^wcl-summaryMatchInformation_')})

    # Referee
    if raw.find_all('div', attrs={'class': re.compile('^wcl-infoLabelWrapper_')})[0].text == 'Referee:':
        data['referee'] = raw.find_all('div', attrs={'class': re.compile('^wcl-infoValue_')})[0].text.replace('\xa0', ' ')
    
    # Venue:
    if raw.find_all('div', attrs={'class': re.compile('^wcl-infoLabelWrapper_')})[1].text == 'Venue:':
        data['venue'] = raw.find_all('div', attrs={'class': re.compile('^wcl-infoValue_')})[1].text
    
    # Capacity:
    if raw.find_all('div', attrs={'class': re.compile('^wcl-infoLabelWrapper_')})[2].text == 'Capacity:':
        data['capacity'] = int(raw.find_all('div', attrs={'class': re.compile('^wcl-infoValue_')})[2].text.replace(' ', ''))
    
    # # Attendance:
    try:
        if raw.find_all('div', attrs={'class': re.compile('^wcl-infoLabelWrapper_')})[3].text == 'Attendance:':
            data['attendance'] = int(raw.find_all('div', attrs={'class': re.compile('^wcl-infoValue_')})[3].text.replace(' ', ''))
    except:
        pass

    # Status
    data['status'] = soup.find('span', attrs={'class':'fixedHeaderDuel__detailStatus'}).text

    # Results
    try:
        data['score']['fullTime']['HomeTeam'] = int(soup.find('div', attrs={'class':'detailScore__wrapper'}).text.split('-')[0].replace("(",""))
        data['score']['fullTime']['AwayTeam'] = int(soup.find('div', attrs={'class':'detailScore__wrapper'}).text.split('-')[-1].replace(")",""))
    except:
        try:
            data['score']['fullTime']['HomeTeam'] = int(soup.find('div', attrs={'class':'detailScore__wrapper'}).text.split('-')[0])
            data['score']['fullTime']['AwayTeam'] = int(soup.find('div', attrs={'class':'detailScore__wrapper'}).text.split('-')[-1])
        except:
            data['score']['fullTime']['HomeTeam'] = None
            data['score']['fullTime']['AwayTeam'] = None

    results = soup.find_all('div', attrs={'class':'smv__incidentsHeader section__title'})
    for i in results:
        if i.div.text == '1st Half':
            data['score']['halfTime']['HomeTeam'] = int(i.find_all('div')[1].text.split(' - ')[0])
            data['score']['halfTime']['AwayTeam'] = int(i.find_all('div')[1].text.split(' - ')[1])
        elif i.div.text == 'Extra Time':
            data['score']['extraTime']['HomeTeam'] = int(i.find_all('div')[1].text.split(' - ')[0])
            data['score']['extraTime']['AwayTeam'] = int(i.find_all('div')[1].text.split(' - ')[1])
        elif i.div.text == 'Penalties':
            data['score']['penalties']['HomeTeam'] = int(i.find_all('div')[1].text.split(' - ')[0])
            data['score']['penalties']['AwayTeam'] = int(i.find_all('div')[1].text.split(' - ')[1])

    # Odds for Win, Draw, and Lose
    try:
        data['odds']['1'] = float(soup.find_all('span', attrs={'class':'oddsValueInner'})[0].text)
    except:
        pass
    try:
        data['odds']['X'] = float(soup.find_all('span', attrs={'class':'oddsValueInner'})[1].text)
    except:
        pass
    try:
        data['odds']['2'] = float(soup.find_all('span', attrs={'class':'oddsValueInner'})[2].text)
    except:
        pass

def match_summary_goals(driver):
    soup = BeautifulSoup(driver.page_source, features="html.parser")
    incidentRows = soup.find_all('div', attrs={'class':re.compile('smv__participantRow')})

    for r in incidentRows:
        try:
            if r.find('svg')['data-testid'] == "wcl-icon-soccer":
                event = {'minute':None, 'player':None, 'assist':None, 'team':None}

                event['minute'] = r.find('div', attrs={'class':'smv__timeBox'}).text

                # Player
                try:
                    event['player'] = r.find('a', attrs={'class':'smv__playerName'})['href'].split('/')[2].replace('-', ' ').title()
                except:
                    pass

                # Assist
                try:
                    event['assist'] = r.find('div', attrs={'class':'smv__assist'}).a['href'].split('/')[2].replace('-', ' ').title()
                except:
                    pass
                try:
                    event['assist'] = r.find('div', attrs={'class':'smv__subIncident'}).text.replace('(','').replace(')','')
                except:
                    pass

                # Teams
                try:
                    if 'home' == re.search('(home)', r['class'][-1]).group(1):
                        event['team'] = soup.find('div', attrs={'class':'duelParticipant__home'}).find('div', attrs={'class':'participant__participantName participant__overflow'}).text
                except:
                    pass
                try:
                    if 'away' == re.search('(away)', r['class'][-1]).group(1):
                        event['team'] = soup.find('div', attrs={'class':'duelParticipant__away'}).find('div', attrs={'class':'participant__participantName participant__overflow'}).text
                except:
                    pass

                data['goals'].append(event)
        except:
            pass

def match_summary_cards(driver):
    soup = BeautifulSoup(driver.page_source, features="html.parser")
    incidentRows = soup.find_all('div', attrs={'class':re.compile('smv__participantRow')})

    for r in incidentRows:
        try:
            if r.find('svg')['class'][0] == "card-ico":
                event = {'minute':None, 'player':None, 'type':None, 'action':None, 'team':None}

                event['minute'] = r.find('div', attrs={'class':'smv__timeBox'}).text
                try:
                    event['player'] = r.find('a', attrs={'class':'smv__playerName'})['href'].split('/')[2].replace('-', ' ').title()
                except:
                    pass

                event['type'] = r.find('svg')['class'][-1][:-4]

                try:
                    event['action'] = r.find('div', attrs={'class':'smv__subIncident'}).text.replace('(','').replace(')','')
                except:
                    pass

                # Teams
                try:
                    if 'home' == re.search('(home)', r['class'][-1]).group(1):
                        event['team'] = soup.find('div', attrs={'class':'duelParticipant__home'}).find('div', attrs={'class':'participant__participantName participant__overflow'}).text
                except:
                    pass
                try:
                    if 'away' == re.search('(away)', r['class'][-1]).group(1):
                        event['team'] = soup.find('div', attrs={'class':'duelParticipant__away'}).find('div', attrs={'class':'participant__participantName participant__overflow'}).text
                except:
                    pass

                data['cards'].append(event)
        except:
            pass

def match_summary_subs(driver):
    soup = BeautifulSoup(driver.page_source, features="html.parser")
    incidentRows = soup.find_all('div', attrs={'class':re.compile('smv__participantRow')})

    for r in incidentRows:
        try:
            if re.search('(Sub)', r.find('div', attrs={'class':'smv__incidentIconSub'})['class'][0]).group(1) == 'Sub':
                event = {'minute':None, 'in':None, 'out':None, 'team':None}

                event['minute'] = r.find('div', attrs={'class':'smv__timeBox'}).text
                try:
                    event['in'] = r.find_all('a', attrs={'class':'smv__playerName'})[0]['href'].split('/')[2].replace('-', ' ').title()
                except:
                    pass

                try:
                    event['out'] = r.find_all('a', attrs={'class':'smv__playerName'})[1]['href'].split('/')[2].replace('-', ' ').title()
                except:
                    #event['out'] = r.find('div', attrs={'class':re.compile("^subDown")}).text
                    pass

                # Teams
                try:
                    if 'home' == re.search('(home)', r['class'][-1]).group(1):
                        event['team'] = soup.find('div', attrs={'class':'duelParticipant__home'}).find('div', attrs={'class':'participant__participantName participant__overflow'}).text
                except:
                    pass
                try:
                    if 'away' == re.search('(away)', r['class'][-1]).group(1):
                        event['team'] = soup.find('div', attrs={'class':'duelParticipant__away'}).find('div', attrs={'class':'participant__participantName participant__overflow'}).text
                except:
                    pass

                data['subs'].append(event)
        except:
            pass

def reports(driver):
    soup = BeautifulSoup(driver.page_source, features="html.parser")
    
    ps = soup.find('div', attrs={'class': 'fsNewsArticle__content'})
    data['man_of_the_match'] = ps.text.strip().split('\n')[-1].split(': ')[-1]

def match_lineups(driver):
    soup = BeautifulSoup(driver.page_source, features="html.parser")

    try:
        data['HomeTeam']['formation'] = soup.find_all('span', attrs={'class':'lf__headerPart'})[0].text
        data['AwayTeam']['formation'] = soup.find_all('span', attrs={'class':'lf__headerPart'})[-1].text
    except:
        pass

    sections = soup.find('div', attrs={'class':'lf__lineUp'})

    for section in sections.find_all('div', attrs={'class':'section'}):
        if section.find('div', attrs={'class', re.compile('^section__title')}).text == "Starting Lineups":
            home_players = section.find_all("div", attrs={'class': 'lf__side'})[0]
            away_players = section.find_all("div", attrs={'class': 'lf__side'})[-1]

            # Home players
            for player in home_players:
                event = {'jersey':None, 'nationality':None, 'name':None, 'rating':None, 'status':None}
    
                event['jersey'] = int(player.find("span", attrs={"data-testid": "wcl-scores-simpleText-01"}).text)
                event['nationality'] = player.find("img", attrs={"data-testid": "wcl-assetContainerBoxFree-XS"})["alt"]
                event['name'] = player.find("a", attrs={"data-testid": "wcl-textLink"})['href'].split('/')[2].replace('-', ' ').title()
                try:
                    event['rating'] = float(player.find("span", attrs={"data-testid": "wcl-scores-caption-03"}).text)
                except:
                    pass
                event['status'] = "line-up"

                data['lineup']['HomeTeam'].append(event)

            # Away players
            for player in away_players:
                event = {'jersey':None, 'nationality':None, 'name':None, 'rating':None, 'status':None}

                event['jersey'] = int(player.find("span", attrs={"data-testid": "wcl-scores-simpleText-01"}).text)
                event['nationality'] = player.find("img", attrs={"data-testid": "wcl-assetContainerBoxFree-XS"})["alt"]
                event['name'] = player.find("a", attrs={"data-testid": "wcl-textLink"})['href'].split('/')[2].replace('-', ' ').title()
                try:
                    event['rating'] = float(player.find("span", attrs={"data-testid": "wcl-scores-caption-03"}).text)
                except:
                    pass
                event['status'] = "line-up"

                data['lineup']['AwayTeam'].append(event)

        if section.find('div', attrs={'class', re.compile('^section__title')}).text == "Substituted players":
            home_players = section.find_all("div", attrs={'class': 'lf__side'})[0]
            away_players = section.find_all("div", attrs={'class': 'lf__side'})[-1]

            # Home players
            for player in home_players:
                event = {'jersey':None, 'nationality':None, 'name':None, 'rating':None, 'status':None}
    
                try:
                    event['jersey'] = int(player.find("span", attrs={"data-testid": "wcl-scores-simpleText-01"}).text)
                except:
                    pass
                try:
                    event['nationality'] = player.find("img", attrs={"data-testid": "wcl-assetContainerBoxFree-XS"})["alt"]
                except:
                    pass
                event['name'] = player.find("a", attrs={"data-testid": "wcl-textLink"})['href'].split('/')[2].replace('-', ' ').title()
                try:
                    event['rating'] = float(player.find("span", attrs={"data-testid": "wcl-scores-caption-03"}).text)
                except:
                    pass
                event['status'] = "subs"

                data['lineup']['HomeTeam'].append(event)

            # Away players
            for player in away_players:
                event = {'jersey':None, 'nationality':None, 'name':None, 'rating':None, 'status':None}
    
                try:
                    event['jersey'] = int(player.find("span", attrs={"data-testid": "wcl-scores-simpleText-01"}).text)
                except:
                    pass
                try:
                    event['nationality'] = player.find("img", attrs={"data-testid": "wcl-assetContainerBoxFree-XS"})["alt"]
                except:
                    pass
                event['name'] = player.find("a", attrs={"data-testid": "wcl-textLink"})['href'].split('/')[2].replace('-', ' ').title()
                try:
                    event['rating'] = float(player.find("span", attrs={"data-testid": "wcl-scores-caption-03"}).text)
                except:
                    pass
                event['status'] = "subs"

                data['lineup']['AwayTeam'].append(event)

        if section.find('div', attrs={'class', re.compile('^section__title')}).text == "Substitutes":
            home_players = section.find_all("div", attrs={'class': 'lf__side'})[0]
            away_players = section.find_all("div", attrs={'class': 'lf__side'})[-1]

            # Home players
            for player in home_players:
                event = {'jersey':None, 'nationality':None, 'name':None, 'status':None}
    
                event['jersey'] = int(player.find("span", attrs={"data-testid": "wcl-scores-simpleText-01"}).text)
                event['nationality'] = player.find("img", attrs={"data-testid": "wcl-assetContainerBoxFree-XS"})["alt"]
                event['name'] = player.find("a", attrs={"data-testid": "wcl-textLink"})['href'].split('/')[2].replace('-', ' ').title()
                event['status'] = "subs"

                data['lineup']['HomeTeam'].append(event)

            # Away players
            for player in away_players:
                event = {'jersey':None, 'nationality':None, 'name':None, 'status':None}

                event['jersey'] = int(player.find("span", attrs={"data-testid": "wcl-scores-simpleText-01"}).text)
                event['nationality'] = player.find("img", attrs={"data-testid": "wcl-assetContainerBoxFree-XS"})["alt"]
                event['name'] = player.find("a", attrs={"data-testid": "wcl-textLink"})['href'].split('/')[2].replace('-', ' ').title()
                event['status'] = "subs"

                data['lineup']['AwayTeam'].append(event)

        if section.find('div', attrs={'class', re.compile('^section__title')}).text == "Missing Players":
            home_players = section.find_all("div", attrs={'class': 'lf__side'})[0]
            away_players = section.find_all("div", attrs={'class': 'lf__side'})[-1]

            # Home players
            for player in home_players:
                event = {'jersey':None, 'nationality':None, 'name':None, 'status':None}

                event['nationality'] = player.find("img", attrs={"data-testid": "wcl-assetContainerBoxFree-XS"})["alt"]
                event['name'] = player.find("a", attrs={"data-testid": "wcl-textLink"})['href'].split('/')[2].replace('-', ' ').title()
                event['status'] = player.find("span", attrs={"data-testid": "wcl-scores-caption-05"}).text

                data['lineup']['HomeTeam'].append(event)

            # Away players
            for player in away_players:
                event = {'jersey':None, 'nationality':None, 'name':None, 'status':None}

                event['nationality'] = player.find("img", attrs={"class": re.compile("^_assetContainer_1nfae_4")})["alt"]
                event['name'] = player.find("a", attrs={"class": re.compile("^_link_1ctg9_4")})['href'].split('/')[2].replace('-', ' ').title()
                event['status'] = player.find("span", attrs={"data-testid": "wcl-scores-caption-05"}).text
                
                data['lineup']['AwayTeam'].append(event)


        if section.find('div', attrs={'class', re.compile('^section__title')}).text == "Coaches":
            home_players = section.find_all("div", attrs={'class': 'lf__side'})[0]
            away_players = section.find_all("div", attrs={'class': 'lf__side'})[-1]

            # Home players
            for player in home_players:
                event = {'jersey':None, 'nationality':None, 'name':None, 'status':None}

                event['nationality'] = player.find("img", attrs={"class": re.compile("^_assetContainer_1nfae_4")})["alt"]
                event['name'] = player.find("a", attrs={"class": re.compile("^_link_1ctg9_4")})['href'].split('/')[2].replace('-', ' ').title()
                event['status'] = "coach"

                data['lineup']['HomeTeam'].append(event)

            # Away players
            for player in away_players:
                event = {'jersey':None, 'nationality':None, 'name':None, 'status':None}

                event['nationality'] = player.find("img", attrs={"class": re.compile("^_assetContainer_1nfae_4")})["alt"]
                event['name'] = player.find("a", attrs={"class": re.compile("^_link_1ctg9_4")})['href'].split('/')[2].replace('-', ' ').title()
                event['status'] = "coach"

                data['lineup']['AwayTeam'].append(event)

def statistics(p, t, driver):
    soup = BeautifulSoup(driver.page_source, features="html.parser")
    
    for i in soup.find_all('div', attrs={'data-testid':'wcl-statistics'}):
        stats_name = i.find('div', attrs={'data-testid': 'wcl-statistics-category'}).text
        data[p]['HomeTeam'][stats_name] = i.find_all('div', attrs={'data-testid': 'wcl-statistics-value'})[0].text
        data[p]['AwayTeam'][stats_name] = i.find_all('div', attrs={'data-testid': 'wcl-statistics-value'})[-1].text

def match_commentary(driver):
    # Match EndTime
    soup = BeautifulSoup(driver.page_source, features="html.parser")
    data['EndTime'] = soup.find('div', attrs={'data-testid':'wcl-commentary-headline-text'}).text

    # Commentary
    minutes = []
    comments = []

    for event in soup.find_all('div', attrs={'data-testid': 'wcl-commentary'}):
        try:
            minutes.append(event.find('strong', attrs={'data-testid': 'wcl-scores-simpleText-02'}).text.replace("'", ""))
        except:
            minutes.append('0')
    
        try:
            comments.append(event.find('div', attrs={'class': re.compile('^wcl-general_')}).text)
        except:
            pass
        try:
            comments.append(event.find('div', attrs={'class': re.compile('^wcl-highlighted_')}).text)
        except:
            pass
        try:
            comments.append(event.find('div', attrs={'class': re.compile('^wcl-live_')}).text)
        except:
            pass

        events = list(zip(minutes, comments))
        events.reverse()
        
        data['commentary'] = events

def main():
    # Open Chrome
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')  # Last I checked this was necessary.
    options.add_argument('--log-level=3') # Remove information from console

    #driver = webdriver.Chrome(service=Service(ChromeDriverManager(version="114.0.5735.90").install()), options=options)
    #driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager(version="114.0.5735.90").install()), options=options)
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
    

    x = 0
    for match_id in match_ids:
        print('Current match: ' + str(match_id) + '\t' + 'Remaining: ' + str(len(match_ids) - 1 - x))

        url = 'https://www.flashscore.com/match/' + match_id + "/#match-summary"

        driver.get(url)
        time.sleep(1)

        # Accept GDPR
        try:
            driver.find_element(by='id', value='onetrust-accept-btn-handler').click()
        except:
            pass

        # Click on the Match tab to start scrapping
        try:
            driver.find_element(by='xpath', value="//a[@href='#/match-summary']").click()
            time.sleep(1.5)
        except:
            pass

        # Create empty dictionary to store data
        emtpy_dict_data()

        # Get Match ID
        data['match_id'] = match_id

        # Match summary (Goals, Cards, Substitutions)
        time.sleep(1)
        match_summary(driver)

        try:
            match_summary_goals(driver)
        except:
            pass
        try:
            match_summary_cards(driver)
        except:
            pass
        try:
            match_summary_subs(driver)
        except:
            pass

        # Match statistics
        try:
            driver.find_element(by='xpath', value="//a[@href='#/match-summary/match-statistics']").click()
            time.sleep(1.5)
            ft = BeautifulSoup(driver.page_source, features="html.parser")
            statistics('FT', ft, driver)

            driver.find_element(by='xpath', value="//a[@href='#/match-summary/match-statistics/1']").click()
            time.sleep(1.5)
            h1 = BeautifulSoup(driver.page_source, features="html.parser")
            statistics('H1', h1, driver)

            driver.find_element(by='xpath', value="//a[@href='#/match-summary/match-statistics/2']").click()
            time.sleep(1.5)
            h2 = BeautifulSoup(driver.page_source, features="html.parser")
            statistics('H2', h2, driver)
        except:
            pass

        # Match statistics for Extra Time
        try:
            driver.find_element(by='xpath', value="//a[@href='#/match-summary/match-statistics/3']").click()
            time.sleep(1.5)
            et = BeautifulSoup(driver.page_source, features="html.parser")
            statistics('extraTime', et, driver)
        except:
            pass

        # Match line-up
        try:
            driver.find_element(by='xpath', value="//a[@href='#/match-summary/lineups']").click()
            time.sleep(1.5)
            match_lineups(driver)
        except:
            pass

        # Match EndTime
        try:
            driver.find_element(by='xpath', value="//a[@href='#/match-summary/live-commentary']").click()
            time.sleep(1.5)
            match_commentary(driver)
        except:
            pass

        # Man of the match
        try:
            driver.find_element(by='xpath', value="//a[@href='#/report']").click()
            time.sleep(1.5)
            reports(driver)
        except:
            pass

        data_processed.append(data)
        x += 1

    yesterday = datetime.datetime.now() - datetime.timedelta(days=1)

    with open(os.getcwd() + r'\processed' + '\\' + str(yesterday.date()) + '.json', 'w') as json_file:
        json.dump(data_processed, json_file)

if __name__ == '__main__':
    main()
