# 해외종목

library(tidyverse)
library(quantmod)
library(PerformanceAnalytics)

symbols <- c('SPY', 'IEF')
getSymbols(symbols, src = 'yahoo', from = '2000-01-01')
symbols <- str_remove_all(symbols, '\\^')
prices <-  do.call(cbind, lapply(symbols, function(x) Ad(get(x)))) %>% 
  `colnames<-`(symbols) %>% 
  na.omit()
rets <- CalculateReturns(prices) %>% na.omit()
portfolio <- Return.portfolio(rets,
                              weights = c(0.6, 0.4),
                              rebalance_on = 'months',
                              verbose = TRUE)
charts.PerformanceSummary(portfolio$returns)
Return.cumulative(portfolio$returns)
Return.annualized(portfolio$returns)
SharpeRatio.annualized(portfolio$returns)
table.Drawdowns(portfolio$returns)
apply.yearly(portfolio$returns, Return.cumulative)



# 국내종목

library(httr)
library(rvest)
library(lubridate)

symbols = c('A069500', 'A148070')
getKorSymbols <- function(symbols){
  for (symbol in symbols){
    url <- "https://fchart.stock.naver.com/sise.nhn"
    resp <- GET(url = url,
                query = list(symbol = str_remove(symbol, 'A'),
                             timeframe = "day",
                             count = 10000,
                             requestType = 0))
    ohlc <- read_html(resp) %>%
      html_nodes(css = 'item') %>%
      html_attr('data') %>%
      read_delim(delim = "|",
                 col_names = c(
                   'Date',
                   paste(symbol, 'Open', sep = '.'),
                   paste(symbol, 'High', sep = '.'),
                   paste(symbol, 'Low', sep = '.'),
                   paste(symbol, 'Close', sep = '.'),
                   paste(symbol, 'Volume', sep = '.')
                 )) %>% 
      mutate(Date = ymd(Date))
    ohlc <- xts(ohlc[, -1], order.by = ohlc$Date)
    assign(symbol, ohlc, envir = .GlobalEnv)
  }
}
getKorSymbols(symbols)
prices <-  do.call(cbind, lapply(symbols, function(x) Cl(get(x)))) %>% 
  `colnames<-`(symbols) %>% 
  na.omit()
rets <- CalculateReturns(prices) %>% na.omit()
portfolio <- Return.portfolio(rets,
                              weights = c(0.6, 0.4),
                              rebalance_on = 'months',
                              verbose = TRUE)
charts.PerformanceSummary(portfolio$returns)
Return.cumulative(portfolio$returns)
Return.annualized(portfolio$returns)
SharpeRatio.annualized(portfolio$returns)
table.Drawdowns(portfolio$returns)
apply.yearly(portfolio$returns, Return.cumulative)

