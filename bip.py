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

	def getPath(token, second):
		#returns an object simulating a path USDT > xxx > xxx > USDT

		#create temp object containing path
		tempPath = {}

		#simulate initial trade from USDT to Token
		fromUSDT = money / float(markets[token][token + '-USDT']['buy'])
		#deduct trading fee
		fromUSDT -= fromUSDT * fee
		tempPath['fromUSDT'] = fromUSDT

		#simulate trade from token to "second"
		toSecond = fromUSDT * float(markets[token][token + '-' + second]['buy'])
		#deduct trading fee
		toSecond -= toSecond * fee
		tempPath['toSecond'] = toSecond

		#simulate trade from "second" back to USDT
		toUSDT = toSecond * float(markets[second][second + '-USDT']['buy'])
		#deduct trading fee
		toUSDT -= toUSDT * fee
		tempPath['toUSDT'] = toUSDT

		return tempPath


	#iterate over each ticker and construct a path to BTC then USDT
	#first = first trade from USDT
	#second = following trade (BTC / ETH / KCS)
	for token in markets:
		tempHolder = {token: {}}

		
		#skip USDT-USDC
		if token in ['USDT', 'USDC']:
			continue
		
	
		if token + '-BTC' in markets[token]:
			btc = getPath(token, 'BTC')
			tempHolder[token]['BTC'] = btc
		
		if token + '-ETH' in markets[token]:
			eth = getPath(token, 'ETH')
			tempHolder[token]['ETH'] = eth

		if token + '-KCS' in markets[token]:
			kcs = getPath(token, 'KCS')
			tempHolder[token]['KCS'] = kcs

		"""
		if token + '-USDC' in markets[token]:
			usdc = getPath(token, 'USDC')
			tempHolder[token]['USDC'] = usdc
		"""

		#add all found paths to paths object
		paths.append(tempHolder)

		
def createTable():

	tableOut = PrettyTable()
	tableOut.field_names = ['TICKER', 'SECONDARY', 'From USDT', 'To  SECONDARY', 'To USDT']
	tableOut.align['From USDT'] = 'l'
	tableOut.align['To  SECONDARY'] = 'l'
	tableOut.align['To USDT'] = 'l'

	for i in paths:
		
		#iterate over tokens
		for tempTicker in i.keys():
			ticker = tempTicker
			
			#iterate over pairs in token
			for secondToken in i[ticker]:
				fromUSDT = i[ticker][secondToken]['fromUSDT']
				tokenToSecond = i[ticker][secondToken]['toSecond']
				toUSDT = i[ticker][secondToken]['toUSDT']

				tableOut.add_row([ticker, secondToken, fromUSDT, tokenToSecond, toUSDT])

	print(tableOut)


l1, markets = getPrimaryList(tick)

getAllPaths(markets)
createTable()
