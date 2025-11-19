# Verify your identity with Your Vespa Cloud Private Key

Sometimes Vespa Cloud support may need to verify your identity before helping you with sensitive operations, for example when resetting your password or making changes to your account.

This guide explains **the signing step** a user must do after receiving a text file from Vespa Cloud support.

Support will later verify your signature using your **Vespa Cloud certificate**.
You will **sign using the matching private key** on your machine.

---

## 1. Prerequisites

You need:

1. A shell on your machine (Linux, macOS, WSL, Git Bash, etc.).
2. OpenSSL installed, you can test with: `openssl version`
3. Your Vespa Cloud data plane private key file, typically something like:

    `~/.vespa/<tenant>.<app>.<instance>/data-plane-private-key.pem`

    Example:

    `~/.vespa/my-tenant.my-app.my-instance/data-plane-private-key.pem`

{% include warning.html content="<p>Never send this private key file to anyone.<br/>
Vespa Support will <b>never ask for your private key</b>. You <b>only send the signed challenge file</b>.</p>" %}



## 2. Save the challenge file from support

Support will send you a text file (for example `challenge.txt`).

1. Save it locally as e.g.: `~/Downloads/vespa-challenge.txt`

2. Check its content (optional but recommended):

```bash
cat ~/Downloads/vespa-challenge.txt
```

## 3. Sign the file with your Vespa private key

In a terminal:

1. Go to the folder where you want the signature to be created:

```bash
cd ~/Downloads
```

2. Run openssl to create a detached signature:

```bash
openssl dgst -sha256 \
  -sign ~/.vespa/my-tenant.my-app.my-instance/data-plane-private-key.pem \
  -out vespa-challenge.sig \
  vespa-challenge.txt
```

Replace the path to the private key and filenames if yours differ.

This command:
- Computes a SHA-256 hash of `vespa-challenge.txt`.
- Signs that hash with your Vespa private key.
- Writes the binary signature to `vespa-challenge.sig`.

## 4. Base64-encode the signature

Convert the binary signature to base64 format (required for reliable transmission via email/chat):

```bash
openssl base64 -in vespa-challenge.sig -A > vespa-challenge.sig.b64
```

This converts the binary signature to text format, making it safe to copy-paste in support tickets without corruption.

You now have:
- `vespa-challenge.txt` – the original file from support
- `vespa-challenge.sig` – binary signature
- `vespa-challenge.sig.b64` – base64-encoded signature (text) ← **send this one**

## 5. What to send back to support

Send both files:
- The original challenge file: `vespa-challenge.txt`
- The base64-encoded signature: `vespa-challenge.sig.b64`

Support will then verify the signature using your Vespa Cloud certificate on their side.
