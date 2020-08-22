library(tidyverse)
library(tidyquant)
library(highcharter)

data_path <- paste(getwd(), 'data', sep = '/')
prices <- read_csv(paste(data_path, 'krx_smartbeta_index.csv', sep = '/'))

prices_monthly <- prices %>% 
  gather(key = 'ticker', value = 'close', -date) %>% 
  mutate(date = ymd(date)) %>% 
  group_by(ticker) %>% 
  tq_transmute(select = close,
               mutate_fun = to.monthly,
               indexAt = 'lastof')

n_lag = 6

lowvol_returns <- prices_monthly %>% 
  filter(ticker == 'lowvol') %>% 
  mutate(lowvol_return = ((close / lag(close)) - 1),
         lowvol_period_return = ((close / lag(close, n_lag)) - 1)) %>% 
  ungroup() %>% 
  select(-ticker, -close) %>% 
  na.omit()

momentum_returns <- prices_monthly %>% 
  filter(ticker == 'momentum') %>% 
  mutate(momentum_return = ((close / lag(close)) - 1),
         momentum_period_return = ((close / lag(close, n_lag)) - 1)) %>% 
  ungroup() %>% 
  select(-ticker, -close) %>% 
  na.omit()  

quality_returns <- prices_monthly %>% 
  filter(ticker == 'quality') %>% 
  mutate(quality_return = ((close / lag(close)) - 1),
         quality_period_return = ((close / lag(close, n_lag)) - 1)) %>% 
  ungroup() %>% 
  select(-ticker, -close) %>% 
  na.omit()

value_returns <- prices_monthly %>% 
  filter(ticker == 'value') %>% 
  mutate(value_return = ((close / lag(close)) - 1),
         value_period_return = ((close / lag(close, n_lag)) - 1)) %>% 
  ungroup() %>% 
  select(-ticker, -close) %>% 
  na.omit()

rates <- read_csv(paste(data_path, 'mmf_rate.csv', sep = '/'))
rates <- rates %>% 
  mutate(date = ymd(date),
         mmf_rate = na.locf(mmf_rate) / 100 * n_lag / 12)   # MMF 연수익률을 lag 기간으로 환산

joined_returns <- lowvol_returns %>% 
  left_join(momentum_returns, by = 'date') %>% 
  left_join(quality_returns, by = 'date') %>% 
  left_join(value_returns, by = 'date') %>% 
  left_join(rates, by = 'date')

return_rank <- joined_returns %>% 
  select(contains('period')) %>% 
  `*`(-1) %>% 
  apply(1, rank) %>% 
  t() %>% 
  as_tibble()
colnames(return_rank) <- paste(colnames(return_rank), 'rank', sep = '_')

joined_returns <- bind_cols(joined_returns, return_rank)

joined_returns <- joined_returns %>% 
  mutate(dm_return = ifelse(lag(lowvol_period_return_rank) == 1 &
                                lag(lowvol_period_return) > lag(mmf_rate),
                              lowvol_return,
                              ifelse(lag(momentum_period_return_rank) == 1 &
                                       lag(momentum_period_return) > lag(mmf_rate),
                                     momentum_return,
                                     ifelse(lag(quality_period_return_rank) == 1 &
                                              lag(quality_period_return) > lag(mmf_rate),
                                            quality_return,
                                            ifelse(lag(value_period_return_rank) == 1 &
                                                     lag(value_period_return) > lag(mmf_rate),
                                                   value_return,
                                                   mmf_rate / n_lag)))), # MMF 연수익률을 월 기준으로 환산
         dm_label = ifelse(lag(lowvol_period_return_rank) == 1 &
                               lag(lowvol_period_return) > lag(mmf_rate),
                             'lovvol',
                             ifelse(lag(momentum_period_return_rank) == 1 &
                                      lag(momentum_period_return) > lag(mmf_rate),
                                    'momentum',
                                    ifelse(lag(quality_period_return_rank) == 1 &
                                             lag(quality_period_return) > lag(mmf_rate),
                                           'quality',
                                           ifelse(lag(value_period_return_rank) == 1 &
                                                    lag(value_period_return) > lag(mmf_rate),
                                                  'value',
                                                  'mmf')))),
         ew_return = (lowvol_return + momentum_return + quality_return + value_return) / 4)

kospi <- read_csv(paste(data_path, 'kospi.csv', sep = '/')) %>% 
  tq_transmute(select = kospi,
               mutate_fun = to.monthly,
               indexAt = 'lastof') %>% 
  mutate(kospi_return = ((kospi / lag(kospi)) - 1))

backtest_result <- joined_returns %>% 
  left_join(kospi, by = 'date') %>% 
  na.omit() %>% 
  select(date, dm_label, dm_return, ew_return, kospi_return) %>% 
  mutate(dm_growth = cumprod(1 + dm_return),
         ew_growth = cumprod(1 + ew_return),
         kospi_growth = cumprod(1 + kospi_return))

backtest_result %>% 
  count(dm_label) %>% 
  mutate(prop = prop.table(n)) %>% 
  ggplot(aes(dm_label, prop, fill = dm_label)) +
  geom_col(width = .15) +
  scale_y_continuous(labels = scales::percent) +
  geom_label(aes(label = dm_label), vjust = -.5, fill = "white") +
  ylab('relative frequeancies') +
  xlab('') +
  expand_limits(y = .4) +
  theme(legend.position = 'none',
        axis.text.x = element_blank(),
        axis.ticks = element_blank())

backtest_result %>% 
  select(dm_return, ew_return) %>% 
  gather(type, returns) %>% 
  ggplot(aes(returns, color = type, fill = type)) +
  geom_histogram(bins = 30) +
  facet_wrap(~type)

backtest_result %>% 
  select(dm_return, ew_return) %>% 
  gather(type, returns) %>% 
  ggplot(aes(type, returns, color = type, fill = type)) +
  geom_boxplot(fill = 'white', width = .1) +
  geom_violin(alpha = .05) +
  coord_flip()

backtest_result %>% 
  select(date, dm_growth, ew_growth, kospi_growth) %>% 
  gather(asset, growth, -date) %>% 
  hchart(., hcaes(date, growth, group = asset), type = 'line') %>% 
  hc_tooltip(pointFormat = "{point.asset}: ${point.growth: .2f}")
