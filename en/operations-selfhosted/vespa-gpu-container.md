---
# Copyright Vespa.ai. All rights reserved.
title: "Container GPU setup"
category: oss
redirect_from:
- /en/vespa-gpu-container.html
---

Vespa supports using GPUs to evaluate ONNX models, as part of
its [stateless model evaluation
feature](/en/stateless-model-evaluation.html). When running Vespa inside a container engine such as Docker or
Podman, special configuration is required to make GPU(s) available inside the
container.

The following guide explains how to do this for Nvidia GPUs, using Podman on
RHEL8. This should also work on plain Rocky Linux 8.8 and AlmaLinux 8.8 on x86_64.
For other platforms and container engines, see
the [Nvidia
container toolkit installation guide](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html).
Commands below need to run as root (use `sudo bash` first).

## Run a script

Fetch and run our script for RHEL8 / x86_64 and run it as follows:

```
sudo dnf -y install wget
wget https://raw.githubusercontent.com/vespa-engine/docker-image/master/experimental/gpu-setup-rhel8-x86.sh
sh gpu-setup-rhel8-x86.sh
```

This will follow the steps below and check if a sample application is able to utilise the GPU.
For more details see the steps below.

## Configuration steps

1. Check that SELinux is disabled with `getenforce`; edit `/etc/selinux/config` and reboot if necessary.
   To temporarily avoid SELinux interfering, it's possible to run `setenforce Permissive` instead.
2. Ensure that Nvidia drivers are installed on your **host** where you want to run the `vespaengine/vespa`
   container image. On RHEL 8 this can be done as follows:

   ```
   dnf config-manager \
     --add-repo=https://developer.download.nvidia.com/compute/cuda/repos/rhel8/x86_64/cuda-rhel8.repo
   dnf module install -y --enablerepo cuda-rhel8-x86_64 nvidia-driver:530
   nvidia-modprobe
   ls -ld /dev/nvidia*
   ```

   You should have (at least) these devices listed after running the above commands:

   ```
   crw-rw-rw-. 1 root root 195,   0 Aug 16 11:24 /dev/nvidia0
   crw-rw-rw-. 1 root root 195, 255 Aug 16 11:24 /dev/nvidiactl
   crw-rw-rw-. 1 root root 238,   0 Aug 16 11:24 /dev/nvidia-uvm
   crw-rw-rw-. 1 root root 238,   1 Aug 16 11:24 /dev/nvidia-uvm-tools
   ```

   See [Device Node Verification](https://docs.nvidia.com/cuda/cuda-installation-guide-linux/index.html#device-node-verification) in the CUDA installation guide for more details.
3. Install `nvidia-container-toolkit`. This grants the container engine access
   to your GPU device(s). On RHEL 8 this can be done as follows:

   ```
   dnf config-manager \
     --add-repo=https://nvidia.github.io/libnvidia-container/rhel8.6/libnvidia-container.repo
   dnf install -y --enablerepo libnvidia-container nvidia-container-toolkit
   ```
4. Generate a "Container Device Interface" config:

   ```
   nvidia-ctk cdi generate --device-name-strategy=type-index --format=json --output /etc/cdi/nvidia.json
   ```
5. Verify that the GPU device is exposed to the container:

   ```
   podman run --rm -it --device nvidia.com/gpu=all docker.io/nvidia/cuda:11.6.2-base-ubuntu20.04 nvidia-smi
   ```

   This should print details about your GPU(s) if everything is configured correctly.
6. Start the Vespa container with the `--device` option:

   ```
   podman run --detach --name vespa --hostname vespa-container \
     --publish 8080:8080 --publish 19071:19071 \
     --device nvidia.com/gpu=all \
     vespaengine/vespa
   ```
7. The `vespaengine/vespa` image does not currently include the
   necessary CUDA libraries by default, due to their large size. These
   libraries must be installed inside the container manually:

   ```
   podman exec -u 0 -it vespa /bin/bash
   dnf -y install dnf-plugins-core
   dnf config-manager \
     --add-repo https://developer.download.nvidia.com/compute/cuda/repos/rhel8/x86_64/cuda-rhel8.repo
   dnf -y install vespa-onnxruntime-cuda
   ```

   Instead of the above installation of `vespa-onnxruntime-cuda` inside the running container,
   you might want to build your own container image using the following `Dockerfile` as
   it avoids having to run the container image with install privileges.

   ```
   FROM vespaengine/vespa

   USER root

   RUN dnf -y install 'dnf-command(config-manager)'
   RUN dnf config-manager --add-repo https://developer.download.nvidia.com/compute/cuda/repos/rhel8/x86_64/cuda-rhel8.repo
   RUN dnf -y install $(rpm -q --queryformat '%{NAME}-cuda-%{VERSION}' vespa-onnxruntime)

   USER vespa
   ```

   Then instead run with your container image name:

   ```
   podman run --detach --name vespa --hostname vespa-container \
     --publish 8080:8080 --publish 19071:19071 \
     --device nvidia.com/gpu=all \
     your-container-image-name
   ```
8. All Nvidia GPUs on the host should now be available inside the container,
   with devices exposed at `/dev/nvidiaN`.
   See [stateless
   model evaluation](/en/stateless-model-evaluation.html#onnx-inference-options) for how to configure the ONNX runtime to use a GPU for
   computation. Similar for embedding models using GPU, see
   [embedder onnx reference](/en/reference/embedding-reference.html#embedder-onnx-reference-config).
