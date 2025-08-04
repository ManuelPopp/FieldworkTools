require("ggplot2")

data <- read.csv("Tests.csv")
data$Altitude <- factor(data$Altitude)

ggplot2::ggplot(data = data, ggplot2::aes(x = Overlap, y = Spacing, colour = Altitude)) +
  ggplot2::geom_point() +
  ggplot2::geom_smooth(method = "lm")

parameter_df <- data.frame()
for (lvl in levels(data$Altitude)) {
  altitude <- as.numeric(as.character(lvl))
  mod <- lm(Spacing ~ Overlap, data = data[which(data$Altitude == lvl),])
  intercept <- coefficients(mod)[1]
  slope <- coefficients(mod)[2]
  df <- data.frame(altitude = altitude, intercept = intercept, slope = slope)
  parameter_df <- rbind(parameter_df, df)
}

plot(intercept ~ altitude, data = parameter_df)
mi <- lm(intercept ~ altitude, data = parameter_df)
abline(a = coefficients(mi)[1], b = coefficients(mi)[2], col = "red")
plot(slope ~ altitude, data = parameter_df)
ms <- lm(slope ~ altitude, data = parameter_df)
abline(a = coefficients(ms)[1], b = coefficients(ms)[2], col = "red")

altitude = 70
overlap = 70

c1 <- coefficients(ms)[2]
c2 <- coefficients(mi)[2]
spacing <- c1 * altitude * overlap + c2 * altitude

(c1 * overlap + c2) * altitude

horizontalfov <- 61.2
spacing = tan((horizontalfov / 2) * pi / 180) * altitude * (2 - overlap / 100)
