# check if we support the model type
# @param model The fitted model object
is_supported <- function (model) {
  ms <- c('lm', 'lmerMod', 'negbin', 'aov')
  return(class(model)[1] %in% ms)
}

# get model predictions per data point
# @param model The fitted model object
# @param df The dataframe that the model will predict on
pointwise_predict <- function (model, df) {
  if (!is_supported(model)) {
    stop(paste('Unsupported model type', class(model)[1]))
  }

  # fixme: lmerMod does not have se.fit
  pred <- predict(model, df, se.fit = TRUE, type = "response")
  disagg_fit <- df  %>%
    mutate(
      fit = pred$fit,                                     # inferential fits
      se.fit = pred$se.fit,                               # standard errors of predicted means
      df = df.residual(model),                            # residual degrees of freedom
      sigma = sigma(model),                               # residual standard deviation
      se.residual = sqrt(sum(residuals(model)^2) / df)    # residual standard errors
    )
  return(disagg_fit)
}

# perform k-fold cross validation
# @param df The dataframe
# @param model The fitted model
# @param y The column name for the observed variable in df
# @param folds The number of folds
# @param func A function returning the fitted y vector from a model and a dataset
cross_validation <- function (df, model, y, folds = 5, func = NULL) {
  l = nrow(df) %/% folds
  mse = 0
  for (i in c(1:folds)) {
    # properly splitting train/test
    i1 = l*(i-1)+1
    i2 = l*i
    d_test = df[i1:i2, ]
    if (i1 > 1) {
      if (i2+1 < nrow(df)) {
        d_train = rbind(df[1:(i1-1), ], df[(i2+1):nrow(df), ])
      } else {
        d_train = df[1:(i1-1), ]
      }
    } else {
      d_train = df[(i2+1):nrow(df), ]
    }

    m1 <- update(model, . ~ ., data = d_train)
    if (!is.null(func)) {
        expected <- func(m1, d_test)
    } else {
        # fixme: lmerMod need to set allow.new.levels = TRUE
        expected <- pointwise_predict(m1, d_test)$fit
    }

    mse = mse + sum((d_test[[y]] - expected)^2)
  }

  mse = sqrt(mse / nrow(df))
  return(mse)
}

# marginalize model predictions
# @param df The dataframe containing individual model fits
# @param term The predictor of interest
# @param y The value field to aggregate
margins <- function (df, term, y = "fit") {
  expectation <- df %>%
    group_by(!! sym(term)) %>%                   # group by predictor(s) of interest
    summarize(expected = weighted.mean(!! sym(y))) %>%  # marninalize across other predictors
    compare_levels(expected, by = !! sym(term)) %>%
    ungroup()
  return(expectation)
}

# get the sampling distribution
# @param model The fitted model
# @param term The predictor of interest
# @param type Type of result (response or model coefficient)
# @param draws The number of draws
sampling_distribution <- function (model, term, type="coef", draws=200) {
  if (!is_supported(model)) {
    stop(paste('Unsupported model type', class(model)[1]))
  }
  ts = c('coef', 'coefficient', 'resp', 'response')
  if (!(type %in% ts)) {
    stop(paste('Unsupported type', type))
  }

  if (type == "coef" || type == "coefficient") {
    uncertainty <- tidy(model, conf.int = TRUE) %>%
      filter(term == !! term) %>%
      mutate(
        df = df.residual(model),                # get model degrees of freedom
        .draw = list(1:draws),                  # generate list of draw numbers
        t = map(df, ~rt(draws, .))              # simulate draws as t-scores
      ) %>%
      unnest(cols = c(".draw", "t")) %>%
      mutate(coef = t * std.error + estimate)
  }

  if (type == "resp" || type == "response") {
    # todo
  }

  return(uncertainty)
}
