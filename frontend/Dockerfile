FROM node:24-alpine AS build

WORKDIR /app

RUN apk add --no-cache git python3 make g++

RUN npm install -g @quasar/cli@2.3.0

COPY . .

RUN npm install --silent --no-audit --no-fund

ARG VITE_GATEWAY_URL
ENV VITE_GATEWAY_URL=$VITE_GATEWAY_URL

ENV NODE_ENV=production
RUN quasar build

FROM nginx:1.29.1-alpine AS serve

COPY --from=build /app/dist/spa /usr/share/nginx/html

RUN echo 'server { \
    listen 80; \
    root /usr/share/nginx/html; \
    index index.html; \
    location / { \
        try_files $uri $uri/ /index.html; \
    } \
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ { \
        expires 1y; \
        add_header Cache-Control "public, immutable"; \
    } \
}' > /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]