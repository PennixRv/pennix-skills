# Cognee deployment overlay

Build this overlay from the `pennix-cognee-memory` directory after the official
Cognee `v1.6.2` backend image is available locally:

```bash
docker build \
  --build-arg BASE_IMAGE=pennix-cognee-backend:1.6.2-ba3631f \
  -f deployment/Dockerfile.overlay \
  -t pennix-cognee-backend:1.6.2-pennix \
  .
```

The overlay copies only the Pennix ASGI ingress. The official Cognee source,
package, entrypoint migrations, UI, storage engines, auth, and worker count
remain owned by the upstream image.
