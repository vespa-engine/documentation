# Vespa documentation

> Vespa is a powerful and scalable engine for low-latency computation over large data sets. It is designed for real-time applications that require a combination of search, recommendation, and personalization. Vespa allows developers to build applications that can handle high volumes of queries and data writes while maintaining fast response times.

**Key Features**

Vespa offers a rich set of features for building sophisticated search and recommendation applications:

* **Real-time Indexing and Search:** Vespa provides low-latency CRUD (Create, Read, Update, Delete) operations, making data searchable in milliseconds after being fed.
* **Approximate Nearest Neighbor (ANN) Search:** Vespa includes a highly efficient implementation of the HNSW algorithm for fast and accurate vector search, which can be combined with traditional filters.
* **Flexible Ranking and Relevance:** Ranking is a first-class citizen in Vespa. It supports complex, multi-phase ranking expressions and can integrate with machine-learned models (e.g., ONNX, TensorFlow, XGBoost, LightGBM) to deliver highly relevant results.
* **Scalability and Elasticity:** Vespa is designed to scale horizontally. Content clusters can be grown or shrunk on the fly without service interruptions, and data is automatically redistributed to maintain a balanced load.
* **Rich Data Modeling:** Vespa supports a variety of data types, including structured data, unstructured text, and tensors for vector embeddings. It also supports parent-child relationships to model complex data hierarchies.
* **Comprehensive Query Language:** Vespa's query language (YQL) allows for a combination of keyword search, structured filtering, and nearest neighbor search in a single query.
* **Component-Based Architecture:** Vespa's container clusters host custom Java components (Searchers, Document Processors) that allow for extensive customization of query and data processing pipelines.

**Architecture**

A Vespa application consists of two main types of clusters:

* **Stateless Container Clusters:** These clusters handle incoming queries and data writes. They host application components that process requests and responses, perform query rewriting, and federate to backend services.
* **Stateful Content Clusters:** These clusters are responsible for storing, indexing, and searching data. They automatically manage data distribution and redundancy.

Vespa's architecture is designed for high availability and fault tolerance. When a node fails, the system automatically re-routes traffic and re-distributes data to maintain service.

**Application Package**

A Vespa application is defined by an **application package**, which contains all the necessary configuration, schemas, components, and machine-learned models. This self-contained package allows for atomic deployments and ensures consistency between code and configuration.

Key files in an application package include:

* **`services.xml`**: Defines the services and clusters that make up the application, including their topology and resource allocation.
* **`schemas/*.sd`**: Defines the document types, their fields, and how they should be indexed and searched. Rank profiles are also defined within schemas.

**APIs and Interfaces**

Vespa provides a comprehensive set of APIs for interacting with the system:

* **Document API (`/document/v1/`)**: A REST API for performing CRUD operations on documents.
* **Query API (`/search/`)**: A powerful API for querying data using YQL, with extensive options for ranking, grouping, and presentation.
* **Configuration and Deployment APIs**: REST APIs for deploying application packages and managing system configuration.

This overview provides a glimpse into the capabilities of the Vespa Search engine. For more in-depth information, please refer to each of the documentation links below.