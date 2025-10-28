---
# Copyright Vespa.ai. All rights reserved.
title: "Exposing schema information"
---

Some applications need to expose information about schemas to data plane clients.
This document explains how to add an API for that to your application.

You need to know two things:
* Your application can expose any custom API by implementing a
  [handler](/en/jdisc/developing-request-handlers.html).* Information about the deployed schemas are available in the component *com.yahoo.search.schema.SchemaInfo*.

With this information, we can add an API exposing schemas information through the following steps.

## 1. Make sure your application package can contain Java components

Application packages containing Java components must follow Maven layout.
If your application package root contains a `pom.xml` and `src/main`
you're good, otherwise convert it to this layout by copying the pom.xml from
[the album-recommendation.java](https://github.com/vespa-engine/sample-apps/tree/master/album-recommendation-java)
sample app and moving the files to follow this layout before moving on.

## 2. Add a handler exposing schema info

Add the following handler (to a package of your choosing):

```
{% highlight java %}
package ai.vespa.example;

import com.yahoo.container.jdisc.HttpRequest;
import com.yahoo.container.jdisc.HttpResponse;
import com.yahoo.container.jdisc.ThreadedHttpRequestHandler;
import com.yahoo.jdisc.Metric;
import com.yahoo.search.schema.SchemaInfo;

import java.io.IOException;
import java.io.OutputStream;
import java.nio.charset.Charset;
import java.util.concurrent.Executor;

public class SchemaInfoHandler extends ThreadedHttpRequestHandler {

    private final SchemaInfo schemaInfo;

    public SchemaInfoHandler(Executor executor, Metric metric, SchemaInfo schemaInfo) {
        super(executor, metric);
        this.schemaInfo = schemaInfo;
    }

    @Override
    public HttpResponse handle(HttpRequest httpRequest) {
        // Creating JSON, handling different paths etc. left as an exercise for the reader
        StringBuilder response = new StringBuilder();
        for (var schema : schemaInfo.schemas().values()) {
            response.append("schema: " + schema.name() + "\n");
            for (var field : schema.fields().values())
                response.append("  field: " + field.name() + "\n");
        }
        return new Response(200, response.toString());
    }

    private static class Response extends HttpResponse {

        private final byte[] data;

        Response(int code, byte[] data) {
            super(code);
            this.data = data;
        }

        Response(int code, String data) {
            this(code, data.getBytes(Charset.forName(DEFAULT_CHARACTER_ENCODING)));
        }

        @Override
        public String getContentType() {
            return "application/json";
        }

        @Override
        public void render(OutputStream outputStream) throws IOException {
            outputStream.write(data);
        }

    }

    private static class ErrorResponse extends Response {
        ErrorResponse(int code, String message) {
            super(code, "{\"error\":\"" + message + "\"}");
        }
    }

}
{% endhighlight %}
```

## 3. Add the new API handler to your container cluster

In your `services.xml` file, under `<container>`, add:

```
{% highlight xml %}

        http://*/schema/v1/*

{% endhighlight %}
```

## 4. Deploy the modified application

```
$ mvn install
$ vespa deploy
```

## 5. Verify that it works

```
$ vespa curl "schema/v1/"
```
