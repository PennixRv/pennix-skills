# Query and citation

Confirm native schemas and default notebook before access. Exact names, known
IDs, deployment keys, and error fragments suit full-text search or scoped
read-only SQL. Conceptual questions and paraphrased experience suit native
semantic search, with native rerank when configured. Begin with a small page
(usually 10), then expand only to answer a known gap. Put the notebook filter
in the native query; fetching globally and filtering locally already reads
outside the default scope. If a semantic tool lacks a notebook filter, use it
only after the owner has verified that its index is limited to the selected
notebook; otherwise use scoped full-text search and report the semantic limit.

Retrieve the original blocks/document and useful references/outline after a
hit. Cite the SiYuan block URI or native reference plus source date/version,
and distinguish historical rationale from current verified behavior. A search
snippet or model summary alone cannot establish current configuration.

Semantic indexing sends eligible note content to the embedding provider;
rerank sends the query and candidate text to its provider. The NAS kernel's
index scope is independent of the reader's notebook convention and of S3 sync.
Index rules and vector maintenance belong to the deployment owner. A configured
dimension or successful provider test does not prove semantic ranking quality.

Report no match as no match. Report authentication, index, provider, and tool
failure as the actual failed layer; do not silently broaden scope, change
models, reconfigure providers, or scan raw history to hide it.
