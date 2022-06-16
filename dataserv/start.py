from flask import Flask
import time
app = Flask("dataserv")

from esxtop_metric_server import esxtop_bp
from promql_metric_server import promql_bp
from etcd_metric_server import  etcd_bp

app.register_blueprint(esxtop_bp)
app.register_blueprint(promql_bp)
app.register_blueprint(etcd_bp)

app.run(host= '0.0.0.0')

