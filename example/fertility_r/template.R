#read in raw data from Study 1
df <- read.csv2("durante_etal_2013_study1.txt", sep = "")

# create religiosity score
df$RelComp <- round(rowMeans(cbind(df$Rel1, df$Rel2, df$Rel3), na.rm = TRUE), digits = 2)

# next menstrual onset (nmo) assessment
Sys.setenv(TZ="Europe/Berlin") # suppress time zone warning
df$DateTesting <- as.Date(df$DateTesting, format = "%m/%d/%y")
df$StartDateofLastPeriod <- as.Date(df$StartDateofLastPeriod, format = "%m/%d/%y")
df$StartDateofPeriodBeforeLast <- as.Date(df$StartDateofPeriodBeforeLast,
                                                    format = "%m/%d/%y")
df$ComputedCycleLength <- df$StartDateofLastPeriod - df$StartDateofPeriodBeforeLast

# --- (NMO) computed
# first nmo option: based on computed cycle length
df$NextMenstrualOnset <- df$StartDateofLastPeriod + df$ComputedCycleLength

# --- (NMO) reported
# second nmo option: based on reported cycle length
df$NextMenstrualOnset <- df$StartDateofLastPeriod + df$ReportedCycleLength

# # --- (NMO) estimate
# # third nmo option: based on reported estimate of next menstrual onset
# # note: this is not available in study one
# df$NextMenstrualOnset <- df$StartDateNext

# --- (ECL) computed
# exclusion based on computed cycle length
df <- df[!(df$ComputedCycleLength < 25 | df$ComputedCycleLength > 35), ]

# --- (ECL) reported
# exclusion based on reported cycle length
df <- df[!(df$ReportedCycleLength < 25 | df$ReportedCycleLength > 35), ]

# --- (ECL) none
# include all cycle lengths

# --- (A)
# compute cycle day
df$DaysBeforeNextOnset <- df$NextMenstrualOnset - df$DateTesting
df$CycleDay <- 28 - df$DaysBeforeNextOnset
df$CycleDay <- ifelse(df$CycleDay <1, 1, df$CycleDay)
df$CycleDay <- ifelse(df$CycleDay > 28, 28, df$CycleDay)

# fertility assessment
bounds = {{fertility_bounds}}
df$Fertility <- rep(NA, dim(df)[1])  # create fertility variable
df$Fertility[df$CycleDay >= bounds[1] & df$CycleDay <= bounds[2]] <- "High"
df$Fertility[df$CycleDay >= bounds[3] & df$CycleDay <= bounds[4]] <- "Low"
df$Fertility[df$CycleDay >= bounds[5] & df$CycleDay <= bounds[6]] <- "Low"

# relationship status assessment
rel.bounds = {{relationship_bounds}}
df$RelationshipStatus[df$Relationship <= rel.bounds[1]] <- "Single"
df$RelationshipStatus[df$Relationship >= rel.bounds[2]] <- "Relationship"

# --- (EC) certainty
# exclusion based on certainty ratings
df <- df[!(df$Sure1 < 6 | df$Sure2 < 6), ]

# --- (EC) none
# include all certainty ratings

# --- (B)
# perform an ANOVA on the processed data set
df$Fertility <- factor(df$Fertility)
df$RelationshipStatus <- factor(df$RelationshipStatus)
an = lm("RelComp~Fertility*RelationshipStatus", df)
summar <- summary(an)
# the p-value of the fertility x relationship interaction
summar$coefficients[4, 4]
