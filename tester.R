# ==========================================
# 1. LÄS IN DATAN
# ==========================================

# Läs in er nya, städade fil
df <- read.csv("final_departures.csv", stringsAsFactors = FALSE)

# Skapa kategorin Transportslag (Linje 64 = Buss, Linje 6 = Spårvagn)
df$Transportslag <- ifelse(df$line == 64, "Buss", "Spårvagn")

# Om ett fordon var för tidigt (negativt värde i delay_minutes) sätter vi förseningen till 0
# för att inte förvränga snittförseningen nedåt i t-testet
df$delay_minutes[df$delay_minutes < 0] <- 0

# ==========================================
# 2. UTFÖR STATISTISKA TESTER (MVE155 / MSG200)
# ==========================================

print("--------------------------------------------------")
print("TEST 1: TWO-SAMPLE T-TEST (KAPITEL 7)")
print("Jämför genomsnittlig försening mellan Buss 64 och Spårvagn 6")
print("--------------------------------------------------")

t_test_resultat <- t.test(delay_minutes ~ Transportslag, data = df)
print(t_test_resultat)

print("--------------------------------------------------")
print("TEST 2: CHI-TVÅ-TEST (KAPITEL 9)")
print("Jämför proportionen försenade avgångar (>3 min)")
print("--------------------------------------------------")

# Skapa korstabellen (Buss/Spårvagn mot True/False)
tabell <- table(df$Transportslag, df$is_delayed)
print("Korstabell (Antal observationer per kategori):")
print(tabell)

# Utför testet
chi2_resultat <- chisq.test(tabell)
print(chi2_resultat)

# ==========================================
# 3. SKAPA EN GRAF TILL PRESENTATIONEN
# ==========================================
boxplot(delay_minutes ~ Transportslag, data = df, 
        main = "Försening i rusningstrafik: Buss 64 vs Spårvagn 6",
        ylab = "Försening (minuter)", 
        col = c("lightblue", "lightgreen"))

