# ==========================================
# 1. READ DATA
# ==========================================
df <- read.csv("final_departures.csv", stringsAsFactors = FALSE)

# Transport mode
df$Transportslag <- ifelse(df$line == 64, "Buss 64", "Spårvagn 6")

# Convert logical column if needed
df$is_delayed <- as.logical(df$is_delayed)

# Define lateness instead of signed delay
df$lateness_minutes <- ifelse(df$delay_minutes < 0, 0, df$delay_minutes)

# ==========================================
# 2. DESCRIPTIVE STATISTICS
# ==========================================
library(dplyr)

summary_table <- df %>%
  group_by(Transportslag) %>%
  summarise(
    n = n(),
    mean_lateness = mean(lateness_minutes),
    median_lateness = median(lateness_minutes),
    sd_lateness = sd(lateness_minutes),
    delayed_count = sum(is_delayed),
    delayed_prop = mean(is_delayed)
  )

print(summary_table)

# ==========================================
# 3. TEST 1
# MEAN LATENESS COMPARISON
# ==========================================
cat("--------------------------------------------------\n")
cat("TEST 1: TWO SAMPLE COMPARISON OF MEAN LATENESS\n")
cat("H0: mean lateness is the same for Bus 64 and Tram 6\n")
cat("H1: mean lateness differs between Bus 64 and Tram 6\n")
cat("--------------------------------------------------\n")

# Welch version
t_test_result <- t.test(lateness_minutes ~ Transportslag, data = df)
print(t_test_result)

# Optional pooled version for closer alignment with course t test
t_test_pooled <- t.test(lateness_minutes ~ Transportslag, data = df, var.equal = TRUE)
print(t_test_pooled)

# ==========================================
# 4. TEST 2
# CHI SQUARE TEST OF HOMOGENEITY
# ==========================================
cat("--------------------------------------------------\n")
cat("TEST 2: CHI SQUARE TEST OF HOMOGENEITY\n")
cat("H0: the proportion delayed > 3 min is the same\n")
cat("H1: the proportions differ\n")
cat("--------------------------------------------------\n")

tabell <- table(df$Transportslag, df$is_delayed)
print(tabell)

# Pearson chi square without Yates correction
chi_result <- chisq.test(tabell, correct = FALSE)
print(chi_result)

cat("Expected counts:\n")
print(chi_result$expected)

# Optional: Yates corrected version
chi_result_yates <- chisq.test(tabell)
print(chi_result_yates)

# Optional: Fisher exact test as robustness check
fisher_result <- fisher.test(tabell)
print(fisher_result)

# ==========================================
# 5. PLOTS
# ==========================================
par(mfrow = c(2, 2))

boxplot(lateness_minutes ~ Transportslag, data = df,
        main = "Lateness in minutes",
        ylab = "Minutes")

hist(df$lateness_minutes[df$Transportslag == "Buss 64"],
     main = "Bus 64 lateness",
     xlab = "Minutes")

hist(df$lateness_minutes[df$Transportslag == "Spårvagn 6"],
     main = "Tram 6 lateness",
     xlab = "Minutes")

barplot(prop.table(tabell, 1),
        beside = TRUE,
        legend.text = c("Not delayed", "Delayed > 3 min"),
        main = "Proportion delayed by transport mode")

# QQ plots
par(mfrow = c(1, 2))
qqnorm(df$lateness_minutes[df$Transportslag == "Buss 64"], main = "QQ plot Bus 64")
qqline(df$lateness_minutes[df$Transportslag == "Buss 64"])

qqnorm(df$lateness_minutes[df$Transportslag == "Spårvagn 6"], main = "QQ plot Tram 6")
qqline(df$lateness_minutes[df$Transportslag == "Spårvagn 6"])