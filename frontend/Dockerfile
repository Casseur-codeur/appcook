FROM node:20-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.http.conf.template /etc/nginx/templates/nginx.http.conf.template
COPY nginx.https.conf.template /etc/nginx/templates/nginx.https.conf.template
COPY docker-entrypoint.d/40-configure-https.sh /docker-entrypoint.d/40-configure-https.sh
RUN chmod +x /docker-entrypoint.d/40-configure-https.sh

EXPOSE 80
EXPOSE 443
CMD ["nginx", "-g", "daemon off;"]
