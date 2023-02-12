#! /home/u4nf/dev/bip3/bin/python3

import requests, datetime, re, os, math
from prettytable import PrettyTable

#user defined variables
money = 100.00

#exchange fee
fee = 0.001
#0.1 is 10% profit per trade
#minProfitPercent = 0.002
minProfitPercent = 0.00
#API URL
url = 'https://api.kucoin.com/api/v1/market/allTickers'
#orderbook API
orderbook = "https://api.kucoin.com/api/v1/market/orderbook/level2_20?symbol="
#File containing pairs list
pairsFile = "kuCoinPairs.txt"
#prefferred currency
tick = 'USDT'
#common pairs (save searching)
commonPairsList = ['BTC-USDT', 'ETH-USDT', 'KCS-USDT']
logFile = './log.txt'

paths = []

def log(dataToLog, destination = 0):

	#log details to console (destination = 0) or file (destination = 1)

	timestamp = datetime.datetime.now().strftime("%Y-%b-%d - %H:%M:%S.%f")

	#write to file
	if destination == 1:
		with open(logFile, 'a') as f:

			#delimiter
			if dataToLog == 1:
				f.write('\n*******************************************************')
				return

			#log to console
			f.write(f'\n{timestamp} --- {dataToLog}')
		return	

    #delimiter
	if dataToLog == 1:
		print('*******************************************************')
		return
	
	#log to console
	print(f'{timestamp} --- {dataToLog}')


def getAPIData(url):
	#gets and checks API data, returns json

	data = requests.get(url)

	#verify good response from API
	if data.status_code != 200:
		print('Bad response - status ' + str(data.status_code))
		exit()

	#format response
	data = data.json()['data']['ticker']

	return data


def getPathList():

	def getMarkets(data):

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

		return markets

	def getOutputPaths(markets):

		outputPaths = []

		for token in markets:

			#skip USDT-USDC
			if token in ['USDT', 'USDC']:
				continue

			for pair in ['-BTC', '-ETH', '-KCS']:

				if token + pair in markets[token]:
					pathList = [token + '-' + tick]
					pathList.append(token + pair)
					pathList.append(pair[1:] + '-' + tick)
					outputPaths.append(pathList)

		return outputPaths


	data = getAPIData(url)
	markets = getMarkets(data)
	pathsList = getOutputPaths(markets)

	return pathsList


def getCommonPairPrices(commonPairs, data):

	tempCommonPairs = {}

	for i in commonPairs:
		tempCommonPairs[i] = {}

		for j in data:
			if j['symbol'] == i:
				tempCommonPairs[i]['buy'] = j['buy']
				tempCommonPairs[i]['sell'] = j['sell']
	
	return tempCommonPairs


def deductTradeFee(input, decimals):
	#returns the input amount minus the fee, rounded as appropriate
	feeToDeduct = input - (input * fee)

	return round(feeToDeduct, decimals)


def getTradeData(path, data):
	#Creates object containing path, buy and sell rates for each pair

	tradeData = {}
	tempPairslist = []
	
	for i, j in enumerate(path):
		
		tempPairslist.append(j)
		tradeData[i] = {}
		tradeData[i]['pair'] = j

		for k in data:

			#stores BTC-USDT as float in exponential form.  Need to convert to nominal prior to adding to report
			if k['symbol'] == j:
				tradeData[i]['buy'] = float(k['buy'])

				tradeData[i]['sell'] = float(k['sell'])


	tradeData['pairs'] = tempPairslist

	return tradeData


def surfaceProfitable(tradeData, percent, money):
	#returns a list of trades that are profitable

	#calculate token qty after trade 0
	tradeData[0]['afterTradeQty'] = deductTradeFee(money / tradeData[0]['sell'], 8)

	#calculate token qty after trade 1
	tradeData[1]['afterTradeQty'] = deductTradeFee(tradeData[0]['afterTradeQty'] * tradeData[1]['sell'], 8)

	#calculate USDT qty after trade 2
	tradeData[2]['afterTradeQty'] = deductTradeFee(tradeData[1]['afterTradeQty'] * tradeData[2]['sell'], 2)

	#calculate profit details
	tradeData['profit'] = {}
	tradeData['profit']['USDT in'] = money
	tradeData['profit']['USDT out'] = tradeData[2]['afterTradeQty']
	tradeData['profit']['netProfit'] = round(tradeData['profit']['USDT out'] - tradeData['profit']['USDT in'], 2)
	tradeData['profit']['profitPercentage'] = round((tradeData['profit']['netProfit'] / tradeData['profit']['USDT in']) * 100, 4)

	#return details if profitable on the surface
	if tradeData['profit']['profitPercentage'] > minProfitPercent:
		return tradeData
	else:

		return 'Not Surface Profitable'


