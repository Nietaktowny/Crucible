# Frontend image: crucible_gui, a React SPA, built and served via nginx.
#
# Build (from crucible_gui/):
#   docker build --target serve -t crucible-frontend .
# Run:
#   docker run -p 8080:80 crucible-frontend
#
# See ../docker-compose.yml for running this together with the backend
# (the "backend" hostname in nginx.conf resolves via the compose network),
# and `docker compose run --rm frontend-tests` for the `test` stage below.

FROM node:22-slim AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

# `docker compose run --rm frontend-tests` targets this stage.
FROM deps AS test
COPY . .
CMD ["npm", "run", "test"]

FROM deps AS build
COPY . .
# Same-origin path proxied to the backend by nginx.conf; override at build
# time (--build-arg VITE_API_BASE_URL=...) for a different deployment
# topology (e.g. a separately hosted backend).
ARG VITE_API_BASE_URL=/api/v1
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
RUN npm run build

FROM nginx:1.27-alpine AS serve
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
