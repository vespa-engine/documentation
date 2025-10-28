---
# Copyright Vespa.ai. All rights reserved.
title: "Multinode systems"
category: oss
redirect_from:
- /en/multinode-systems.html
- /en/vespa-quick-start-multinode-aws.html
- /en/vespa-quick-start-multinode-aws-ecs.html
- /en/operations/multinode-systems.html
---

A Vespa *system* consists of one or more stateless and stateful clusters configured by an application package.
A Vespa system is configured and managed through an admin cluster as shown below.

![Vespa Overview](/assets/img/vespa-overview.svg)

All nodes of a Vespa system have the same software installed.
Which processes are started on each node and how they are configured
is determined by the admin cluster from the specification given in
[services.xml](../reference/services.html) in the application package.

## Creating a multinode system from a sample application

To create a fully functional production ready multinode system from a single-node sample application,
follow these steps (also see [next steps](#next-steps)):

1. Add an [admin cluster](../reference/services-admin.html) in services.xml:

   ```
   {% highlight xml %}



















   {% endhighlight %}
   ```
2. Install the Vespa packages or the *vespaengine/vespa* Docker image on all the nodes.
3. Run

   ```
   $ echo "override VESPA_CONFIGSERVERS [configserver-hostnames]" >> $VESPA_HOME/conf/vespa/default-env.txt
   ```

   where `[configserver-hostnames]` is replaced by the full hostname of the config server
   (or a comma-separated list if multiple).
4. Add these nodes to the container and content clusters
   by adding more `node` tags in *services.xml*.
5. Add the same nodes to *hosts.xml*.
6. Start Vespa on the nodes

See below for AWS examples.
Refer to [configuration server operations](/en/operations-selfhosted/configuration-server.html) for troubleshooting.

## AWS EC2

The following is a procedure to set up a multinode application on *AWS EC2* instances.
Please run the procedure in
[multinode-HA](https://github.com/vespa-engine/sample-apps/tree/master/examples/operations/multinode-HA)
first, to get familiar with the different Vespa concepts before running the AWS procedure below.
This procedure will use the name number of hosts, 10, and set up the same application.

{% include important.html content='Note the use of `sudo`.
The Vespa start scripts will modify the environment (directories, system limits), requiring root access -
refer to [vespa-start-configserver](/en/operations-selfhosted/vespa-cmdline-tools.html#vespa-start-configserver)
and [vespa-start-services](/en/operations-selfhosted/vespa-cmdline-tools.html#vespa-start-services).
After the environment setup, Vespa is run as the `vespa` user.' %}
{% include note.html content="The procedure below is a bare minimum, for educational purposes.
Make sure to use AWS instance types suitable for the application load,
and implement security mechanisms of choice." %}

Can [AWS Auto Scaling](https://aws.amazon.com/autoscaling/) be used?
Read the [autoscaling Q/A](#autoscaling).

### Node setup
* Provision nodes:
  + Find AMI at [CentOS AWS AMI Cloud Images](https://centos.org/download/aws-images/) -
    this procedure is tested with *CentOS Stream 8 us-east-1 x86_64 ami-0ee70e88eed976a1b*
    and vespa-8.30.50.
  + Use minimum *t2.medium* instances.
  + Let AWS create a security group for the nodes, or use an existing one.
  + Make sure to check for SSH traffic, for host login.
  + Launch 10 instances - the 3 first will be Vespa config server nodes, the 7 last Vespa nodes.
    Write down private / public hostnames.
    The private names are used in Vespa configuration, the public names for login to check status.
    To find a hostname, click the instance
    and copy hostname from *Private IP DNS name (IPv4 only)* and *Public IPv4 DNS*.
    Create a table like:

    | type | Private IP DNS name (IPv4 only) | Public IPv4 DNS |
    | --- | --- | --- |
    | configserver | ip-10-0-1-234.ec2.internal | ec2-3-231-33-190.compute-1.amazonaws.com |
    | configserver | ip-10-0-1-154.ec2.internal | ec2-3-216-28-201.compute-1.amazonaws.com |
    | configserver | ip-10-0-0-88.ec2.internal | ec2-34-230-33-42.compute-1.amazonaws.com |
    | services | ip-10-0-1-95.ec2.internal | ec2-44-192-98-165.compute-1.amazonaws.com |
    | services | ip-10-0-0-219.ec2.internal | ec2-3-88-143-47.compute-1.amazonaws.com |
    | services | ip-10-0-0-28.ec2.internal | ec2-107-23-52-245.compute-1.amazonaws.com |
    | services | ip-10-0-0-67.ec2.internal | ec2-54-198-251-100.compute-1.amazonaws.com |
    | services | ip-10-0-1-84.ec2.internal | ec2-44-193-84-85.compute-1.amazonaws.com |
    | services | ip-10-0-0-167.ec2.internal | ec2-54-224-15-163.compute-1.amazonaws.com |
    | services | ip-10-0-1-41.ec2.internal | ec2-44-200-227-127.compute-1.amazonaws.com |
* Security group setup:
  + Click the Security Group for the nodes just provisioned (under the security tab),
    then *Edit inbound rules*.
    Add *All TCP* for port range 0-65535, specifying the name of the current Security Group as the Source.
    This lets the hosts communicate with each other.
* Host login example, without ssh-agent:

  ```
  $ SSH_AUTH_SOCK=/dev/null ssh -i mykeypair.pem centos@ec2-3-231-33-190.compute-1.amazonaws.com
  ```
* On each of the 10 hosts,
  install Vespa using the [install procedure](../build-install-vespa.html#rpms):

  ```
  $ sudo dnf config-manager \
    --add-repo https://raw.githubusercontent.com/vespa-engine/vespa/master/dist/vespa-engine.repo
  $ sudo dnf config-manager --enable powertools
  $ sudo dnf install -y epel-release
  $ sudo dnf install -y vespa
  $ export VESPA_HOME=/opt/vespa
  ```
* On all the 10 hosts, set up the environment using the config server host list:

  ```
  $ echo "override VESPA_CONFIGSERVERS" \
    "ip-10-0-1-234.ec2.internal,ip-10-0-1-154.ec2.internal,ip-10-0-0-88.ec2.internal" \
    | sudo tee -a $VESPA_HOME/conf/vespa/default-env.txt
  ```

  It is required that all nodes, both config server and Vespa nodes,
  have the same setting for `VESPA_CONFIGSERVERS`.

### Config server cluster setup
* Start the 3-node config server cluster:

  ```
  $ sudo systemctl start vespa-configserver
  ```
* Verify the config cluster is running - on one of the config server nodes:

  ```
  $ for configserver in \
    ip-10-0-1-234.ec2.internal \
    ip-10-0-1-154.ec2.internal \
    ip-10-0-0-88.ec2.internal; \
    do curl -s http://$configserver:19071/state/v1/health | head -5; done

  {
    "time" : 1660034756595,
    "status" : {
      "code" : "up"
    },
  {
    "time" : 1660034756607,
    "status" : {
      "code" : "up"
    },
  {
    "time" : 1660034756786,
    "status" : {
      "code" : "up"
    },
  ```

  A successful config server start will log an entry like:

  ```
  $ $VESPA_HOME/bin/vespa-logfmt | grep "Application config generation"

    [2022-08-09 08:29:38.684] INFO    : configserver
    Container.com.yahoo.container.jdisc.ConfiguredApplication
    Switching to the latest deployed set of configurations and components.
    Application config generation: 0
  ```

  Do not continue setup before the config server cluster is successfully started.
  See the video: [Troubleshooting startup - multinode](https://www.youtube.com/embed/BG7XZmXpIzo) and read
  [config server start sequence](/en/operations-selfhosted/configuration-server.html#start-sequence).
* Start Vespa services on the 3 config server nodes - this starts basic Vespa services like log forwarding:

  ```
  $ sudo systemctl start vespa
  ```
  *$VESPA_HOME/logs/vespa/vespa.log* will now contain messages for
  `APPLICATION_NOT_LOADED`,
  this is normal until an application is deployed (next section).

### Configure application
* Configure the sample application - on one of the config server nodes:

  ```
  $ sudo dnf install -y git zip
  $ git clone https://github.com/vespa-engine/sample-apps.git && \
    cd sample-apps/examples/operations/multinode-HA
  ```
* Edit *hosts.xml* - replace the *nodeX.vespanet* names.
  Let the 3 first hosts be the config server hosts above, the 7 rest the Vespa hosts - example:

  ```
  {% highlight xml %}
    xml version="1.0" encoding="utf-8" ?



          node0


          node1


          node2




          node3



          node4


          node5



          node6


          node7



          node8


          node9


  {% endhighlight %}
  ```
* Deploy the application:

  ```
  $ zip -r - . -x "img/*" "scripts/*" "pki/*" "tls/*" README.md .gitignore | \
    curl --header Content-Type:application/zip --data-binary @- \
    http://localhost:19071/application/v2/tenant/default/prepareandactivate
  ```

  Expected output:

  ```
  {% highlight json %}
  {
      "log": [],
      "tenant": "default",
      "url": "http://localhost:19071/application/v2/tenant/default/application/default/environment/prod/region/default/instance/default",
      "message": "Session 2 for tenant 'default' prepared and activated.",
      "configChangeActions": {
          "restart": [],
          "refeed": [],
          "reindex": []
      }
  }
  {% endhighlight %}
  ```

### Vespa nodes setup
* Start Vespa on the 7 hosts:

  ```
  $ sudo systemctl start vespa
  ```
* Validate the installation.
  Use the [multinode-HA](https://github.com/vespa-engine/sample-apps/tree/master/examples/operations/multinode-HA) steps to check the health interfaces on all 10 nodes.
  Note that in this guide, the ports are not mapped through a Docker container,
  so the native Vespa ports should be used - e.g. for nodes 4 to 7 (see illustration below):

  ```
  $ curl http://localhost:8080/state/v1/health

  {
    "time" : 1660038306465,
    "status" : {
      "code" : "up"
    },
  ```

  Refer to the sample application ports:
  ![Sample application ports](https://raw.githubusercontent.com/vespa-engine/sample-apps/master/examples/operations/multinode-HA/img/multinode-HA.svg)

### Terminate instances

Remember to terminate the instances in the AWS console after use.

### AWS EC2 singlenode

This is a variant of the multinode install, using only one host,
running both a config server and the other Vespa services on the same node.
* Provision a node, minimum a *t2.large*.
  Get its hostname for use in `VESPA_CONFIGSERVERS`:

  ```
  $ hostname
  ```
* Install Vespa:

  ```
  $ sudo dnf config-manager \
    --add-repo https://raw.githubusercontent.com/vespa-engine/vespa/master/dist/vespa-engine.repo
  $ sudo dnf config-manager --enable powertools
  $ sudo dnf install -y epel-release
  $ sudo dnf install -y vespa
  $ export VESPA_HOME=/opt/vespa
  $ echo "override VESPA_CONFIGSERVERS ip-172-31-95-248.ec2.internal" | \
    sudo tee -a $VESPA_HOME/conf/vespa/default-env.txt
  ```
* Get a sample application:

  ```
  $ sudo dnf install -y git zip
  $ git clone https://github.com/vespa-engine/sample-apps.git && cd sample-apps/album-recommendation
  ```
* Start the config server, check health port after a few seconds:

  ```
  $ sudo systemctl start vespa-configserver
  $ curl http://localhost:19071/state/v1/health | head -5
  ```
* Deploy the sample application:

  ```
  $ zip -r - . -x "img/*" "scripts/*" "pki/*" "tls/*" README.md .gitignore | \
    curl --header Content-Type:application/zip --data-binary @- \
    http://localhost:19071/application/v2/tenant/default/prepareandactivate
  ```
* Start Vespa, check container node health after some seconds:

  ```
  $ sudo systemctl start vespa
  $ curl http://localhost:8080/state/v1/health | head -5
  ```
* Remember to terminate the instances in the AWS console after use.

## AWS ECS

The following is a procedure to set up a multinode application on
[AWS ECS](https://us-east-1.console.aws.amazon.com/ecs) instances.
Please run the procedure in
[multinode-HA](https://github.com/vespa-engine/sample-apps/tree/master/examples/operations/multinode-HA)
first, to get familiar with the different Vespa concepts before running the AWS procedure below.
This procedure will use the name number of host, 10, and set up the same application.
Running the [EC2 procedure](#aws-ec2) above can also be helpful,
this procedure has a similar structure.

### Create a 10-node ECS cluster
* Log in to AWS and the EC2 Container Service.
  Click *Clusters > Create Cluster > EC2 Linux + Networking > Next step*, using the defaults and:

  | Cluster name | vespa |
  | EC2 instance type | t2.medium |
  | Number of instances | 10 |
  | Key pair | *Select or create your keypair* |
  | Security group inbound rules - port range | 0 - 65535 |
* Click *Create*, wait for the tasks to succeed, then *View Cluster* -
  it should say *Registered container instances: 10* in ACTIVE state.

### Configure ECS instances
* Click the *ECS Instances tab* - this should list 10 container instances.
* Select the 3 first Container Instance checkboxes,
  then *Actions > View/Edit attributes*.
* Click *Add attribute*.
  Set `Name=type` and `Value=configserver`,
  click the green checkbox on the right, then *Close*.
* Select the next 7 Container instance checkboxes,
  then *Actions > View/Edit attributes*.
* Click *Add attribute*.
  Set `Name=type` and `Value=services`,
  click the green checkbox on the right, then *Close*.
* Write down private / public hostnames and create a table like in the [EC2 procedure](#node-setup)
  The private names are used in Vespa configuration, the public names for login to check status.
  To find a hostname, click *ECS Instance > Instance ID*
  and copy hostname from *Private IP DNS name (IPv4 only)* and *Public IPv4 DNS*.

### Start the config server task
* Click *Task Definitions > Create new Task Definition > EC2 > Next step*.
* Click *Configure via JSON* and replace the content with
  (note the comma-separated hostnames of the config servers addresses):

  ```
  {
      "networkMode": "host",
      "containerDefinitions": [
          {
              "name": "configserver",
              "environment": [
                  {
                      "name": "VESPA_CONFIGSERVERS",
                      "value": "ip-10-0-1-234.ec2.internal,ip-10-0-1-154.ec2.internal,ip-10-0-0-88.ec2.internal"
                  }
              ],
              "image": "vespaengine/vespa",
              "privileged": true,
              "memoryReservation": 1024
          }
      ],
      "placementConstraints": [
          {
              "expression": "attribute:type == configserver",
              "type": "memberOf"
          }
      ],
      "family": "configserver"
  }
  ```
* Click *Save > Create*.
* Choose *Actions -> Run task* and configure:

  | Launch type | EC2 |
  | Cluster | vespa |
  | Number of tasks | 3 |
  | Placement templates | One Task Per Host |
* Click *Run Task*.
* Validate that the config servers started successfully -
  use the same procedure as for [EC2 instances](#config-server-cluster-setup),
  checking */state/v1/health*.
  Do not continue before successfully validating this:

  ```
  $ ssh -i mykeypair.pem ec2-user@ec2-3-231-33-190.compute-1.amazonaws.com \
    curl -s http://localhost:19071/state/v1/health | head -5

  {
      "time" : 1660635645783,
      "status" : {
        "code" : "up"
      },
  ```

### Configure application - ECS
* Log into a config server:

  ```
  $ ssh -i mykeypair.pem ec2-user@ec2-3-231-33-190.compute-1.amazonaws.com
  ```
* Download the multinode-HA sample application:

  ```
  $ sudo yum -y install git zip
  $ git clone https://github.com/vespa-engine/sample-apps.git && \
    cd sample-apps/examples/operations/multinode-HA
  ```
* Modify *hosts.xml* using the internal DNS hostnames -
  this step is the same as for [EC2 instances](#configure-application)
* Deploy the application:

  ```
  $ zip -r - . -x "img/*" "scripts/*" "pki/*" "tls/*" README.md .gitignore | \
    curl --header Content-Type:application/zip --data-binary @- \
    http://localhost:19071/application/v2/tenant/default/prepareandactivate
  ```

### Start the services tasks
* Click *Task Definitions > Create new Task Definition > EC2 > Next step*.
* Click *Configure via JSON* and replace the content with
  (using the same 3 config server internal DNS names):

  ```
  {
      "networkMode": "host",
      "containerDefinitions": [
          {
              "name": "services",
              "environment": [
                  {
                      "name": "VESPA_CONFIGSERVERS",
                      "value": "ip-10-0-1-234.ec2.internal,ip-10-0-1-154.ec2.internal,ip-10-0-0-88.ec2.internal"
                  }
              ],
              "image": "vespaengine/vespa",
              "command": [
                  "services"
              ],
              "privileged": true,
              "memoryReservation": 1024
          }
      ],
      "placementConstraints": [
          {
              "expression": "attribute:type == services",
              "type": "memberOf"
          }
      ],
      "family": "services"
  }
  ```
* Click *Save > Create*.
  Note the `"command": [ "services" ]`.
  See [controlling which services to start](/en/operations-selfhosted/docker-containers.html#controlling-which-services-to-start)
  for details, this starts *services* only -
  the start script starts both the *configserver* and *services* if given no arguments -
  this is used for the config server above.
  For these 7 nodes, `services` is given as an argument to the start script to only start Vespa services.
* Choose *Actions > Run task* and configure:

  | Launch type | EC2 |
  | Cluster | vespa |
  | Number of tasks | 7 |
  | Placement templates | One Task Per Host |
* Click *Run Task*.
* Validate startup.
  This step is the same as for [EC2 instances](#vespa-nodes-setup),
  e.g. for nodes running a Vespa container the port is 8080:

  ```
  $ ssh -i mykeypair.pem ec2-user@ec2-3-88-143-47.compute-1.amazonaws.com \
    curl -s http://localhost:8080/state/v1/health | head -5

  {
      "time" : 1660652648442,
      "status" : {
        "code" : "up"
      },
  ```

### Terminate cluster
* Remember to delete the cluster in the AWS console after use.

## Log collection

Logs are automatically collected from all nodes in real time to the admin node listed as `adminserver`.
To view log messages from the system,
run [vespa-logfmt](/en/operations-selfhosted/vespa-cmdline-tools.html#vespa-logfmt) on this node.

## Making changes to live systems

To change the system, deploy the changed application to the admin cluster.
The admin cluster will automatically change the participating nodes as necessary.
It is safe to do this while serving live query and write traffic.
In some cases the admin cluster will report that some processes must be restarted to make the change effective.
To avoid query or write traffic disruption,
such restarts must be done on one node at the time,
waiting until the node is fully up before restarting the next one.

## Multiple proton processes

See [multiple schemas](/en/schemas.html#multiple-schemas)
for an overview of how to map schemas to content clusters.
There is another way to distribute load over hosts,
by mapping multiple content clusters to the same hosts:

```
{% highlight xml %}















{% endhighlight %}
```

Observe that both clusters use `node1`.
This is a non-recommended configuration, as it runs multiple [proton](../proton.html) processes per node.
To reduce interference between the processes in this case, virtualize the host into more nodes.
One can use [containers or VMs](/en/operations-selfhosted/docker-containers.html) to do this:

![Multiple proton processes per node](/assets/img/schemas-and-content-clusters-multiple-proton.svg)
{% include important.html content='Vespa\'s features for overload handling,
like [feed-block](/en/operations/feed-block.html),
requires that only one proton process is running on the node.' %}

## Autoscaling

A common question is, *"Can [AWS Auto Scaling](https://aws.amazon.com/autoscaling/) be used?"*
That is a difficult question to answer, here is a transcript from the [Vespa Slack](http://slack.vespa.ai):

> I have a question about deployment.
> I set up cluster on two AWS auto-scaling groups (config & services) based on
> [multinode-systems.html#aws-ec2](#aws-ec2).
> But if one of instances was replaced by auto-scaling group,
> I need manually update hosts.xml file, zip it and deploy new version of the app.
> I'm thinking about automation of this process by Cloudwatch & Lambda...
> I wonder if there is some node-discovery mechanism which can e.g.
> check instances tags and update hosts config based on it?

First, you see in [aws-ec2](#aws-ec2) that there are two types of hosts,
`configserver` and `services`.
configserver setup / operations is documented at
[configuration server operations](/en/operations-selfhosted/configuration-server.html).
This must be set up first.
This is backed by an [Apache ZooKeeper](https://zookeeper.apache.org/) cluster,
so should be 1 or 3 nodes large.
In our own clusters in Yahoo, we do not autoscale configserver clusters, there is no need - we use 3.
If that is too many, use 1. So this question is easy - do not autoscale configservers.

For the services nodes, observe that there are two kinds of nodes -
stateless containers and stateful content nodes -
see the [overview](../overview.html).
In any way, you will want to manage these differently -
the stateless nodes are more easily replaced / increased / shrunk,
by changing *services.xml* and *hosts.xml*.
It is doable to build an autoscaling service for the stateless nodes,
but you need to make sure to use the right metrics for your autoscaling code,
and integrate the deploy-automation with the other deployments (say schema modifications).

A much harder problem is autoscaling the stateful nodes -
these are the nodes with the indexes and data. See [elasticity](../elasticity.html) -
adding a node + data redistribution can take hours,
and the node's load will increase during redistribution.
Building autoscaling here is very difficult to do safely and efficient.

Nothing of this is impossible,
and it is actually implemented at [cloud.vespa.ai/autoscaling](https://cloud.vespa.ai/#autoscaling) -
but it is a difficult feature to get right.

So, my recommendation is starting with a static set of hosts, like in
[multinode-HA](https://github.com/vespa-engine/sample-apps/tree/master/examples/operations/multinode-HA) -
and in parallel try out [cloud.vespa.ai/en/free-trial](https://cloud.vespa.ai/en/free-trial)
with autoscaling experiments using your data and use cases.

Autoscaling can save money, but before going there,
it is wise to read anout [performance](/en/performance/)
and optimize resources using a static node set
(or use the sizing suggestions from the Vespa Cloud Console).
I.e., get the node resources right first,
then consider if autoscaling node count for your load patterns makes sense.

## Next steps
* [Multinode-HA](https://github.com/vespa-engine/sample-apps/tree/master/examples/operations/multinode-HA)
  is a high-availability multi-node template - use this as a basis for the final configuration.
* The [multinode](https://github.com/vespa-engine/sample-apps/tree/master/examples/operations/multinode)
  sample application is a useful for experimenting with node state transitions.
