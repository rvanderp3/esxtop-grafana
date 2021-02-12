FROM grafana/grafana
COPY grafana.ini /etc/grafana/grafana.ini
COPY datasources.yaml /etc/grafana/provisioning/datasources/datasources.yaml
EXPOSE 3000
RUN grafana-cli plugins install grafana-simple-json-datasource
