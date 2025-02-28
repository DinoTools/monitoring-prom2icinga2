# Config

There are two environment variables available to specify the location of the configuration files.

* PROM2ICINGA2_CONFIG - The base config
* PROM2ICINGA2_CHECK_CONFIG - The check config

Example:

```
PROM2ICINGA2_CHECK_CONFIG=checks.yaml PROM2ICINGA2_CONFIG=config.toml
```

## Base config

You can specify the base configuration using a file, environment variables, or a combination of both methods.
Currently, configuration files in TOML and YAML formats are supported. You have to install the Python toml module to
use TOML files.

```toml
[icinga2]
url="https://localhost:5665/"
username="icinga2"
password="password"
ssl_verify=true

[prometheus]
url="http://localhost:9090/"
```

To set the Icinga2 password using an environment variable, follow the example provided below.

```
PROM2ICINGA2__ICINGA2__PASSWORD="your-password"
```


## Define checks

ToDo
