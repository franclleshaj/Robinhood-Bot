import sys
sys.path.insert(0, "c:\python38\lib\site-packages")
import os
import robin_stocks.robinhood as rs
from numpy.lib.function_base import average
import matplotlib.pyplot as plt
import time
import smtplib
from email.message import EmailMessage

# login process
robin_user = os.environ.get("robinhood_username")
robin_pass = os.environ.get("robinhood_password")
rs.authentication.login(username=robin_user, password=robin_pass, expiresIn=86400, scope='internal', by_sms=True,
                        store_session=True)
phone_number = os.environ.get("phone_number")

# user information is presented
firstName = rs.profiles.load_user_profile('first_name')
lastName = rs.profiles.load_user_profile('last_name')
print('\nUser:', firstName, lastName)
buyingPower = round(
    float(rs.profiles.load_account_profile('crypto_buying_power')), 2)
print('Buying power: $', buyingPower, '\n')

# class that stores information about the asset in question, including quantity owned, price histroy, one and three month moving averages and standard deviations


class assetClass:
   def __init__(self, quantity, priceHistory, oneMonthAvg, oneMonthStd, threeMonthAvg, threeMonthStd):
      self.quantity = quantity
      self.priceHistory = priceHistory
      self.oneMonthAvg = oneMonthAvg
      self.oneMonthStd = oneMonthStd
      self.threeMonthAvg = threeMonthAvg
      self.threeMonthStd = threeMonthStd


# truncates price to 2 decimal places
def truncatePrice(price):
   a = str(price)
   index = a.index('.') + 3

   return float(a[:index])


# sends email alerts to recipient of your choice
def emailAlert(subject, body, to):
   # the email's contents, including its subject, body, and receiver, are set
   msg = EmailMessage()
   msg.set_content(body)
   msg['subject'] = subject
   msg['to'] = to

   # the email adress that is sending the email is set
   user = os.environ.get('alerts_email')
   msg['from'] = user
   pas = os.environ.get('alerts_email_password')

   # the function logs in the email adress and uses it to send the email to the receiver
   server = smtplib.SMTP('smtp.gmail.com', 587)
   server.starttls()
   server.login(user, pas)
   server.send_message(msg)

   server.quit()

# function that is used to get the price history, one and three month moving averages and standard deviations for cryptocurrencies
def updateCryptoPriceInfo(ticker):

   # price data is collected from robinhood and converted from a list of strings to float values
   priceHistory = rs.crypto.get_crypto_historicals(
       ticker, interval='day', span='5year', bounds='24_7', info='close_price')
   priceHistory = [float(price) for price in priceHistory]

   # processed data will be stored in these lists, which will then be returned by the function
   oneMonthAvg, oneMonthStd, threeMonthAvg, threeMonthStd = [], [], [], []

   # robinhood data is processed, each loop iteration processes data for each day
   # i starts at 30 because 30 days is the minimum amount of time required to computed the 30 day moving average and standard deviation
   i = 30
   while i < len(priceHistory):

      # if statement decides when to compute the 30 day moving average along with the 30 day standard deviation
      if i >= 30:
         oneMonthAvg.append(sum(priceHistory[i - 30:i]) / 30)
         # this loop calculates 30 day standard deviation
         j, summ = i - 31, 0
         while j < i:
            summ += (priceHistory[j] - oneMonthAvg[i - 30]) ** 2
            j += 1
         oneMonthStd.append((summ / 30) ** .5)

      # if statement decides when to compute the 30 day moving average along with the 90 day standard deviation
      if i >= 90:
         threeMonthAvg.append(sum(priceHistory[i - 90:i]) / 90)
         # this loop calculates 30 day standard deviation
         j, summ = i - 91, 0
         while j < i:
            summ += (priceHistory[j] - oneMonthAvg[i - 90]) ** 2
            j += 1
         threeMonthStd.append((summ / 90) ** .5)
      i += 1

   return [priceHistory, oneMonthAvg, oneMonthStd, threeMonthAvg, threeMonthStd]

# function used to get the price history, one and three month moving average of a stock, it is not used in this program
def updateStockPriceInfo(ticker):

   # price data is collected from robinhood
   priceHistory = rs.stocks.get_stock_historicals(
       ticker, interval='day', span='5year', bounds='regular', info='close_price')

   priceHistory = [float(price) for price in priceHistory]

   # processed data will be stored in these lists, which will then be returned by the function
   oneMonthAvg, oneMonthStd, threeMonthAvg, threeMonthStd = [], [], [], []

   # robinhood data is processed, each loop iteration computes data for each day
   i = 0
   while i < len(priceHistory):

      # if statement decides when to compute the 30 day moving average along with the 30 day standard deviation
      if i >= 30:
         oneMonthAvg.append(sum(priceHistory[i - 30:i]) / 30)
         # this loop calculates 30 day standard deviation
         j, summ = i - 30, 0
         while j < i:
            summ += (priceHistory[j] - oneMonthAvg[i - 30]) ** 2
            j += 1
         oneMonthStd.append((summ / 30) ** .5)

      # if statement computes the 90 day moving average along with the 90 day standard deviation
      if i >= 90:
         threeMonthAvg.append(sum(priceHistory[i - 90:i]) / 90)
         # this loop calculates 90 day standard deviation
         j, summ = i - 90, 0
         while j < i:
            summ += (priceHistory[j] - oneMonthAvg[i - 90]) ** 2
            j += 1
         threeMonthStd.append((summ / 90) ** .5)
      i += 1

   return [priceHistory, oneMonthAvg, oneMonthStd, threeMonthAvg, threeMonthStd]

