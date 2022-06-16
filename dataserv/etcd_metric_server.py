
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
from urllib.parse import parse_qs
from datetime import datetime
from flask import Flask, jsonify, request, Blueprint
import json
import copy
import re
from os import listdir
from os.path import isfile, join


etcd_bp = Blueprint('etcd', __name__)

columnMap = dict()
metrics = dict()
hostname=""

print(">>>> Initializing etcd log datasource")

@etcd_bp.route("/etcd/api/v1/label/__name__/values", methods=['GET'])
def labels():
    #reloadMetrics()
    labels = []
    outResults = {
        "status": "success",
        "data": labels
    }
    for col in columnMap:
        if col == col+"_time":
            continue
        labels.append(col)
    return json.dumps(outResults)

@etcd_bp.route("/etcd/api/v1/values", methods=['GET'])
@etcd_bp.route("/etcd/api/v1/query", methods=['GET'])
@etcd_bp.route("/etcd/api/v1/query_range", methods=['GET'])
def query():
    reloadMetrics()
    query_parameters = request.args

    query_val = query_parameters.get('query')
    start_time = query_parameters.get('start')
    end_time = query_parameters.get('end')
    return populateResults(query_val,start_time,end_time)


@etcd_bp.route("/etcd/api/v1/metadata", methods=['GET'])
def metadata():
    return getMetadata()


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
        if col == col+"_time" or (query != None and col.find(query) == -1):
            continue
        thisResult = copy.deepcopy(result)
        resultMap[col] = thisResult
        thisResult["metric"]["__name__"] = col
        thisResult["metric"]["instance"] = hostname
    
    index = 0    
    for col in columnMap:
        if col == col+"_time" or (query != None and col.find(query) == -1):
            continue
        for t in metrics[col+"_time"]:
          if (start != None and (t < float(start))) or (end != None and (t > float(end)) ):
            index = index + 1
            continue
          resultMap[col]["values"].append([t,metrics[col][index]])
          index = index + 1
    


    for col in columnMap:
        if col in resultMap:
            outResults["data"]["result"].append(resultMap[col])

    return json.dumps(outResults)

def reloadMetrics():
    global hostname, columnMap, metrics
    columnMap = dict()
    metrics = dict()    
    for fname in listdir('/csv/data/etcd'):
        fullPath = join('/csv/data/etcd',fname)
        if isfile(fullPath) and fname[0] != "." :
            print(">>>> Loading " + fname)
            with open(fullPath) as f:
                print(">>>> Opened " + fname)
                firstLine = True
                for line in f:
                    try:
                        index = 0
                        if firstLine:
                            firstLine = False                            
                            columnMap[fname] = index
                            metrics[fname] = []
                            metrics[fname+"_time"] = []
                            index = index + 1
                        logLineJson = json.loads(line)                        
                        if logLineJson["msg"] != "apply request took too long":
                            continue
                        metrics[fname+"_time"].append(timeToMillis(logLineJson["ts"]))
                        took = logLineJson["took"]
                        took = took.rstrip("ms")
                        metrics[fname].append(took)
                    except ValueError:
                        pass
        print("processed " + str(len(metrics[fname])) + " metrics")

print(">>>> Initialized etcd datasource")

def timeToMillis(time):    
    return datetime.strptime(time,'%Y-%m-%dT%H:%M:%S.%fZ').timestamp()


reloadMetrics()
