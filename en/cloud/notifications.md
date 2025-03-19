---
# Copyright Vespa.ai. All rights reserved.
title: Notifications
---

Vespa Cloud supports two different categories of notifications. Notifications can be sent
by email if this has been configured in the Console.

 * **Tenant notifications** are administrative notifications about the tenant.  Information
   about users, plan, etc. are sent to all contacts configured to get tenant notifications.

 * **Application notifications** are notifications about your running Vespa applications.
   If there are resource constraint issues, deployment errors, configuration errors or other
   issues with a Vespa application, they will be sent to all contacts configured to get
   application notifications.

## Configuring Notifications
Notifications are configured in the Console under **Account > Notifications**.  You can add
contacts here that will start receiving emails for the categories enabled for that contact.

<!--
![Console Notifications](/assets/console-notifications.png)
-->
<img src="/assets/img/console-notifications.png" alt="Console Notifications"
  width="932px" height="auto">

To add a new address to get notifications:
1. Click **+Add new contact**.
2. Enter the email address to receive notifications to.
3. Choose the types of notifications to receive.
4. Click **Save**
5. Go to your email inbox and click the verification link you have received there.
