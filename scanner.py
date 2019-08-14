from urllib.request import urlopen, Request
from bs4 import BeautifulSoup
import texttable as tt
import datetime, time

PERIOD = 60 # seconds per refresh
GAINS_PERCENT = 20 # at least how many percent gain
MAX_LAST = 20 # maximum price
FLOAT_BTW = [2000000,15000000] # size of float
MIN_VOLUME = 50000 # minimum volume

YAHOO_FIN = 'https://finance.yahoo.com/quote/{}/key-statistics?p={}'
QUOTE_PAGE = 'http://thestockmarketwatch.com/markets/pre-market/today.aspx'
#QUOTE_PAGE2= 'https://marketchameleon.com/Reports/PremarketTrading'
GRAY = '\033[1;30;40m'
RED = '\033[1;31;40m'
GREEN = '\033[1;32;40m'
YELLOW = '\033[1;33;40m'
BLUE = '\033[1;34;40m'
MAG = '\033[1;35;40m'
CYAN = '\033[1;36;40m'
WHITE = '\033[1;37;40m'
# -------------------------------------------------------------
def print_criterias():
  print('Change% at least: {}%'.format(GAINS_PERCENT))
  print('Max Last: ${}'.format(MAX_LAST))
  print('Float between: {:,} < x < {:,}'.format(FLOAT_BTW[0],FLOAT_BTW[1]))
  print('Minimum volume: {:,}'.format(MIN_VOLUME))
def acceptable_float_size(flt):
  if flt > FLOAT_BTW[0] and flt < FLOAT_BTW[1]:
    return True
  else:
    return False
def flt_str_to_int(flt):
  flt = flt.lower()
  if 'k' in flt: # thousand
    return int(float(flt[:-1])*1000)
  elif 'm' in flt: # Million
    return int(float(flt[:-1])*1000000)
  else: # billion
    return int(float(flt[:-1])*1000000000)
def print_time_now():
  time_now = str(datetime.datetime.now())[:-7]
  print('\n{}{} {}(delayed 15 mins, stops when market opens)'.format(RED,time_now,WHITE))
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.3'}
def soup_maker(s):
  req = Request(url=s, headers=HEADERS)
  page = urlopen(req).read()
  soup = BeautifulSoup(page, 'html.parser')
  return soup
def scrape_thestockmarketwatch():
  soup = soup_maker(QUOTE_PAGE)
  track_gainers = []
  gainers = soup.find('table', {'id': 'tblMoversDesktop'})
  for td in gainers.find_all('tr')[1:]:
    perc = td.find('div', {'class':'chgUp'}).text[:-1]
    last = td.find('div', {'class':'lastPrice'}).text[1:]
    vol = td.find('td', {'class':'tdVolume'}).text
    perc = float(perc)
    last = float(last)
    vol = int(vol)
    if perc > GAINS_PERCENT and \
       last < MAX_LAST and \
       vol > MIN_VOLUME:
      track_gainers.append(td)
  return track_gainers
def filter_yahoofin(candidates):
  passed_candidates = []
  for candidate in candidates:
    ticker = candidate.find('a', {'class':'symbol'}).text
    yahoo_fin = YAHOO_FIN.format(ticker, ticker)
    soup = soup_maker(yahoo_fin)
    trs = soup.find_all('tr')
    for tr in trs:
      td = tr.find('td')
      if td:
        if 'Float' in td.text and 'Short' not in td.text:
          flt = tr.find('td', {'class':'Fz(s) Fw(500) Ta(end) Pstart(10px) Miw(60px)'}).text
    flt2 = flt_str_to_int(flt)
    if acceptable_float_size(flt2):
      passed_candidates.append((candidate,flt))
  return passed_candidates
def display(cds):
  if len(cds) == 0:
    return "No tickers match your criterias at the moment.."
  tab = tt.Texttable()
  headings = ['Ticker','Name','Last','ChgUp','Float','Vol']
  tab.header(headings)
  for (c,flt) in cds:
    chgUp = c.find('div', {'class':'chgUp'}).text
    ticker = c.find('a', {'class':'symbol'}).text
    coy_name = c.find('a', {'class':'company'}).text
    volume = c.find('td', {'class':'tdVolume'}).text
    last = c.find('div', {'class':'lastPrice'}).text
    tab.add_row([ticker,coy_name,last,chgUp,flt,volume])
  s = tab.draw()
  return s
  
# -------------------------------------------------------------
old_display = ''
while 1:
  eligible_candidates = scrape_thestockmarketwatch()
  passed_candidates = filter_yahoofin(eligible_candidates)
  new_display = display(passed_candidates)
  if new_display != old_display:
    print_time_now()
    print_criterias()
    print(new_display)
    old_display = new_display
  time.sleep(PERIOD)

