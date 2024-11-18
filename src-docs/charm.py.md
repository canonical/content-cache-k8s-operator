<!-- markdownlint-disable -->

<a href="../src/charm.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `charm.py`
Charm for Content-cache on Kubernetes. 

**Global Variables**
---------------
- **REQUIRED_INGRESS_RELATION_FIELDS**
- **CACHE_PATH**
- **CONTAINER_NAME**
- **EXPORTER_CONTAINER_NAME**
- **CONTAINER_PORT**
- **REQUIRED_JUJU_CONFIGS**


---

## <kbd>class</kbd> `ContentCacheCharm`
Charm the service. 

Attrs:  on: Ingress Charm Events  ERROR_LOG_PATH: NGINX error log  ACCESS_LOG_PATH: NGINX access log  _metrics_endpoint: Provider of metrics for Prometheus charm  _logging: Requirer of logs for Loki charm  _grafana_dashboards: Dashboard Provider for Grafana charm  nginx_proxy_provides: Ingress proxy provider  ingress: Ingress requirer  unit: Charm's designated juju unit  model: Charm's designated juju model 

<a href="../src/charm.py#L65"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `__init__`

```python
__init__(*args)
```

Init function for the charm. 



**Args:**
 
 - <b>`args`</b>:  Variable list of positional arguments passed to the parent constructor. 


---

#### <kbd>property</kbd> app

Application that this unit is part of. 

---

#### <kbd>property</kbd> charm_dir

Root directory of the charm as it is running. 

---

#### <kbd>property</kbd> config

A mapping containing the charm's config and current values. 

---

#### <kbd>property</kbd> meta

Metadata of this charm. 

---

#### <kbd>property</kbd> model

Shortcut for more simple access the model. 

---

#### <kbd>property</kbd> unit

Unit that this execution is responsible for. 



---

<a href="../src/charm.py#L224"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `configure_workload_container`

```python
configure_workload_container(event: ConfigChangedEvent) → None
```

Configure/set up workload container inside pod. 



**Args:**
 
 - <b>`event`</b>:  config-changed event. 


