---
# Copyright Vespa.ai. All rights reserved.
title: Private endpoints
category: cloud
---

Vespa Cloud lets you set up private endpoint services on your application clusters,
for exclusive access from your own, co-located VPCs with the same cloud provider.
This is supported for AWS deployments through AWS's
[PrivateLink](https://docs.aws.amazon.com/vpc/latest/privatelink/what-is-privatelink.html), and for GCP deployments through GCP's
[Private Service Connect](https://cloud.google.com/vpc/docs/private-service-connect).
This guide takes you through the necessary configuration steps for either
[AWS PrivateLink](#aws-private-link)
or for [GCP Private Service Connect](#gcp-private-service-connect).

Private endpoints are only supported in zones in the
[prod environment](https://cloud.vespa.ai/en/reference/environments#production).

{% include note.html content='
Private endpoints use mTLS authentication by default, and token-based authentication must be explicitly enabled.
See [configuring private endpoint authentication method](#authentication-methods).
'%}

## AWS PrivateLink

Required information:

| Item | Description |
| --- | --- |
| **Your IAM account number** | The numeric identifier for your AWS account. |
| **VPC ID** | The identifier of your AWS VPC where you wish to connect to the service endpoints from. |
| **AWS region name** | The name of the AWS region to connect from. Note that you can only connect to a service in the same region, or, if public endpoints are disabled, in the same AWS availability zone. |

Procedure:

1. **Configure a private endpoint service on your Vespa Cloud Container cluster**

   Add `<endpoint type="private" />`
   to [deployment.xml](https://cloud.vespa.ai/en/reference/deployment#endpoint-private),
   allowing access to the container cluster using the designated ARN from your account.
   The example allows all roles and users under the `123123123123` account
   to connect to the endpoint service on the `my-container` cluster,
   in each region listed under the `<prod>` tag.

   See [endpoint service configuration](https://docs.aws.amazon.com/vpc/latest/privatelink/configure-endpoint-service.html)
   for details on valid ARNs, and more fine-grained access control.

   The example also shows how to disable the public zone endpoint by adding the
   [`"zone"` type endpoint](https://cloud.vespa.ai/en/reference/deployment#endpoint-zone)
   declaration—this is an optional step, and not required to set up the private service

   ```
   {% highlight xml %}


           region-1
           region-2








   {% endhighlight %}
   ```

   Build and deploy the application package, and wait for it to deploy to the indicated regions.
2. **Find the service ID of your endpoint services**

   Navigate to the endpoints tab for your application in the Console,
   and find the service ID for the deployment to which you wish to connect.
   While there, verify that access to connect to the endpoint was granted to the correct ARNs.

   ![Service ID for VPC endpoint](/assets/img/vpc-1.png)
3. **Create the VPC interface endpoint**

   [Create a VPC endpoint](https://docs.aws.amazon.com/cli/latest/reference/ec2/create-vpc-endpoint.html)
   in your VPC. This is your entry point, which forwards connections to your Vespa application through the private network of AWS.
   For this example, assume your VPC has id
   `vpc-123` and resides in the AWS region `us-east-1`, and that the service ID of your
   endpoint service, found in the Console, is `com.amazonaws.vpce.us-east-1.vpce-svc-321`:

   ```
   $ aws ec2 create-vpc-endpoint \
     --region us-east-1 \
     --vpc-id vpc-123 \
     --service-name com.amazonaws.vpce.us-east-1.vpce-svc-321 \
     --vpc-endpoint-type Interface \
     --private-dns-enabled | jq .
   ```

   Note the value of the `VpcEndpointId` field, for verification in the below item.
   This is also where you specify optional security group and subnet IDs; these are omitted here for brevity.
   If creating the VPC endpoint through the AWS console instead, be sure to check "Enable DNS names"!
4. **Verify the VPC endpoint is connected to the Vespa cluster**

   Navigate back to the endpoints tab in the Console, and refresh the page.
   You should now see a new entry representing the connection between your newly created interface endpoint
   and the endpoint service on your container cluster.
   This is the "CONNECTED ENDPOINTS" in the image above.
   Verify the ID matches the value of the `VpcEndpointId` field above.
   The connection is ready when the state is `open`.
5. **Verify your Vespa cluster is reachable from within your VPC**

   The zone endpoint of the designated container cluster should now resolve through private DNS, for any AWS resource
   that is allowed to connect to your VPC endpoint.
   The easiest way to verify this is to run the following Python 3.9 lambda,
   using your own zone endpoint, from within your VPC:

   ```
   from socket import gethostbyname
   from urllib.request import urlopen

   def lambda_handler(event, context):
       return {
           'statusCode': 200,
           'body': urlopen('https://badc0ffee.deadbeef.z.vespa-app.cloud/status.html').read(),
           'ip': gethostbyname('badc0ffee.deadbeef.z.vespa-app.cloud')
       }
   ```

   Alternatively, run a couple of commands from a host inside the VPC:

   ```
   $ host my-container.my-app.my-tenant.region-1.z.vespa-app.cloud
   $ curl https://my-container.my-app.my-tenant.region-1.z.vespa-app.cloud/status.html
   ```

   In both cases, the IP should be in one of the private IP ranges, and the HTTP response from the
   Vespa container endpoint should be `OK`.

{% include note.html content='
Enclave users may set up high-availability PrivateLink endpoints connected across multiple AZs. Contact
[Vespa support](https://vespa.ai/support/) for guidance.
'%}

## GCP Private Service Connect

Prerequisites:

| Item | Description |
| --- | --- |
| **Enabled GCP APIs** | The *Compute Engine*, *Service Directory* and *Cloud DNS* APIs must all be enabled in your GCP account:  ``` $ gcloud services enable compute.googleapis.com $ gcloud services enable dns.googleapis.com $ gcloud services enable servicedirectory.googleapis.com ``` |
| **Your GCP project name** | The string identifier for your GCP account, like *resonant-diode-123456* |
| **VPC network and subnetwork names** | The name of the network and subnetwork to create your consumer endpoint in. |

Procedure:

1. **Configure a private endpoint service on your Vespa Cloud Container cluster**

   Add `<endpoint type="private"/>`
   to [deployment.xml](https://cloud.vespa.ai/en/reference/deployment#endpoint-private),
   allowing access to the container cluster from the GCP account with the designated project ID.
   The example below allows consumer endpoints created under the `private-test` account
   to connect to the endpoint service on the `my-container` cluster,
   in each region listed under the `<prod>` tag.

   The example also shows how to disable the public zone endpoint by adding the
   [`"zone"` type endpoint](https://cloud.vespa.ai/en/reference/deployment#endpoint-zone)
   declaration—this is an optional step, and not required to set up the private service

   ```
   {% highlight xml %}


           region-1
           region-2








   {% endhighlight %}
   ```

   Build and deploy the application package, and wait for it to deploy to the indicated regions.
2. **Find the service ID of your endpoint services**

   Navigate to the endpoints tab for your application in the Console,
   and find the service ID for the deployment to which you wish to connect.
   While there, verify that access to connect to the endpoint was granted to the correct projects.

   ![Service ID for VPC endpoint](/assets/img/vpc-2.png)
3. **Create the service consumer endpoint**

   [Create a service consumer endpoint](https://cloud.google.com/vpc/docs/configure-private-service-connect-services)
   in your VPC. This is your entry point, which forwards connections to your Vespa application through the private GCP network.
   In this example, the project is named
   `test-project`, has a VPC network named
   `test-network` that resides in the GCP region `us-central1`, with a subnet `test-subnet`
   to hold the endpoint, behind an address to be named `test-address`, and the service ID of the
   endpoint service (found in the Console) is
   `projects/vespa-external/regions/us-central1/serviceAttachments/scsa-xxxxxx`.
   Finally, the endpoint is named `badc0ffee`, and the service directory namespace is `my-tenant-my-app`.
   See the discussion on generated endpoint names in the last item in this guide.

   Create network (if it does not already exist):

   ```
   $ gcloud compute networks create test-network
   ```

   Create subnet (if it does not already exist):

   ```
   $ gcloud compute networks subnets create test-subnet \
       --region=us-central1 \
       --network=test-network \
       --range=10.10.0.0/24
   ```

   Create the IP address which will be used for the endpoint, for clients inside your VPC:

   ```
   $ gcloud compute addresses create test-address \
       --region=us-central1 \
       --subnet=test-subnet
   ```

   Create a forwarding rule for traffic to the above IP, to the service endpoint in Vespa Cloud:

   ```
   $ gcloud compute forwarding-rules create badc0ffee \
       --region=us-central1 \
       --network=test-network \
       --address=test-address \
       --target-service-attachment=projects/vespa-external/regions/us-central1/serviceAttachments/scsa-xxxxxx \
       --service-directory-registration=projects/test-project/locations/us-central1/namespaces/my-tenant-my-app
   ```

   Note the ID of the created resource, for the verification step below.
4. **Verify the VPC endpoint is connected to the Vespa cluster**

   Navigate back to the endpoints tab in the Console, and refresh the page.
   You should now see a new entry representing the connection between your newly created interface endpoint,
   and the endpoint service on your container cluster.
   This is the "CONNECTED ENDPOINTS" in the image above.
   Verify the ID matches the resource ID of the forwarding rule created above.
   The connection is ready when the state is `open`.
5. **Verify your Vespa cluster is reachable from within your VPC**

   The generated endpoint name (see last items) of the designated container cluster should now resolve
   through private DNS inside your VPC.
   The easiest way to verify this is to launch an instance in your VPC, inside the designated subnet,
   and run a couple of commands from it:

   ```
   $ host badc0ffee.deadbeef.z.vespa-app.cloud
   $ curl https://badc0ffee.deadbeef.z.vespa-app.cloud/status.html
   ```

   The resolved IP address should be that of the address created earlier, and the `curl` command
   should simply output `OK`.

   If the endpoint fails to resolve, refer to
   [GCP's troubleshooting documentation](https://cloud.google.com/vpc/docs/configure-private-service-connect-services#troubleshooting).
6. **Generated endpoints with Private Service Connect**

   When a consumer endpoint is created with a *Service Directory* namespace, GCP automatically creates
   a private DNS record for that endpoint, which must be used instead of the IP address (created above) of the endpoint,
   as Vespa application containers have web certificates matching specific domain names.
   Unfortunately, we are unable to set the final endpoint names for the consumer endpoint.
   For a private endpoint service, we can only set a domain name *suffix*, and GCP then generates private
   DNS records matching *your endpoint resource name prepended to this suffix*.
   The Service Directory namespace of these endpoints *must also be one-to-one* with their domain name suffixes,
   lest the automatic setup fail.

   The domain name suffix used by Vespa Cloud is
   `[<tenant-and-app-anonymous-id>.].z.vespa-app.cloud`. We therefore encourage using the
   `<tenant>-<application>` pair as the service directory namespace,
   as this ensures a one-to-one mapping between suffixes and namespaces, as required by GCP (see above).

   The Vespa Cloud web certificates (see above) match any direct descendant of the domain suffix we set for your services.
   Thus, any endpoint resource name yields a private DNS record that matches the web certificate, with Service Directory.
   Moreover, the zone endpoints generated by Vespa Cloud consist of a random, unique cluster-instance-region ID.
   Using this same ID as the GCP endpoint resource name (as in the example) results in identical domain names for
   the private DNS set up by GCP, and the endpoint names generated by Vespa Cloud, visible in our console.

## Configuring Private Endpoint Authentication

You can configure private endpoints to use either mTLS or token-based authentication
with the optional `auth-method` attribute. If the attribute is not set, mTLS will be used by default.
The attribute is only allowed with `private` type endpoints and must
be either `mtls` or `token`.

{% include note.html content='
Only one authentication method can be enabled at the same time.
Enabling token authentication will disable mTLS authentication for the private endpoint, and vice versa.
'%}

#### Example with token-based authentication

```
{% highlight xml %}


        region-1
        region-2







{% endhighlight %}
```

#### Changing authentication method for an existing deployment

If you have an existing deployment with a private endpoint, you must remove any connections and redeploy with a
[validation override](/en/reference/validation-overrides.html)
to modify the authentication method:

1. Remove the VPC interface endpoint (AWS) or service consumer endpoint (GCP) configured above
2. Change the authentication method for the endpoint in `deployment.xml`
3. Deploy with the `zone-endpoint-change` validation override:

```
{% highlight xml %}


        zone-endpoint-change


{% endhighlight %}
```
