# Relation endpoints

### grafana-dashboard

_Interface_: grafana-dashboard

_Supported charms_: [grafana-k8s](https://charmhub.io/grafana-k8s)

Grafana is an open-source visualization tool that allows to query, visualize, alert on, and visualize metrics from mixed datasources in configurable dashboards for observability. This charm is shipped with its own Grafana dashboard and supports integration with the [Grafana Operator](https://charmhub.io/grafana-k8s) to simplify observability.

Grafana-dashboard relation enables quick dashboard access already tailored to
fit the needs of operators to monitor the charm. Modifications to the dashboard can be made but will not be
persisted upon restart/redeployment of the charm.

Grafana-Prometheus integrate command:
```
juju integrate grafana-k8s:grafana-source prometheus-k8s:grafana-source
```
Grafana-dashboard integrate command:
```
juju integrate content-cache-k8s grafana-dashboard`
```

### ingress

_Interface_: ingress

_Supported charms_: [nginx-ingress-integrator](https://charmhub.io/nginx-ingress-integrator),
[traefik](https://charmhub.io/traefik-k8s)

The Content-cache charm also supports being integrated with [Ingress](https://kubernetes.io/docs/concepts/services-networking/ingress/#what-is-ingress) by using [NGINX Ingress Integrator](https://charmhub.io/nginx-ingress-integrator/).

Ingress manages external HTTP/HTTPS access to services in a Kubernetes cluster.
In this case, an existing Ingress controller is required. For more information, see [Adding the Ingress Relation to a Charm](https://charmhub.io/nginx-ingress-integrator/docs/adding-ingress-relation). Documentation to enable ingress in MicroK8s can be found in
[Addon: Ingress](https://microk8s.io/docs/addon-ingress).

Ingress integrate command: 
```
juju integrate content-cache-k8s nginx-ingress-integrator
```

### logging

_Interface_: loki_push_api  
_Supported charms_: [loki-k8s](https://charmhub.io/loki-k8s)

Loki is an open-source fully-featured logging system. This charm is shipped with support for the [Loki Operator](https://charmhub.io/loki-k8s) to collect the generated logs.

The logging relation is a part of the COS relation to enhance logging observability. Logging relation through the `loki_push_api` interface installs and runs promtail which ships the
contents of local logs found at `/var/log/apache2/access.log` and `/var/log/apache2/error.log` to Loki.
This can then be queried through the Loki API or easily visualized through Grafana. Learn more about COS
[here](https://charmhub.io/topics/canonical-observability-stack).

Logging-endpoint integrate command: 
```
juju integrate content-cache-k8s loki-k8s
```


### metrics-endpoint

_Interface_: [prometheus_scrape](https://charmhub.io/interfaces/prometheus_scrape-v0)

_Supported charms_: [prometheus-k8s](https://charmhub.io/prometheus-k8s)

Prometheus is an open-source system monitoring and alerting toolkit with a dimensional data model, flexible query language, efficient time series database, and modern alerting approach. This charm is shipped with a Prometheus exporter, alerts, and support for integrating with the [Prometheus Operator](https://charmhub.io/prometheus-k8s) to automatically scrape the targets.

Metrics-endpoint relation allows scraping the `/metrics` endpoint provided by the charm.
The metrics are exposed in the [open metrics format](https://github.com/OpenObservability/OpenMetrics/blob/main/specification/OpenMetrics.md#data-model) and will only be scraped by Prometheus once the
relation becomes active.

Metrics-endpoint integrate command: 
```
juju integrate content-cache-k8s prometheus-k8s
```
