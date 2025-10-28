---
# Copyright Vespa.ai. All rights reserved.
title: "Dockerを使ったVespaのクイック・スタート"
---

このガイドではDockerを使って1台のマシン上にVespaをインストールして起動する方法を説明します。
**必要条件**:
* [Docker](https://docs.docker.com/engine/install/)がインストールされていること。
* [Git](https://git-scm.com/downloads)がインストールされていること。
* オペレーティング・システム: macOSまたはLinux
* アーキテクチャ: x86_64
* 少なくとも2GBのメモリがコンテナのインスタンスに割り当てられていること。

1. **[GitHub](https://github.com/vespa-engine/sample-apps)からVespaのサンプル・アプリケーションをcloneする:**

   ```
   $ git clone https://github.com/vespa-engine/sample-apps.git
   $ export VESPA_SAMPLE_APPS=`pwd`/sample-apps
   ```
2. **VespaのDockerコンテナを起動する:**

   ```
   $ docker run --detach --name vespa --hostname vespa-container --privileged \
     --volume $VESPA_SAMPLE_APPS:/vespa-sample-apps --publish 8080:8080 vespaengine/vespa
   ```

   `volume`オプションで、事前にダウンロードしたソースコードにDockerコンテナ内の`/vespa-sample-apps`としてアクセスできるようになります。
   検索やフィード用のインタフェースにアクセスできるように、Dockerコンテナの外に`8080`ポートを公開します。
   `vespa`の名前で同時に稼働できるDockerコンテナは1つまでです。必要あらば変更してください。

   上記のコマンドの具体的なステップに興味がある場合は、[Dockerfile](https://github.com/vespa-engine/docker-image/blob/master/Dockerfile) と[起動スクリプト](https://github.com/vespa-engine/docker-image/blob/master/include/start-container.sh)を参照してください。
3. **設定サーバが起動するのを待つ - 200 OKのレスポンスを待つ:**

   ```
   $ docker exec vespa bash -c 'curl -s --head http://localhost:19071/ApplicationStatus'
   ```
4. **サンプル・アプリケーションをデプロイしてアクティベートする:**

   ```
   $ docker exec vespa bash -c 'vespa-deploy prepare /vespa-sample-apps/basic-search/src/main/application/ && \
     vespa-deploy activate'
   ```

   さらなるサンプル・アプリケーションは[sample-apps](https://github.com/vespa-engine/sample-apps/tree/master)で見つけることができます。
   [アプリケーション・パッケージ](../en/application-packages.html)のアプリケーションの項目を参照してください。
5. **アプリケーションがアクティブであることを確認する - 200 OKのレスポンスを待つ:**

   ```
   $ curl -s --head http://localhost:8080/ApplicationStatus
   ```
6. **ドキュメントをフィードする:**

   ```
   $ curl -s -H "Content-Type:application/json" --data-binary @${VESPA_SAMPLE_APPS}/basic-search/music-data-1.json \
       http://localhost:8080/document/v1/music/music/docid/1 | python -m json.tool
   $ curl -s -H "Content-Type:application/json" --data-binary @${VESPA_SAMPLE_APPS}/basic-search/music-data-2.json \
       http://localhost:8080/document/v1/music/music/docid/2 | python -m json.tool
   ```

   この例では[ドキュメントAPI](../en/reference/document-v1-api-reference.html)を使っています。
   大規模なデータを高速にフィードするには[Java Feeding API](../en/vespa-feed-client.html)を使ってください。
7. **クエリーとドキュメント取得リクエストを実行する:**

   ```
   $ curl -s http://localhost:8080/search/?query=bad | python -m json.tool
   ```
```
   $ curl -s http://localhost:8080/document/v1/music/music/docid/2 | python -m json.tool
   ```

   ブラウザで[localhost:8080/search/?query=bad](http://localhost:8080/search/?query=bad)の結果を参照してください。
   詳しくは[Query API](../en/query-api.html)を参照してください。
8. **終わったらクリーンアップする**

   必要なくなった稼働中のコンテナを停止する:

   ```
   $ docker stop vespa
   ```

   必要に応じて、停止したコンテナを完全に削除する:

   ```
   $ docker rm vespa
   ```

## 次のステップ
* このアプリケーションは完全に機能してプロダクションで使うことができますが、冗長性のために
  [ノードを追加](../en/operations-selfhosted/multinode-systems.html )した方がいいかもしれません。* Vespaアプリケーションにあなた独自のJavaコンポーネントを追加するには、
    [アプリケーションの開発](../en/developer-guide.html)
    を参照してください。* [Vespa API](../en/api.html)はVespaのインタフェースの理解に役立つでしょう。* [サンプル・アプリケーション](https://github.com/vespa-engine/sample-apps/tree/master)を眺めてみましょう。* [Vespaのインストールをセキュア](../en/operations-selfhosted/securing-your-vespa-installation.html)にします。* AWSで稼働させるには、[AWS EC2での複数ノードのクイック・スタート](../en/operations-selfhosted/multinode-systems.html#aws-ec2)または
            [AWS ECSでの複数ノードのクイック・スタート](../en/operations-selfhosted/multinode-systems.html#aws-ecs)を参照してください。
