from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
from urllib.parse import parse_qs
from datetime import datetime
from flask import Flask, jsonify, request
from start import app
import json 
import copy
import re
from os import listdir
from os.path import isfile, join

promql_files = "/csv/data/promql"

metadataResults = {
    "status": "success",
    "data": {
    }
}


@app.route("/promql/api/v1/label/__name__/values", methods=['GET'])
def promql_labels():
    labels = []
    outResults = {
        "status": "success",
        "data": labels
    }
    for f in listdir(promql_files):
        if isfile(join(promql_files,f)) and f[0] != "." :            
            labels.append(f)
    return json.dumps(outResults)

@app.route("/promql/api/v1/metadata", methods=['GET'])    
def getMetadata():
    outResults = copy.deepcopy(metadataResults)
    for f in listdir(promql_files):
        if isfile(join(promql_files,f)) and f[0] != "." :
            outResults["data"][f] = [{
                "type": "gauge",
                "help": "",
                "unit": ""
            }]
    return json.dumps(outResults)


@app.route("/promql/api/v1/values", methods=['GET'])
@app.route("/promql/api/v1/query", methods=['GET'])
@app.route("/promql/api/v1/query_range", methods=['GET'])
def query():
    query_parameters = request.args
    
    query_val = query_parameters.get('query')
    start_time = query_parameters.get('start')
    end_time = query_parameters.get('end')
    with open(join(promql_files,query_val)) as f:
        return f.read()    