
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
from urllib.parse import parse_qs
from datetime import datetime
from flask import Flask, jsonify, request
import json 
import copy

app = Flask("dataserv")

@app.route("/api/v1/label/__name__/values", methods=['GET'])
def labels():
    labels = []
    outResults = {
        "status": "success",
        "data": labels
    }
    for col in columnMap:
        if col == "time":
            continue
        labels.append(col)
    return json.dumps(outResults)
    
@app.route("/api/v1/values", methods=['GET'])
@app.route("/api/v1/query", methods=['GET'])
@app.route("/api/v1/query_range", methods=['GET'])
def query():
    query_parameters = request.args
    
    query_val = query_parameters.get('query')
    start_time = query_parameters.get('start')
    end_time = query_parameters.get('end')
    return populateResults(query_val,start_time,end_time)
    

@app.route("/api/v1/metadata", methods=['GET'])
def metadata():
    return getMetadata()

columnMap = dict()
metrics = dict()

metadataResults = {
    "status": "success",
    "data": {
    }
}

results = {
    "status": "success",
    "data": {
        "resultType": "matrix",
        "result": [

        ]
    }
}

result = {
    "metric": {
        "__name__":"",
        "job": "",
        "instance": ""
    },
    "values": []
}

def getMetadata():
    outResults = copy.deepcopy(metadataResults)
    for col in columnMap:
        if col == "time":
            continue
        outResults["data"][col] = [{
            "type": "gauge",
            "help": "",
            "unit": ""
        }]
        
    return json.dumps(outResults)

def populateResults(query, start, end):
    outResults = copy.deepcopy(results)
    resultMap = {}
    for col in columnMap:
        if col == "time" or (query != None and query != col):
            continue
        thisResult = copy.deepcopy(result)
        resultMap[col] = thisResult
        thisResult["metric"]["__name__"] = thisResult["metric"]["job"] = thisResult["metric"]["instance"] = col    

    index = 0

    for t in metrics["time"]:
        if (start != None and (t < float(start))) or (end != None and (t > float(end)) ):
            index = index + 1
        else:
            for col in columnMap:            
                if col == "time" or (query != None and query != col):
                    continue                
                resultMap[col]["values"].append([t,metrics[col][index]])
            index = index + 1    
        

    for col in columnMap:
        if col in resultMap:
            outResults["data"]["result"].append(resultMap[col])    
    
    return json.dumps(outResults)

def timeToMillis(time):    
    return datetime.strptime(time,'%m/%d/%Y %H:%M:%S').timestamp()

with open('/csv/metrics.csv') as f:
    firstLine = True
    for line in f:
        columns = line.split(",")        
        index = 0
        if firstLine:
            firstLine = False
            metrics["time"] = []
            for col in columns:
                try:
                    col = col[3:-1]
                    hostnameLoc = col.index("\\")                    
                    name = col[hostnameLoc+1:-1].replace(' ', '').replace('\\', '_').replace('(', '').replace(')', '').lower()                    
                    columnMap[name] = index
                    metrics[name] = []
                    index = index + 1
                except ValueError:
                    index = index + 1
                    continue                 
        else:
            metrics["time"].append(timeToMillis(columns[0].replace('"', '')))
            for col in columnMap:
                val = columns[columnMap[col]].replace('"', '')
                metrics[col].append(val)

app.run(host= '0.0.0.0')
