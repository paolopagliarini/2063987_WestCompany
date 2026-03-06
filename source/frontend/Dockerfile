# Dockerfile
FROM node:20-alpine

# Si imposta la directory di lavoro del container.
WORKDIR /frontend

COPY package*.json ./
RUN npm install
COPY . .

CMD ["npm", "run", "dev"]