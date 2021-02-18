# Overview 

`esxtop` is able to record data in a `batch mode`.  In `batch mode` data is stored in a time-stamped csv format.  Reviewing the data can be difficult due to the format, quantity, and a lack of tools that can quickly consume it.  This project consumes this CSV data and structures it in to prometheus query results.  This project is intended to be 'turn-key' and stands up an instance of grafana and the metric server.  Data is consumed from a file named `metrics.csv` which is to be placed in `dataserv/data/esxtop/metrics.csv`.

# Requirements

- podman
- [podman-compose](https://github.com/containers/podman-compose)
- ssh access to an ESXi host

# Gathering Data

In its most basic invocation, `esxtop` will record all known metrics:

~~~
ssh <esxuser>@<esxihost> esxtop -b &> metrics.csv
~~~

This is usually a staggering number of metrics and can be difficult to effectively parse.  It is recommended that metrics are selectively chosen to reduce the burden on the collection and review of the metrics.  To do this:

1. Determine the entities of the metrics being monitored

~~~
ssh <esxuser>@<esxihost> esxtop -export-entity entities.dat
scp <esxuser>@<esxihost>:entities.dat .
~~~

In this file there are entity groups.  `SchedGroup` contains processes and VMs.  If the goal is to collect metrics from VMs associated with nodes in the cluster the VMs of interest must be isolated.

2. Filter entities to collect

~~~
NODES=$(oc get nodes -o=jsonpath='{.items[*].metadata.name}')
echo SchedGroup > filtered.dat
for NODE in $NODES; do cat entities.dat | grep $NODE >> filtered.dat ; done
scp filtered.dat <esxuser>@<esxihost>: .
~~~

3. Collect metrics

~~~
ssh <esxuser>@<esxihost> esxtop -b -import-entity filtered.dat | tee metrics.csv
~~~

When finished, `control+c` can be invoked.  Also, `esxtop` accepts parameters which define the time between collections(`-d`) and the number of collections(`-n`).  Otherwise, `esxtop` will run until interrupted.

4. Start Metrics Server

a. Copy `metrics.csv` to `dataserv/data/esxtop/metrics.csv`.  
b. From the root of the project, run `podman-compose build;podman-compose up`


5. Analyze Metrics

Enter `http://localhost:3000` in to your browser of choice.  The datasource is `esxtop batch reader`.  The metrics server only has limited query support:
- The timeframe of the metrics can be restricted
- Indiviual metrics can be selected for query
- Substrings of metrics can be provided in the query


# Overlaying Additional Metrics

Metrics may also be directly exported from prometheus to augment the data gathered from `esxtop`.  This can be helpful, if for example, it is needed to
correlate etcd performance against ESXi performance.  

## Extracting Metrics From Prometheus

~~~
function promqlQuery() {
    END_TIME=$(date -u +%s) 
    START_TIME=$(date -u --date="30 minutes ago" +%s)

    oc exec -c prometheus -n openshift-monitoring prometheus-k8s-0 -- curl --data-urlencode "query=$1" --data-urlencode "step=10" --data-urlencode "start=$START_TIME" --data-urlencode "end=$END_TIME" http://localhost:9090/api/v1/query_range 
}

promqlQuery "histogram_quantile(0.99, sum(rate(etcd_disk_backend_commit_duration_seconds_bucket{job=\"etcd\"}[2m])) by (instance, le))" > etcd_disk_backend_commit_duration_seconds_bucket
~~~

## Adding Extracted Metrics to Grafana

Copy the extracted metrics file to `dataserv/data/promql`.  The files will be read in under the `promql result reader` data source in grafana.