def isProfitable(input):

	def getOrderbookData(pair):
		#gets orderbook data to 20 places, returns json

		log(f'Getting API DATA for {pair}')
		data = requests.get(orderbook + pair)
		log('Got API DATA')


		#verify good response from API
		if data.status_code != 200:
			print('Bad response - status ' + str(data.status_code))
			exit()

		#format response
		data = data.json()
		return data


	def checkLiquidityL1(amountIn, orderbook, askOrBid, pairName, index):

		l1Price = float(orderbook['data'][askOrBid][0][0])
		l1Qty = float(orderbook['data'][askOrBid][0][1])

		if index == 0:
			WantToBuy = round(amountIn / l1Price, 8)

			if (amountIn / l1Price) < l1Qty:
				
				#add to transaction bundle
				transactionBundle[index] = {'pair':pairName, 'qtyToBuy':WantToBuy, 'price':l1Price}
				return transactionBundle

			else:
				return 'Insufficient liquidity'


		elif index == 1:
			WantToBuy = round(amountIn * l1Price, 8)

			if amountIn < l1Qty:
				
				#add to transaction bundle
				transactionBundle[index] = {'pair':pairName, 'qtyToBuy':WantToBuy, 'price':l1Price}
				#print(f'Pair {pairName}, amountIn {amountIn}, want to buy {WantToBuy}, qty available at l1 {round(l1Qty * l1Price, 8)}')
				return transactionBundle

			else:
				#print(f'Pair {pairName}, amountIn {amountIn}, want to buy {WantToBuy}, qty available at l1 {l1Qty}')
				return 'Insufficient liquidity'


		elif index == 2:
			WantToBuy = round(amountIn * l1Price, 8)

			if amountIn < l1Qty:
				
				#add to transaction bundle
				transactionBundle[index] = {'pair':pairName, 'qtyToBuy':WantToBuy, 'price':l1Price}
				#print(f'Pair {pairName}, amountIn {amountIn}, want to buy {WantToBuy}, qty available at l1 {round(l1Qty * l1Price, 8)}')
				return transactionBundle

			else:
				#print(f'Pair {pairName}, amountIn {amountIn}, want to buy {WantToBuy}, qty available at l1 {l1Qty}')
				return 'Insufficient liquidity'


	#list of dictionaries to build transaction requests from
	transactionBundle = [{}, {}, {}]

	#first time this is being simulated, use var "money" as amount in
	firstRun = True
	amountIn = money

	profitCalc = {'input': amountIn, 'output': 0, 'profitUSDT': 0, 'profitPercent': 0}


	for i, j in enumerate(input['pairs']):
		pairName = j
		index = i

		#determine if we are calculating based on USDT in (from prior confirmed trade) or we are continuing the simulated calculation
		if not firstRun:
			amountIn = transactionBundle[i-1]['qtyToBuy']

		firstRun = False
		
		orderbookData = getOrderbookData(j)
		orderbookData['pair'] = j

		#alternate between bid / ask
		#1st trade (from USDT) use asks, 2nd trade (to BTC / ETH / KCC) needs to use bids
		if i == 0 or i == 2:
			askOrBid = 'asks'

		elif i == 1:
			askOrBid = 'bids'

		qtyBought = checkLiquidityL1(amountIn, orderbookData, askOrBid, pairName, index)

		if qtyBought == 'Insufficient liquidity':
			return 'Insufficient liquidity', -1


	profitCalc['output'] = transactionBundle[2]['qtyToBuy']
	profitCalc['profitUSDT'] = round(profitCalc['output'] - profitCalc['input'], 4) 
	profitCalc['profitPercent'] = round(profitCalc['profitUSDT'] / profitCalc['input'], 4)

	#If profitable at L1
	if profitCalc['profitPercent'] > minProfitPercent:
		log('PROFITABLE TRADE -----  LOGGED TO FILE')
		log(1,1)
		log(f"PROFITABLE TRADE %{profitCalc['profitPercent']}",1)
		log(f"PAIRS   - {input['pairs']}", 1)
		log(f'PROFIT  - {profitCalc}', 1)
		log(f'DETAILS - {transactionBundle}', 1)

		return(transactionBundle, profitCalc)
	else:
		log(transactionBundle)
		log(profitCalc)
		return f"Not Profitable -- %{profitCalc['profitPercent']}", -1




