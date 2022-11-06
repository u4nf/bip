#! /home/u4nf/dev/bip/bin/python3

import requests, re
from prettytable import PrettyTable

money = 100
tick = 'USDT'

url = 'https://api.kucoin.com/api/v1/market/allTickers'
data = requests.get(url).json()['data']['ticker']
fee = 0.001


prospects = {}
paths = []


def getPrimaryList(tick):
	#returns list of pairs that have multiple markets (not "SHITCOIN-USDT"), ensure arb is possible
	l1 = [] 
	markets = {}

	for i in data:

		if bool(re.search(tick, i['symbol'])):
			#ensure is variable 'tick' is in the ticker pair

			index = re.search('-', i['symbol']).start()
			base = i['symbol'][:index]

			counter = 0
			temp = {}

			for j in data:
				#ensure the base token has multiple markets

				if bool(re.search('^' + base + '-', j['symbol'])):
					temp[j['symbol']] = {'buy': j['buy'], 'sell': j['sell']}
					counter +=1

			if counter > 2:
				markets[base] = temp
				l1.append(i)

	return l1, markets


def getAllPaths(markets):

	#iterate over each ticker and construct a path to BTC then USDT
	for i in markets:

		#iterate over pairs associated with ticker
		for j in markets[i]:

			#check for BTC pair
			if i + '-BTC' in markets[i]:
				
				#create temp object containing path
				tempPath = {i:{}}

				#simulate initial trade from USDT to Token
				fromUSDT = money / float(markets[i][i + '-USDT']['buy'])
				#deduct trading fee
				fromUSDT -= fromUSDT * fee
				tempPath[i]['fromUSDT'] = fromUSDT

				#simulate trade from token to BTC
				toBTC = fromUSDT * float(markets[i][i + '-BTC']['buy'])
				#deduct trading fee
				toBTC -= toBTC * fee
				tempPath[i]['toBTC'] = toBTC

				#simulate trade from BTC to USDT
				toUSDT = toBTC * float(markets['BTC']['BTC-USDT']['buy'])
				#deduct trading fee
				toUSDT -= toUSDT * fee
				tempPath[i]['toUSDT'] = toUSDT

				#add to path
				paths.append(tempPath)

				break

		
def createTable():

	tableOut = PrettyTable()
	tableOut.field_names = ['TICKER', 'From USDT', 'To  BTC', 'To USDT']
	tableOut.align['From USDT'] = 'l'
	tableOut.align['To  BTC'] = 'l'
	tableOut.align['To USDT'] = 'l'

	for i in paths:
		print(i)
		for tempTicker in i.keys():
			ticker = tempTicker 

		tableOut.add_row([ticker, i[ticker]['fromUSDT'], i[ticker]['toBTC'], i[ticker]['toUSDT']])

	print(tableOut)


l1, markets = getPrimaryList(tick)

getAllPaths(markets)
createTable()






"""
#create table
for i in prospects:
	tableOut.add_row([i, prospects[i]])
print(tableOut)
"""
