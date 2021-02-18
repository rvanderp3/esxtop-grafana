from flask import Flask
app = Flask("dataserv")

import esxtop_metric_server
import promql_metric_server

app.run(host= '0.0.0.0')