# MAIN METHOD -- USED FOR ALGOTRADING


# Updates data for crypto asset you are holding (in this case, Ethereum)
# Due the the robinhood API being unofficial, most calls to the API functions will be surrounded by try catch statements. That way, if robinhood changes their website
# and the HTTP requests this program is making no longer work, the error will be caught and dealt with.
try:
   cryptoHoldings = rs.crypto.get_crypto_positions()
   quantity = float([crypto for crypto in cryptoHoldings if crypto.get(
       'currency').get('code') == 'ETH'][0].get('quantity_available'))

   priceInfo = updateCryptoPriceInfo('ETH')

   eth = assetClass(quantity, priceHistory=priceInfo[0], oneMonthAvg=priceInfo[1],
                    oneMonthStd=priceInfo[2], threeMonthAvg=priceInfo[3], threeMonthStd=priceInfo[4])
except:
   # due to the code running on the cloud, the user will be notified of any failures by receiving texts/emails
   emailAlert('RobinhoodPro ERROR',
              'Failed to get historical price data.', phone_number + '@tmomail.net')
   sys.exit('ERROR: Failed to get historical price data.')

# This while loop is in essence the trading algorithm that the program uses. It sees if the current price is above or below the one month moving average. If it is
# below, it sells your assets if you still own them. If it is above, it buys your assets with the buying power you have left.
i = 0
while True:

   # Gets price
   # This code will be executed every 5 minutes in order not to overburden the website with HTTP requests.
   try:
      currentPrice = round(
          float(rs.crypto.get_crypto_quote('ETH', info='mark_price')), 2)
   except:
      emailAlert('RobinhoodPro ERROR',
                 'Failed to get current price.', phone_number + '@tmomail.net')
      sys.exit('ERROR: Failed to get current price.')

   # Buys at buying power / 1.01 as robinhood needs a min of $1 order buy also needs 1% less than your buying power. Morover, the minimum ammount of ethereum
   # that can be bought is .001 (although I made it .002 just to be sure).
   buyingPrice = truncatePrice(buyingPower / 1.01)
   if currentPrice > eth.oneMonthAvg[-1] and buyingPrice >= 1.00 and buyingPrice / currentPrice >= .002:

      try:
         orderInfo = rs.orders.order_crypto(
             'ETH', 'buy', buyingPrice, amountIn='price', limitPrice=None, timeInForce='gtc', jsonify=True)
      except:
         emailAlert('RobinhoodPro ERROR',
                    'Buy order caused program to crash.', phone_number + '@tmomail.net')
         sys.exit('ERROR: Buy order caused program to crash.')

      # program waits for 10 seconds to wait for order to execute
      time.sleep(10)

      try:
         # The ethereum quantity is updated accordingly. If the order had failed, then the 'quantity' iteam in the orderInfo dictionary won't be a number but an
         # error message, thus causing the program to crash and sending texts or emails to the user
         eth.quantity += float(orderInfo.get('quantity'))
      except:
         emailAlert('RobinhoodPro ERROR',
                    'Buy order was not executed.', phone_number + '@tmomail.net')
         sys.exit('ERROR: Buy order was not executed.')

      buyingPower = round(
          float(rs.profiles.load_account_profile('crypto_buying_power')), 2)

   # Sells if the user is holding any ethereum
   elif currentPrice <= eth.oneMonthAvg[-1] and eth.quantity != 0:

      try:
         orderInfo = rs.orders.order_crypto(
             'ETH', 'sell', eth.quantity, amountIn='quantity', limitPrice=None, timeInForce='gtc', jsonify=True)
      except:
         emailAlert('RobinhoodPro ERROR',
                    'Sell order caused program to crash.', phone_number + '@tmomail.net')
         sys.exit('ERROR: Sell order caused program to crash.')

      time.sleep(10)

      try:
         eth.quantity -= float(orderInfo.get('quantity'))
      except:
         emailAlert('RobinhoodPro ERROR',
                    'Sell order was not executed.', phone_number + '@tmomail.net')
         sys.exit('ERROR: Sell order was not executed.')

      buyingPower = round(
          float(rs.profiles.load_account_profile('crypto_buying_power')), 2)

   time.sleep(300)
   i += 1

rs.authentication.logout()
