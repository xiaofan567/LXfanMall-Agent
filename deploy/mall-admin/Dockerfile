FROM openjdk:8-jre-slim

WORKDIR /app

COPY mall-admin-1.0-SNAPSHOT.jar app.jar

ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN mkdir -p /var/logs

EXPOSE 8080

ENTRYPOINT ["java", "-jar", \
    "-Dspring.profiles.active=prod", \
    "-Djava.security.egd=file:/dev/./urandom", \
    "-Xms128m", "-Xmx256m", \
    "app.jar"]
