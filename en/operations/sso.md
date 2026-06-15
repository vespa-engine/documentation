---
# Copyright Vespa.ai. All rights reserved.
title: Single Sign-On
applies_to: cloud
---

Single Sign-On (SSO) is available for Vespa Cloud customers on the [Enterprise plan](https://vespa.ai/pricing/).
It is powered by Auth0's Self-Service Enterprise Configuration and supports the following identity provider connectors:

- **Generic SAML** for any SAML 2.0 compliant identity provider
- **Okta Workforce Identity OIDC** for organizations using Okta as their identity provider

Once SSO is active, users signing in with an email address on the configured domain are automatically redirected to your identity provider.

## Setup process

SSO setup requires involvement from both the customer and the Vespa Support team.
The overall flow is:

1. **Initiate:** Contact [Vespa Support](https://vespa.ai/support/) or your account manager to request SSO setup.
   Include your Vespa Cloud tenant name in the request.

2. **Receive self-service URL:** Vespa Support will provide you with a self-service configuration URL for your tenant.

3. **Validate your domain:** In the self-service portal, you will be given a DNS TXT record to add to your domain.
   This proves ownership of the email domain that will be used for SSO.
   Propagation may take up to 48 hours depending on your DNS provider.

4. **Configure your identity provider:** The self-service portal guides you through the connector-specific setup.
   Follow the on-screen instructions to configure either Generic SAML or Okta OIDC in your identity provider.

5. **Confirm completion:** Once you have completed the configuration, notify Vespa Support.

6. **Activation:** Vespa Support will verify the setup and activate the SSO connection for your tenant.

## After activation

Users authenticating with an email address belonging to your validated domain will be automatically redirected
to your identity provider when signing in to Vespa Cloud.

Users who previously authenticated with username/password or other methods will be required to
authenticate through SSO going forward.

## Getting help

For questions or issues during setup, reach out to [Vespa Support](https://vespa.ai/support/)
or contact your account manager.
