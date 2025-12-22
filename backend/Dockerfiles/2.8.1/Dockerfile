FROM openjdk:25-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN apt update
RUN apt install -y wget

WORKDIR /app
ADD ./app .

RUN wget -O otp-shaded.jar https://github.com/opentripplanner/OpenTripPlanner/releases/download/v2.8.1/otp-shaded-2.8.1.jar

EXPOSE 8080 8081

ENTRYPOINT [ "sh", "./run.sh" ]