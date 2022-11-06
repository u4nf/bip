#!/usr/bin/env python3

import requests, re
from prettytable import PrettyTable

money = 100
tick = 'BTC'

url = 'https://api.kucoin.com/api/v1/market/allTickers'
data = requests.get(url).json()['data']['ticker']

tableOut = PrettyTable()
tableOut.field_names = ['TICKER', 'QTY']
tableOut.align['QTY'] = 'l'

prospects = {}

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
			
	print('************************************************************************************************************************************')
	print(markets)
	print('************************************************************************************************************************************')

	return l1


def getSecondaryList(l1):

	#print(l1)
	for i in l1:
		index = re.search('-', i['symbol']).start()
		ticker = i['symbol'][:(index)]
		if float(i['buy']) > 0:
			qty = money / (float(i['buy']))
		prospects [ticker] = qty

l1 = getPrimaryList(tick)

getSecondaryList(l1)

for i in prospects:
	tableOut.add_row([i, prospects[i]])
print(tableOut)

