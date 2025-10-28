---
# Copyright Vespa.ai. All rights reserved.
title: "Server Tutorial"
redirect_from:
- /en/reference/server-tutorial.html
---

How to run an arbitrary server in the Container.
Familiarity with the [Developer Guide](../developer-guide.html) is assumed.

## JDisc servers

JDisc servers are the most abstract level in JDisc, they are an arbitrary service with a life cycle.
JDisc will start the service and stop the service as required,
but what the service actually does is fully up to the user.
JDisc only handles basic infrastructure in this case, and makes no assumptions about what a service is.

## The server class

Set up a project as in the [Developer Guide](../developer-guide.html),
then create `hello_world/components/src/main/java/com/mydomain/demo/HelloWorldServer.java`:

```
{% highlight java %}
package com.mydomain.demo;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.ServerSocket;
import java.net.Socket;
import java.nio.charset.Charset;
import java.util.logging.Logger;
import java.util.logging.Level;

import com.yahoo.jdisc.service.AbstractServerProvider;
import com.yahoo.jdisc.service.CurrentContainer;

/**
 * Dummy server sort of compatible with HTTP.
 */
public class HelloWorldServer extends AbstractServerProvider {
    private final Logger logger = Logger.getLogger(HelloWorldServer.class.getName());
    private Listener daemon;
    private final int port;
    private final byte[] response;
    private static final Charset charset = Charset.forName("utf-8");
    private static final byte[] header = ("HTTP/1.1 200 OK\r\n"
            + "Connection: close\r\n"
            + "Content-Type: text/html\r\n"
            + "\r\n").getBytes(charset);
    private final ServerSocket serverSocket;

    private class Listener implements Runnable {
        private final Logger logger = Logger.getLogger(Listener.class.getName());
        private final ServerSocket server;
        private volatile boolean shutdown = false;
        private final byte[] response;

        public Listener(ServerSocket s, byte[] response) {
            server = s;
            this.response = response;
        }

        public void run() {
            while (!shutdown) {
                Socket clientSocket;
                try {
                    clientSocket = server.accept();
                } catch (IOException e) {
                    logger.log(Level.WARNING, "Failure while accepting connection.", e);
                    continue;
                }
                try {
                    BufferedReader in = new BufferedReader(new InputStreamReader(clientSocket.getInputStream(),
                            charset));
                    OutputStream out = clientSocket.getOutputStream();

                    in.readLine();
                    out.write(header);
                    out.write(response);
                    out.flush();
                } catch (IOException e) {
                    logger.log(Level.WARNING, "Could not write to client.", e);
                } finally {
                    try {
                        clientSocket.close();
                    } catch (IOException e) {
                        logger.log(Level.WARNING, "Error while closing client socket.", e);
                    }
                }
            }
        }

        public void stop() {
            shutdown = true;
            try {
                server.close();
            } catch (IOException e) {
                // just ignore it
            }
        }

    }

    public HelloWorldServer(CurrentContainer container, HelloWorldServerConfig config) {
        super(container);
        port = config.port();
        response = config.response().getBytes(charset);
        try {
            serverSocket = new ServerSocket(port);
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
    }

    @Override
    public void start() {
        daemon = new Listener(serverSocket, response);
        Thread daemonThread = new Thread(daemon);
        daemonThread.setDaemon(true);
        daemonThread.start();
    }

    @Override
    public void close() {
        if (daemon == null) {
            logger.log(Level.ERROR, "HelloWorldServer.close() invoked without successful start()");
        } else {
            daemon.stop();
        }
    }
}
{% endhighlight %}
```

The important part is the class `com.yahoo.jdisc.service.AbstractServerProvider`.
This provides wiring, so it is possible for JDisc to do life cycle management,
while the example is left to implement the actual server.
A server is defined by the interface `com.yahoo.jdisc.service.ServerProvider`,
it contains only two methods: `void start()` and `void close()`.
A server can in other words be pretty much anything,
the container just makes life cycle management, reconfiguration and so on available as needed.

## The configuration class

The demo server requires a custom configuration class, it is defined in
`components/src/main/resources/configdefinitions/hello-world-server.def`:

```
package=com.mydomain.demo

response string default="No config value given."
port int
```

Notice how hyphens in the file name are converted to camel-casing in the generated class name.

## The application

```
{% highlight xml %}



            Hello, world!
            16889



{% endhighlight %}
```

Everything is pretty much the same as when writing a basic handler, though,
as the server is not directly connected to HTTP, it has no binding.
Our custom configuration configures the HelloWorldServer to bind to port 16889.
