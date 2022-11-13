#! /home/u4nf/dev/bip/bin/python3

import requests, re
from prettytable import PrettyTable

#user defined variables
money = 100.00
tick = 'USDT'
#exchange fee
fee = 0.001
#0.1 is 10% profit per trade
minProfitPercent = 0.001
#API URL
url = 'https://api.kucoin.com/api/v1/market/allTickers'



def getInitailAPIData(url):
	#gets and checks API data, returns json

	data = requests.get(url)

	#verify good response from API
	if data.status_code != 200:
		print('Bad response - status ' + str(data.status_code))
		exit()

	#format response
	data = data.json()['data']['ticker']

	return data




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
		tempPath['fromUSDT'] = round(fromUSDT, 8)

		#simulate trade from token to "second"
		toSecond = fromUSDT * float(markets[token][token + '-' + second]['buy'])
		#deduct trading fee
		toSecond -= toSecond * fee
		tempPath['toSecond'] = round(toSecond, 8)

		#simulate trade from "second" back to USDT
		toUSDT = toSecond * float(markets[second][second + '-USDT']['buy'])
		#deduct trading fee
		toUSDT -= toUSDT * fee
		tempPath['toUSDT'] = round(toUSDT, 4)

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

		
def selectProfitable(paths, percent):
	#returns a list of trades that are profitable
	profitable = []

	for i in paths:

		#iterate over provided token paths
		for tempTicker in i.keys():
			ticker = tempTicker

			#iterate over each secondary pair
			for second in i[ticker]:
				outputOfTrade = i[ticker][second]['toUSDT']
				
				#check to see if trade exceeds the profit threshold
				profit = outputOfTrade - money
		
				if profit > (money * percent):
					
					#create object for list
					profitablePath = {ticker: {second: i[ticker][second]}}

					profitPercentage = round((profit / money) * 100, 4)
					profitablePath[ticker][second]['percent'] = profitPercentage

					profitable.append(profitablePath)
					
	return profitable


def createTable(input):

	tableOut = PrettyTable()
	tableOut.field_names = ['TICKER', 'SECONDARY', 'From USDT', 'To  SECONDARY', 'To USDT', '% Profit']
	tableOut.align['From USDT'] = 'l'
	tableOut.align['To  SECONDARY'] = 'l'
	tableOut.align['To USDT'] = 'l'
	tableOut.align['% Profit'] = 'l'

	#sort table
	tableOut.sortby = "% Profit"
	tableOut.reversesort = True

	for i in input:
		
		#iterate over tokens
		for tempTicker in i.keys():
			ticker = tempTicker
			
			#iterate over pairs in token
			for secondToken in i[ticker]:
				fromUSDT = i[ticker][secondToken]['fromUSDT']
				tokenToSecond = i[ticker][secondToken]['toSecond']
				toUSDT = i[ticker][secondToken]['toUSDT']
				percent = i[ticker][secondToken]['percent']

				tableOut.add_row([ticker, secondToken, fromUSDT, tokenToSecond, toUSDT, percent])

	return tableOut

data = getInitailAPIData(url)

l1, markets = getPrimaryList(tick)

getAllPaths(markets)

profitable = selectProfitable(paths, minProfitPercent)

OutputTable = createTable(profitable)

print(OutputTable)