os.system("clear")
pathsList = getPathList()


while True:
	#get raw data
	log(1)
	log('GETTING INITIAL API DATA')
	data = getAPIData(url)
	log('GOT INITIAL API DATA')

	#get surface prices of BTC/ETH/KCS to minimise lookups
	commonPairs = getCommonPairPrices(commonPairsList, data)

	for i in pathsList:

		tradeData = getTradeData(i, data)

		#check to see if potentially profitable
		tempSurfaceProfitable = surfaceProfitable(tradeData, minProfitPercent, money)

		#check if profitable taking int account the current orderbook
		if tempSurfaceProfitable != 'Not Surface Profitable':

			log(1)
			log(f"checking {tempSurfaceProfitable['pairs']}")
			log(f"Surface profit = %{tempSurfaceProfitable['profit']['profitPercentage']}")

			profitable, profitCalc = isProfitable(tempSurfaceProfitable)
			log(profitable)


			

	#l1, markets = getPrimaryList(tick)

	#getAllPaths(markets)

	#profitable = surfaceProfitable(paths, minProfitPercent)

	#OutputTable = createTable(profitable)

	#print(OutputTable)
	paths = []






#Probably won't need these

"""
#*************************

def calculateDepth(amountIn, orderbook, askOrBid):
		tradingBalance = amountIn
		qtyBought = 0

		#keep track of how many levels deep in the orderbook
		levels = -1
		
		tempHolder = []

		print(orderbook['pair'])
		print(f'AmountIn = {amountIn}')
		print(askOrBid)
		print(orderbook['data'][askOrBid])

		for level in orderbook['data'][askOrBid]:


			levelPrice = float(level[0])
			levelAvailableQty = float(level[1])
			
			#value measured in QUOTE currency (ie: TONE/UDST - levelValue measured in USDT)
			levelValue = levelPrice * levelAvailableQty


			if tradingBalance - levelValue < 0:
				qtyBought += tradingBalance / levelPrice
				tradingBalance = 0

			else:
				tradingBalance -= levelValue				
				qtyBought += levelAvailableQty

			levels += 1
			tempHolder.append(f'value at level {levels} ({levelAvailableQty}) tokens = {levelValue} >> bought {qtyBought} tokens // Trading balance remaining = {tradingBalance}')

			if tradingBalance <= 0:
				for i in tempHolder:
					print(i)

				print('*******************************')
				break

			elif levels == 19:
				print('Insuficient liquidity')
				
				for i in tempHolder:
					print(i)
				
				return -1

		return qtyBought


def reformatOrderbook(asks, bids, direction):
		# if b2q, orderbook reformatted to show qty as USDT 
		# ie:
		# TONE-USDT
		# org - ['0.01439', '701.9717'] - 701.9717 TONE available at 0.01439 USDT
		# adj - [69.49270326615705, 10.101372763] - 10.101 USDT in value at this level

		adjAsks = []
		adjBids = bids

		if direction == 'b2q':
			for i in asks:
				askPrice = float(i[0])
				adjPrice = 1 / askPrice
				adjQty = float(i[1]) * askPrice
				adjAsks.append([adjPrice, adjQty])
		
		return adjAsks, adjBids


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

		# if token + '-USDC' in markets[token]:
		# 	usdc = getPath(token, 'USDC')
		# 	tempHolder[token]['USDC'] = usdc


		#add all found paths to paths object
		paths.append(tempHolder)

		
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


#*************************

"""