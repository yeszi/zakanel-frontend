FROM node:20-alpine AS build
WORKDIR /app
ARG VITE_API_BASE_URL
ARG VITE_CONTRACT_ADDRESS
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
ENV VITE_CONTRACT_ADDRESS=$VITE_CONTRACT_ADDRESS
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
# fallback SPA: semua rute (mis. /verifikasi/valid) diarahkan ke index.html
RUN printf 'server {\n  listen 80;\n  root /usr/share/nginx/html;\n  location / { try_files $uri $uri/ /index.html; }\n}\n' > /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
