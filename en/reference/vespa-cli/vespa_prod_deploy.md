---
title: vespa prod deploy
render_with_liquid: false
---

## vespa prod deploy

Deploy an application to production

### Synopsis

Deploy an application to production.

This commands uploads an application package to Vespa Cloud and deploys it to
the production zones specified in deployment.xml.

Nodes are allocated to the application according to resources specified in
services.xml.

For more information about production deployments in Vespa Cloud see:
[https://cloud.vespa.ai/en/production-deployment](https://cloud.vespa.ai/en/production-deployment)
[https://cloud.vespa.ai/en/automated-deployments](https://cloud.vespa.ai/en/automated-deployments)
[https://cloud.vespa.ai/en/reference/vespa-cloud-api#submission-properties](https://cloud.vespa.ai/en/reference/vespa-cloud-api#submission-properties)


```
vespa prod deploy [application-directory-or-file] [flags]
```

### Examples

```
$ mvn package # when adding custom Java components
$ vespa prod deploy
```

### Options

```
  -A, --add-cert              Copy certificate of the configured application to the current application package (default false)
      --author-email string   Email of the author of the commit being deployed
      --commit string         Identifier of the source code being deployed. For example a commit hash
      --description string    Description of the source code being deployed. For example a git commit message
  -h, --help                  help for deploy
      --risk int              The risk score of source code being deployed. 0 to ignore (default 0)
      --source-url string     URL which points to the source code being deployed. For example the build job running the submission
```

### Options inherited from parent commands

```
  -a, --application string   The application to use (cloud only). Format "tenant.application.instance" - instance is optional
  -C, --cluster string       The container cluster to use. This is only required for applications with multiple clusters
  -c, --color string         Whether to use colors in output. Must be "auto", "never", or "always" (default "auto")
  -i, --instance string      The instance of the application to use (cloud only)
  -q, --quiet                Print only errors
  -t, --target string        The target platform to use. Must be "local", "cloud", "hosted" or an URL (default "local")
  -z, --zone string          The zone to use. This defaults to a dev zone (cloud only)
```

### SEE ALSO

* [vespa prod](vespa_prod.html)	 - Deploy an application package to production in Vespa Cloud

